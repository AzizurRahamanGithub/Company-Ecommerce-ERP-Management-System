from rest_framework.exceptions import ValidationError

from rest_framework.views import APIView
from rest_framework.response import Response
from .repositories import OrderRepository
from .payment_service import StripePaymentService
from .serializers import (
    OrderSerializer,
    OrderListSerializer,
    DeliveryNoteSerializer,
    AllInvoiceSerializer,
    ReviewSerializer,
    Review,
)
from apps.delivery_manage.models import ProductLoad, LoadItem
from .repositories import PaymentRepository
import stripe
from django.conf import settings
from apps.core.getDetails import BaseRetrieveAPIView
from apps.core.getList import BaseListAPIView
from .models import Order
from apps.cart.repositories import CartRepository
import logging
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework import filters
from .models import DeliveryNote, Invoice
from django.db.models import Sum, Avg
import django_filters
from datetime import datetime, timedelta
from django.utils import timezone
from rest_framework import generics
from collections import defaultdict
from django.http import JsonResponse
from apps.core.response import success_response, failure_response
from apps.core.pagination import CustomPagination
from decimal import Decimal, InvalidOperation

stripe.api_key = settings.STRIPE_SECRET_KEY
logger = logging.getLogger(__name__)

class StripePaymentAndOrderView(APIView):
    def post(self, request):
        logger.debug(f"Received data: {request.data}")

        selected_items = request.data.get("selected_items", [])
        total_amount = request.data.get("total_amount", 0)
        payment_method_id = request.data.get("payment_method_id", None)
        delivery_date = request.data.get("delivery_date", None)
        delivery_address = request.data.get("delivery_address", None)
        delivery_area = request.data.get("delivery_area", None)

        # Validation
        if not payment_method_id:
            return failure_response( "Payment method ID is missing")
        if not selected_items:
            return failure_response( "No items selected")
        if not total_amount or total_amount <= 0:
            return failure_response( "Invalid total amount")

        # Step 1: Stripe payment
        try:
            payment_intent = StripePaymentService.create_payment(
                total_amount, payment_method_id, request.user
            )
            logger.debug(f"Payment Intent created: {payment_intent.id}")
        except Exception as e:
            logger.error(f"Stripe payment failed: {str(e)}", exc_info=True)
            return failure_response(f"Payment failed: {str(e)}")

        # Step 2: Log payment
        try:
            payment = PaymentRepository.create_payment(
                None,
                "stripe",
                total_amount,
                transaction_id=payment_intent.id,
                status="completed",
            )
        except Exception as e:
            logger.error(f"Payment logging failed: {str(e)}", exc_info=True)
            return failure_response("Payment succeeded but failed o log it")

        # Step 3: Create order
        try:
            order = OrderRepository.create_order_snapshot(
                request.user,
                selected_items,
                total_amount,
                delivery_date,
                delivery_address,
                delivery_area,
            )
        except Exception as e:
            logger.error(f"Order creation failed: {str(e)}", exc_info=True)
            return failure_response(f"Order creation failed: {str()}")

        # Step 4: Link payment to order
        payment.order = order
        payment.save()

        # Step 5: Update order status
        OrderRepository.update_order_status(order, "pending")

        # Step 6: Clear cart
        try:
            cart = CartRepository.get_cart(request.user)
            for item in selected_items:
                product = item.get("product")
                CartRepository.remove_item(cart, product)
        except Exception as e:
            logger.warning(f"Cart cleanup failed (non-critical): {str(e)}", exc_info=True)
            # Don't fail the whole request — payment + order already succeeded

        # Step 7: Create invoice
        try:
            Invoice.objects.create(order=order, payment_status="paid")
        except Exception as e:
            logger.warning(f"Invoice creation failed (non-critical): {str(e)}", exc_info=True)

        return success_response( "Payment successful and order created successfully",
                                
               { "order_id": order.id,
                "payment_id": payment.id,
               }
        )


class OfflinePayment(APIView):
    def post(self, request):
        try:
            # Log the input data to check what was received
            logger.debug(f"Received data: {request.data}")

            # Receive selected items, total amount, and payment method ID
            selected_items = request.data.get("selected_items", [])
            total_amount = request.data.get("total_amount", 0)
            delivery_date = request.data.get("delivery_date", None)
            delivery_address = request.data.get("delivery_address", None)
            delivery_area = request.data.get("delivery_area", None)
            payment_method = request.data.get("payment_method", None)

            if not selected_items:
                return success_response( "No items selected")

            if total_amount <= 0:
                return success_response( "Invalid total amount")

            # Step 1: Process Payment with Stripe
            # payment_intent = StripePaymentService.create_payment(
            #     total_amount, payment_method_id, request.user
            # )

            # Log payment intent for debugging
            # logger.debug(f"Payment Intent created: {payment_intent}")

            # Step 2: Log the payment in the payment history
            payment = PaymentRepository.create_payment(
                None,
                payment_method,
                total_amount,
                transaction_id=f"{payment_method}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                status="pending",
            )

            # Step 3: Create the order after the payment is successful
            order = OrderRepository.create_order_snapshot(
                request.user,
                selected_items,
                total_amount,
                delivery_date,
                delivery_address,
                delivery_area,
                payment_method,
            )

            # Step 4: Link the payment to the created order
            payment.order = order
            payment.save()

            # Step 5: Update the order status to 'pending'
            OrderRepository.update_order_status(order, "pending")

            # Step 6: Remove the selected items from the cart after the successful payment
            cart = CartRepository.get_cart(request.user)
            for item in selected_items:
                product = item.get("product")
                CartRepository.remove_item(cart, product)

            # invoice creatre for order
            invoice = Invoice.objects.create(
                order=order,
                payment_status="paid",
            )

            return success_response( "Payment successful and order created successfully",
                    {"order_id": order.id,
                    "payment_id": payment.id
                    }
            )

        except Exception as e:
            # Log the exception for debugging
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return failure_response("An unexpected error occurred")


class OrderList(BaseListAPIView):
    queryset = Order.objects.all().order_by("-id")
    serializer_class = OrderListSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["delivery_date", "delivery_area", "order_status"]
    search_fields = ["order_number", "delivery_area", "user__username"]
    ordering_fields = ["id", "delivery_date", "total_amount"]


class OrderProductSummaryAPIView(APIView):
    # permission_classes = [IsAuthenticated]

    def get(self, request):
        date_str = request.GET.get("delivery_date")
        area = (request.GET.get("delivery_area") or "").strip()

        if not date_str:
            return JsonResponse(
                {"success": False, "message": "delivery_date is required (YYYY-MM-DD)"},
                status=400,
            )

        try:
            delivery_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return JsonResponse(
                {"success": False, "message": "Invalid delivery_date. Use YYYY-MM-DD."},
                status=400,
            )

        qs = Order.objects.filter(delivery_date=delivery_date)

        if area:
            qs = qs.filter(delivery_area__icontains=area)

        qs = qs.only("order_items", "id")

        existing_loads = ProductLoad.objects.filter(
            selected_delivery_date=delivery_date
        )

        if area:
            existing_loads = existing_loads.filter(delivery_area__icontains=area)

        already_loaded_product_ids = set()

        if existing_loads.exists():
            load_items = LoadItem.objects.filter(
                load__in=existing_loads
            ).select_related("product")

            already_loaded_product_ids = {item.product_id for item in load_items}

        # key = (product_id, product_name, price)
        def _bucket():
            return {
                "product_id": None,
                "product_name": "Unknown",
                "product_image": None,
                "price": None,
                "total_quantity": Decimal("0"),
            }

        totals = defaultdict(_bucket)

        orders_count = 0
        line_items_count = 0

        for order in qs.iterator():
            orders_count += 1

            items = order.order_items or []

            if not isinstance(items, list):
                continue

            for item in items:

                if not isinstance(item, dict):
                    continue

                line_items_count += 1

                pid = item.get("product_id")
                pname = item.get("product_name") or "Unknown"

                # Skip already loaded products
                if pid in already_loaded_product_ids:
                    continue

                # quantity
                raw_qty = item.get("quantity")

                if raw_qty is None:
                    raw_qty = item.get("qty")

                if raw_qty is None:
                    raw_qty = item.get("amount")

                try:
                    qty_val = Decimal(str(raw_qty if raw_qty is not None else "0"))
                except (InvalidOperation, TypeError, ValueError):
                    qty_val = Decimal("0")

                # price
                price = (
                    item.get("price")
                    or item.get("product_price")
                    or item.get("unit_price")
                    or None
                )

                # image
                image = (
                    item.get("product_image")
                    or item.get("image")
                    or item.get("image_url")
                    or None
                )

                key = (pid, pname, price)

                bucket = totals[key]

                if bucket["product_id"] is None:
                    bucket["product_id"] = pid

                if bucket["product_name"] == "Unknown" and pname:
                    bucket["product_name"] = pname

                if bucket["price"] is None and price:
                    bucket["price"] = price

                if bucket["product_image"] is None and image:
                    bucket["product_image"] = image

                bucket["total_quantity"] += qty_val

        items_out = []

        for (_pid, _pname, _price), b in totals.items():
            items_out.append(
                {
                    "product_id": b["product_id"],
                    "product_name": b["product_name"],
                    "product_image": b["product_image"],
                    "price": b["price"],
                    "total_quantity": float(b["total_quantity"]),
                }
            )

        items_out.sort(key=lambda x: (x["product_name"] or "", x["price"] or 0))

        grand_total_qty = float(
            sum(Decimal(str(i["total_quantity"])) for i in items_out)
        )

        return JsonResponse(
            {
                "success": True,
                "data": {
                    "filters": {
                        "delivery_date": str(delivery_date),
                        "delivery_area_contains": area or None,
                    },
                    "orders_count": orders_count,
                    "line_items_count": line_items_count,
                    "distinct_products": len(items_out),
                    "grand_total_qty": grand_total_qty,
                    "items": items_out,
                    "already_loaded_count": len(already_loaded_product_ids),
                },
            },
            status=200,
        )



class RetrieveOrder(BaseRetrieveAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer


class OrderUpdateView(APIView):
    def put(self, request, pk):
        # Get the order instance to update
        order = Order.objects.get(pk=pk)

        # Extract the fields directly from the request data
        order_status = request.data.get("order_status", order.order_status)
        delivery_date = request.data.get("delivery_date", order.delivery_date)
        delivery_area = request.data.get("delivery_area", order.delivery_area)
        delivery_info = request.data.get("delivery_info", order.delivery_info)
        return_info = request.data.get("return_info", order.return_info)
        signature = request.data.get("signature", order.signature)

        # Manually update the order instance with the provided fields
        order.order_status = order_status
        order.delivery_date = delivery_date
        order.delivery_area = delivery_area
        order.delivery_info = delivery_info
        order.return_info = return_info
        order.signature = signature

        # Save the order instance
        order.save()

        # Handle the creation or update of the DeliveryNote
        delivery_note_data = {
            "delivery_area": order.delivery_area,
            "delivery_info": order.delivery_info,
            "return_info": order.return_info,
            "signature": order.signature,
        }

        # Create or update DeliveryNote for the order
        delivery_note_instance, created = DeliveryNote.objects.update_or_create(
            order=order,
            defaults={"delivery_details": delivery_note_data},
        )

        # Check if an Invoice already exists for the order before creating a new one
        if not Invoice.objects.filter(order=order).exists():
            Invoice.objects.create(
                order=order,
                invoice_type="delivery_note",
            )

        # Return the updated order data
        return Response(
            {
                "success": True,
                "message": "Order updated successfully",
                "data": {
                    "order_status": order.order_status,
                    "delivery_date": order.delivery_date,
                    "delivery_area": order.delivery_area,
                    "delivery_info": order.delivery_info,
                    "return_info": order.return_info,
                    "signature": order.signature,
                    "delivery_note": delivery_note_instance.id,
                },
            },
            status=status.HTTP_200_OK,
        )


class InvoiceFilter(django_filters.FilterSet):
    this_week = django_filters.BooleanFilter(
        method="filter_this_week", label="This Week"
    )
    previous_week = django_filters.BooleanFilter(
        method="filter_previous_week", label="Previous Week"
    )
    order_number = django_filters.CharFilter(
        field_name="order__order_number", lookup_expr="icontains"
    )  # Use `__` to filter by related field

    class Meta:
        model = Invoice
        fields = ["invoice_number", "invoice_type", "payment_status", "order_number"]

    def filter_this_week(self, queryset, name, value):
        if value:
            today = timezone.localdate()  # Get today's date in local time zone
            start_of_week = today - timedelta(
                days=today.weekday()
            )  # Monday of the current week
            end_of_week = start_of_week + timedelta(
                days=6
            )  # Sunday of the current week
            return queryset.filter(
                invoice_date__gte=start_of_week, invoice_date__lte=end_of_week
            )
        return queryset

    def filter_previous_week(self, queryset, name, value):
        if value:
            today = timezone.localdate()  # Get today's date in local time zone
            start_of_current_week = today - timedelta(
                days=today.weekday()
            )  # Monday of the current week
            start_of_previous_week = start_of_current_week - timedelta(
                weeks=1
            )  # Monday of the previous week
            end_of_previous_week = start_of_previous_week + timedelta(
                days=6
            )  # Sunday of the previous week
            return queryset.filter(
                invoice_date__gte=start_of_previous_week,
                invoice_date__lte=end_of_previous_week,
            )
        return queryset


class AllInvoice(BaseListAPIView):
    queryset = Invoice.objects.all()
    serializer_class = AllInvoiceSerializer
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_class = InvoiceFilter
    ordering_fields = ["invoice_number", "invoice_date", "created_at"]
    ordering = ["-created_at"]


class InvoiceRetrieveView(BaseRetrieveAPIView):
    queryset = Invoice.objects.all()
    serializer_class = AllInvoiceSerializer


class DeliveryNoteList(BaseListAPIView):
    queryset = DeliveryNote.objects.all().order_by("-id")
    serializer_class = DeliveryNoteSerializer


class DeliveryNoteRetrieveView(BaseRetrieveAPIView):
    queryset = DeliveryNote.objects.all()
    serializer_class = DeliveryNoteSerializer


class OrderGraphDataView(APIView):
    def get(self, request):
        """
        Get the aggregated data for each day of the current week (Monday to Sunday),
        showing order counts, delivery counts, and total amounts for each day.
        """
        # Get the start and end of the current week (Monday to Sunday)
        today = timezone.localdate()
        start_of_week = today - timedelta(
            days=today.weekday()
        )  # Start of the current week (Monday)
        days_of_week = [
            start_of_week + timedelta(days=i) for i in range(7)
        ]  # List of days in this week

        # Initialize the result list
        result = []

        # Loop through each day and get the aggregated data for orders, deliveries, and total amounts
        for day in days_of_week:
            # Get the total orders for this day
            orders_today = Order.objects.filter(ordered_date__date=day)
            total_orders = orders_today.count()
            total_amount = (
                orders_today.aggregate(Sum("total_amount"))["total_amount__sum"] or 0
            )

            # Get the total deliveries for this day
            deliveries_today = DeliveryNote.objects.filter(created_at__date=day)
            total_deliveries = deliveries_today.count()

            # Add the result for the current day to the list
            result.append(
                {
                    "day": day.strftime("%a"),  # Day name (Mon, Tue, etc.)
                    "orders": total_orders,
                    "deliveries": total_deliveries,
                    "total_amount": total_amount,  # Total amount for the orders on this day
                }
            )

        return Response(
            {"success": True, "message": "Data retrieved successfully", "data": result},
            status=status.HTTP_200_OK,
        )


class ReviewListCreateAPIView(generics.ListCreateAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    # permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        request_time = timezone.now()
        user = self.request.user

        # Get order_number from request data
        order_number = self.request.data.get("order_number")
        if not order_number:
            raise ValidationError({"order_number": "This field is required."})

        # Validate order existence
        try:
            order = Order.objects.get(order_number=order_number)
        except Order.DoesNotExist:
            raise ValidationError({"order_number": "Order not found."})

        # Check if the user already reviewed this order
        if Review.objects.filter(user=user, order_id=order).exists():
            raise ValidationError({"detail": "You have already reviewed this order."})

        # Save the review linked to the correct order and user
        serializer.save(created_at=request_time, user=user, order_id=order)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return Response(
            {
                "success": True,
                "message": "Review created successfully",
                "data": response.data,
            },
            status=response.status_code,
        )

    def get(self, request, *args, **kwargs):
        reviews = self.get_queryset()
        serializer = ReviewSerializer(reviews, many=True)
        meta = {
            "total_reviews": reviews.count(),
            "average_rating": reviews.aggregate(Avg("rating"))["rating__avg"],
        }
        return Response(
            {
                "success": True,
                "message": "Reviews fetched successfully",
                "meta": meta,
                "data": serializer.data,
            }
        )


class ReviewAPIView(APIView):
    def get(self, request, order_number):
        # Get the order object by order_number
        try:
            order = Order.objects.get(order_number=order_number)
        except Order.DoesNotExist:
            return Response(
                {"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Fetch all reviews related to the order
        reviews = Review.objects.filter(order_id=order)

        # Serialize the reviews data
        serializer = ReviewSerializer(reviews, many=True)

        # Return the reviews in response
        return Response(
            {
                "success": True,
                "message": "Reviews fetched successfully",
                "status_code": status.HTTP_200_OK,
                "data": serializer.data,
            }
        )


class CompletedOrderListAPIView(generics.ListAPIView):
    serializer_class = OrderSerializer

    def get_queryset(self):
        # Only return orders that are completed for the logged-in user
        return Order.objects.filter(user=self.request.user, order_status="completed")

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(
            {
                "success": True,
                "message": "Completed orders fetched successfully",
                "total_completed_orders": queryset.count(),
                "data": serializer.data,
            }
        )
