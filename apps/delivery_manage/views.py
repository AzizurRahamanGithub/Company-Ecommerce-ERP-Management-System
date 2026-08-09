from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import (
    ProductLoadSerializer,
    ProductLoad,
)
from rest_framework.permissions import IsAuthenticated
from collections import defaultdict
from apps.order.models import Order
from .models import LoadItem
from apps.core.pagination import CustomPagination

class AllProductLoadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        filter_date = request.query_params.get("date", None)

        # Filter by date or fetch all
        if filter_date:
            product_loads = ProductLoad.objects.filter(selected_delivery_date=filter_date)
        else:
            product_loads = ProductLoad.objects.all().order_by("-selected_delivery_date")

        if not product_loads.exists():
            return Response(
                {"success": True, "message": "No product loads found for this date.", "data": []},
                status=status.HTTP_200_OK,
            )

        # === Pagination setup ===
        paginator = CustomPagination()
        paginated_loads = paginator.paginate_queryset(product_loads, request)

        all_loads_data = []
        for product_load in paginated_loads:
            matching_orders = Order.objects.filter(
                delivery_area=product_load.delivery_area,
                delivery_date=product_load.selected_delivery_date,
            )

            # === Loaded products ===
            load_items = LoadItem.objects.filter(load=product_load)
            loaded_product_summary = defaultdict(int)
            loaded_product_details = {}

            for item in load_items:
                loaded_product_summary[item.product.name] += item.quantity
                # Adding unit_type and box information
                loaded_product_details[item.product.name] = {
                    "box": item.box,
                }

            loaded_product_list_and_quantity = [
                {
                    "product_name": name,
                    "total_quantity": qty,
                    "box": loaded_product_details[name]["box"]
                }
                for name, qty in loaded_product_summary.items()
            ]

            # === Needed products ===
            order_product_summary = defaultdict(int)
            needed_product_details = {}

            for order in matching_orders:
                for order_item in order.items.all():
                    if order_item.product:
                        order_product_summary[order_item.product.name] += order_item.quantity
                        # Fetch unit_type and box from LoadItem model
                        # Find corresponding LoadItem for the product in the matching load
                        corresponding_load_item = LoadItem.objects.filter(
                            product=order_item.product,
                            load__in=product_loads
                        ).first()

                        if corresponding_load_item:
                            needed_product_details[order_item.product.name] = {
                                "box": corresponding_load_item.box,
                            }
                        else:
                            needed_product_details[order_item.product.name] = {
                                "box": "N/A",        # Default if not found
                            }

            need_product_list_and_quantity = [
                {
                    "product_name": name,
                    "total_quantity_needed": qty,
                    "box": needed_product_details[name]["box"]
                }
                for name, qty in order_product_summary.items()
            ]

            # === Combined data ===
            load_data = {
                "id": product_load.id,
                "delivery_area": product_load.delivery_area,
                "selected_delivery_date": product_load.selected_delivery_date,
                "notes": product_load.notes,
                "assigned_driver": {
                    "id": product_load.assigned_driver.id if product_load.assigned_driver else None,
                    "full_name": product_load.assigned_driver.full_name if product_load.assigned_driver else None,
                    "email": product_load.assigned_driver.email if product_load.assigned_driver else None,
                    "phone_number": product_load.assigned_driver.phone_number if product_load.assigned_driver else None,
                },
                "loaded_product_list_and_quantity": loaded_product_list_and_quantity,
                "need_product_list_and_quantity": need_product_list_and_quantity,
            }
            all_loads_data.append(load_data)

        return paginator.get_paginated_response(
            {
                "success": True,
                "message": "All product loads with matching orders fetched successfully.",
                "data": all_loads_data,
            }
        )




class ProductLoadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ProductLoadSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "message": "Product load created successfully.",
                    "data": serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {
                "message": "Failed to create product load.",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class ProductLoadOrderMatchView(APIView):
    def get(self, request, load_id):
        try:
            # Step 1: Retrieve the ProductLoad instance by load_id
            product_load = ProductLoad.objects.get(id=load_id)

            # Step 2: Retrieve the matching orders based on delivery area and selected delivery date
            matching_orders = Order.objects.filter(
                delivery_area=product_load.delivery_area,
                delivery_date=product_load.selected_delivery_date,
            )

            # Debugging: If no matching orders are found
            if not matching_orders:
                print(
                    f"No matching orders found for delivery area '{product_load.delivery_area}' and date '{product_load.selected_delivery_date}'"
                )

            # Step 3: Collect the loaded products and quantities from the ProductLoad's LoadItems
            load_items = LoadItem.objects.filter(load=product_load)
            loaded_product_summary = defaultdict(int)
            for item in load_items:
                loaded_product_summary[item.product.name] += item.quantity

            # Step 4: Prepare the loaded products summary
            loaded_product_list_and_quantity = [
                {"product_name": name, "total_quantity": quantity}
                for name, quantity in loaded_product_summary.items()
            ]

            # Step 5: Prepare the needed product summary based on the orders found
            order_product_summary = defaultdict(int)
            for order in matching_orders:
                for order_item in order.items.all():
                    if order_item.product:
                        order_product_summary[order_item.product.name] += (
                            order_item.quantity
                        )

            # Step 6: Prepare the needed product list
            need_product_list_and_quantity = [
                {"product_name": name, "total_quantity_needed": quantity}
                for name, quantity in order_product_summary.items()
            ]

            # Prepare the final data to return
            data = {
                "delivery_area": product_load.delivery_area,
                "selected_delivery_date": product_load.selected_delivery_date,
                "notes": product_load.notes,
                "assigned_driver": {
                    "id": product_load.assigned_driver.id,
                    "full_name": product_load.assigned_driver.full_name,
                    "email": product_load.assigned_driver.email,
                    "phone_number": product_load.assigned_driver.phone_number,
                },
                "loaded_product_list_and_quantity": loaded_product_list_and_quantity,
                "need_product_list_and_quantity": need_product_list_and_quantity,
            }

            # Step 7: Return the result with both loaded and needed product lists
            return Response(
                {
                    "success": True,
                    "message": "Product load details fetched successfully.",
                    "data": data,
                },
                status=status.HTTP_200_OK,
            )

        except ProductLoad.DoesNotExist:
            return Response(
                {"message": "Product Load not found"}, status=status.HTTP_404_NOT_FOUND
            )
