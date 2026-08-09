from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, Q, Sum,F,Max
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.order.models import Order  , OrderItem
from datetime import datetime
from django.db.models.functions import Coalesce


class OrderOverviewGraphDataView(APIView):
    def get(self, request):
        """
        Get day-wise order counts by status (pending, delivered, completed, cancelled)
        for the current week (Monday to Sunday).
        """
        today = timezone.localdate()
        start_of_week = today - timedelta(days=today.weekday())  # Monday
        days_of_week = [start_of_week + timedelta(days=i) for i in range(7)]

        result = []

        for day in days_of_week:
            # Filter all orders of this particular day
            orders_today = Order.objects.filter(ordered_date__date=day)

            # Count by status
            status_counts = orders_today.values("order_status").annotate(count=Count("id"))
            counts = {
                "pending": 0,
                "delivered": 0,
                "completed": 0,
                "cancelled": 0,
            }

            # Fill the counts dynamically
            for sc in status_counts:
                counts[sc["order_status"]] = sc["count"]

            # Total orders and total amount for the day
            total_orders = orders_today.count()
            total_amount = orders_today.aggregate(Sum("total_amount"))["total_amount__sum"] or 0

            result.append(
                {
                    "day": day.strftime("%a"),  # Mon, Tue, ...
                    "orders": total_orders,
                    "total_amount": total_amount,
                    "pending": counts["pending"],
                    "delivered": counts["delivered"],
                    "completed": counts["completed"],
                    "cancelled": counts["cancelled"],
                }
            )

        return Response(
            {"success": True, "message": "Data retrieved successfully", "data": result},
            status=status.HTTP_200_OK,
        )


class SalesByProductAPIView(APIView):
    """
    Returns total sales (amount) grouped by product.
    """

    def get(self, request):
        # Aggregate total sales by product
        sales_data = (
            OrderItem.objects.values(product_name=F("product__name"))
            .annotate(total_sales=Sum(F("price") * F("quantity")))
            .order_by("-total_sales")
        )

        # Format the response
        data = [
            {
                "product": item["product_name"],
                "total_sales": float(item["total_sales"] or 0),
            }
            for item in sales_data
        ]

        return Response(
            {
                "success": True,
                "message": "Sales by product retrieved successfully",
                "data": data,
            },
            status=status.HTTP_200_OK,
        )


class SalesByCustomersView(APIView):
    """
    GET /api/analytics/sales-by-customers/
      ?start=YYYY-MM-DD     (optional)
      ?end=YYYY-MM-DD       (optional)
      ?statuses=completed,delivered  (optional; defaults to completed+delivered)
      ?limit=6              (optional; default 6)

    Response:
    {
      "success": true,
      "data": {
        "labels": ["Customer 01","Customer 02", ...],
        "values": [120.0, 75.0, ...],
        "table": [
          {"customer_id": 5, "customer_name": "Acme Ltd", "orders": 12, "total_amount": 1234.56},
          ...
        ]
      }
    }
    """
    DEFAULT_STATUSES = ["completed", "delivered"]

    def get(self, request):
        # Parse inputs
        start_s = request.query_params.get("start")
        end_s = request.query_params.get("end")
        limit = int(request.query_params.get("limit", 6))
        statuses = request.query_params.get("statuses")
        statuses = (
            [s.strip() for s in statuses.split(",") if s.strip()]
            if statuses else self.DEFAULT_STATUSES
        )

        # Build filters
        filters = {"order_status__in": statuses}
        if start_s:
            try:
                start = datetime.fromisoformat(start_s).date()
                filters["ordered_date__date__gte"] = start
            except ValueError:
                return Response({"detail": "Invalid 'start' date. Use YYYY-MM-DD."},
                                status=status.HTTP_400_BAD_REQUEST)
        if end_s:
            try:
                end = datetime.fromisoformat(end_s).date()
                filters["ordered_date__date__lte"] = end
            except ValueError:
                return Response({"detail": "Invalid 'end' date. Use YYYY-MM-DD."},
                                status=status.HTTP_400_BAD_REQUEST)

        # Aggregate: group by user; prefer Customer.business_name, fallback to username
        qs = (
            Order.objects
            .filter(**filters)
            .values("user_id")
            .annotate(
                customer_name=Coalesce(
                    Max("user__customer_account__business_name"),
                    Max("user__username"),
                ),
                orders=Count("id"),
                total_amount=Sum("total_amount"),
            )
            .order_by("-total_amount")[:limit]
        )

        rows = list(qs)
        labels = [r["customer_name"] or f"Customer {r['user_id']}" for r in rows]
        values = [float(r["total_amount"] or 0) for r in rows]

        # Optional: pad to exactly N bars to match your UI layout
        # while len(labels) < limit:
        #     labels.append("")
        #     values.append(0.0)

        return Response(
            {
                "success": True,
                "message": "Sales by customers aggregated successfully",
                "data": {
                    "labels": labels,
                    "values": values,
                    "table": [
                        {
                            "customer_id": r["user_id"],
                            "customer_name": r["customer_name"],
                            "orders": r["orders"],
                            "total_amount": float(r["total_amount"] or 0),
                        }
                        for r in rows
                    ],
                },
            },
            status=status.HTTP_200_OK,
        )
        
        
class TotalSellAndTotalDelivery(APIView):
    def get(self, request):
        total_sell = Order.objects.filter(order_status="completed").aggregate(total_sell=Sum('total_amount'))['total_sell']
        total_delivery = Order.objects.filter(order_status="delivered").aggregate(total_delivery=Sum('total_amount'))['total_delivery']
        return Response({
           "success": True,
           "data": {
               "total_sell": total_sell,
               "total_delivery": total_delivery
           }
        }, status=status.HTTP_200_OK)