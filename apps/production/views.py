from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from .models import Production
from .serializers import ProductionSerializer
from apps.core.response import success_response, failure_response

# apps/production/views.py
from datetime import timedelta, datetime
from django.utils import timezone
from django.db.models import Sum
from django.db.models.functions import TruncDate, Coalesce
from django.db.models import DecimalField, Value
from apps.collection.models import YieldCalculation
from django.db.models import Sum, DecimalField, Value
from django.db.models.functions import Coalesce

WEEKDAY_LABELS = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
SAT_FIRST = ["Sat","Sun","Mon","Tue","Wed","Thu","Fri"]  # to match your UI







class YieldVisualizationAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            tz_today = timezone.localdate()
            start_param = request.GET.get("start")
            product = request.GET.get("product")

            if start_param:
                try:
                    start = datetime.strptime(start_param, "%Y-%m-%d").date()
                except ValueError:
                    return failure_response(
                        "Invalid start format. Use YYYY-MM-DD.",
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                dow = tz_today.weekday()  # Monday=0, Saturday=5
                days_since_sat = (dow - 5) % 7
                start = tz_today - timedelta(days=days_since_sat)

            # 7-day window (Sat → Fri)
            days = [start + timedelta(days=i) for i in range(7)]
            end_inclusive = days[-1]
            end_exclusive = end_inclusive + timedelta(days=1)

            qs = YieldCalculation.objects.all()
            if product:
                qs = qs.filter(product_name__iexact=product)

            # --- FIXED aggregation on DateField (no TruncDate) ---
            dec0 = Value(0, output_field=DecimalField(max_digits=12, decimal_places=2))
            agg = (
                qs.filter(date__gte=days[0], date__lt=end_exclusive)
                  .values("date")
                  .annotate(
                      forecasted=Coalesce(Sum("forecasted_yield"), dec0),
                      actual=Coalesce(Sum("actual_yield"), dec0),
                  )
                  .values("date", "forecasted", "actual")
            )
            by_date = {row["date"]: row for row in agg}

            # Build chart data
            labels = ["Sat", "Sun", "Mon", "Tue", "Wed", "Thu", "Fri"]
            forecasted_series, actual_series = [], []

            for day in days:
                row = by_date.get(day)
                forecasted_series.append(float(row["forecasted"]) if row else 0.0)
                actual_series.append(float(row["actual"]) if row else 0.0)

            payload = {
                "range": {"start": str(days[0]), "end": str(end_inclusive)},
                "labels": labels,
                "series": [
                    {"name": "Forecasted Yield (kg)", "data": forecasted_series},
                    {"name": "Actual Yield (kg)", "data": actual_series},
                ],
                "totals": {
                    "forecasted_yield": round(sum(forecasted_series), 2),
                    "actual_yield": round(sum(actual_series), 2),
                },
                "filters": {"product": product or None}
            }

            return success_response(
                "Yield visualization fetched successfully",
                data=payload,
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return failure_response(
                f"Unexpected error: {str(e)}",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProductionVisualizationAPIView(APIView):
    """
    GET /api/production/visualization/?start=YYYY-MM-DD&product=Yogurt
    Returns Sat..Fri window by default, with two series:
    - Produced (kg)
    - Milk Used (kg)
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            tz_today = timezone.localdate()
            start_param = request.GET.get("start")
            product = request.GET.get("product")

            if start_param:
                try:
                    start = datetime.strptime(start_param, "%Y-%m-%d").date()
                except ValueError:
                    return failure_response(
                        "Invalid start format. Use YYYY-MM-DD.",
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                # Find the most recent Saturday (Mon=0..Sun=6, Sat=5)
                dow = tz_today.weekday()
                days_since_sat = (dow - 5) % 7
                start = tz_today - timedelta(days=days_since_sat)

            # 7-day window Sat..Fri
            days = [start + timedelta(days=i) for i in range(7)]
            end_inclusive = days[-1]
            end_exclusive = end_inclusive + timedelta(days=1)

            qs = Production.objects.all()
            if product:
                qs = qs.filter(product_name__iexact=product)

            # Aggregate per calendar date
            agg = (
                qs.filter(created_at__date__gte=days[0], created_at__date__lt=end_exclusive)
                  .annotate(d=TruncDate("created_at"))
                  .values("d")
                  .annotate(
                      produced=Coalesce(Sum("quantity_produced_kg"), Value(0, output_field=DecimalField())),
                      milk_used=Coalesce(Sum("quantity_milk_used_kg"), Value(0, output_field=DecimalField())),
                  )
                  .values("d", "produced", "milk_used")
            )

            by_date = {row["d"]: row for row in agg}

            labels = ["Sat","Sun","Mon","Tue","Wed","Thu","Fri"]
            produced_series, milk_used_series = [], []

            for day in days:
                row = by_date.get(day)
                produced_series.append(float(row["produced"]) if row else 0.0)
                milk_used_series.append(float(row["milk_used"]) if row else 0.0)

            payload = {
                "range": {"start": str(days[0]), "end": str(end_inclusive)},
                "labels": labels,
                "series": [
                    {"name": "Produced (kg)", "data": produced_series},
                    {"name": "Milk Used (kg)", "data": milk_used_series},
                ],
                "totals": {
                    "produced_kg": round(sum(produced_series), 2),
                    "milk_used_kg": round(sum(milk_used_series), 2),
                },
                "filters": {"product": product or None}
            }

            # 👇 Wrap in your standard envelope
            return success_response(
                "Production visualization fetched successfully",
                data=payload,
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return failure_response(
                f"Unexpected error: {str(e)}",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProductionListCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        queryset = Production.objects.prefetch_related("ingredients").order_by(
            "-created_at"
        )
        serializer = ProductionSerializer(queryset, many=True)
        return Response({
            "status": "success",
            "status_code": status.HTTP_200_OK,
            "message": "All production record retrieve successfully",
            "count": queryset.count(),
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = ProductionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response({
                "status": "success",
                "status_code": status.HTTP_201_CREATED,
                "message": "Production record added successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": "error",
            "status_code": status.HTTP_400_BAD_REQUEST,
            "message": "Production record added failed",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ProductionDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        obj = get_object_or_404(
            Production.objects.prefetch_related("ingredients"), pk=pk
        )
        serializer = ProductionSerializer(obj)
        return Response({
            "status": "success",
            "status_code": status.HTTP_200_OK,
            "message": "Production record retrieve successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    def put(self, request, pk):
        obj = get_object_or_404(Production, pk=pk)
        serializer = ProductionSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "status": "success",
                    "status_code": status.HTTP_200_OK,
                    "message": "Production record updated successfully",
                    "data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        return Response(
            {
                "status": "error",
                "status_code": status.HTTP_400_BAD_REQUEST,
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request, pk):
        obj = get_object_or_404(Production, pk=pk)
        obj.delete()
        return Response(
            {
                "status": "success",
                "status_code": status.HTTP_204_NO_CONTENT,
                "message": "Production record deleted successfully",
            },
            status=status.HTTP_204_NO_CONTENT,
        )
