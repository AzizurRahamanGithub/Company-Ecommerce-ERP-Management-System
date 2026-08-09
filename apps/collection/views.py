from rest_framework.views import APIView
from rest_framework import status, permissions
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db.utils import IntegrityError

from apps.core.response import success_response, failure_response
from .models import MilkCollection, YieldCalculation
from .serializers import MilkCollectionSerializer, YieldCalculationSerializer
from apps.customer.models import Customer
from django.db.models import Sum, Avg
from django.utils import timezone
from datetime import timedelta, date
from django.db.models import Sum, F, Count

from rest_framework.response import Response
from datetime import datetime

from django.db.models import Sum, DecimalField, Value
from django.db.models.functions import Coalesce

from django.db.models import Avg
from django.db.models.functions import TruncMonth,  ExtractMonth
from rest_framework.views import APIView
from rest_framework import permissions, status
from .models import MilkCollection


class SupplierListAPIView(APIView):
    """
    GET /api/suppliers/?is_active=true or false
    Returns unique suppliers who have milk collection entries.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Get query param (?is_active=true/false)
        is_active_param = request.GET.get("is_active", "").lower()
        if is_active_param not in ["true", "false", ""]:
            return Response({
                "status": "error",
                "message": "Invalid is_active value. Use true or false."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Convert to boolean
        is_active = None
        if is_active_param == "true":
            is_active = True
        elif is_active_param == "false":
            is_active = False

        # Fetch distinct suppliers who appear in MilkCollection
        supplier_ids = (
            MilkCollection.objects
            .values_list("supplier_id", flat=True)
            .distinct()
        )

        suppliers = Customer.objects.filter(id__in=supplier_ids)
        if is_active is not None:
            suppliers = suppliers.filter(is_active=is_active)

        # Build response data
        data = [
            {
                "id": s.id,
                "business_name": s.business_name,
                "is_active": s.is_active,
                "user_id": getattr(s.user, "id", None),
                "username": getattr(s.user, "username", None),
            }
            for s in suppliers
        ]

        return Response({
            "status": "success",
            "message": "Suppliers fetched successfully",
            "count": len(data),
            "data": data
        }, status=status.HTTP_200_OK)


class MilkQualityVisualizationAPIView(APIView):
    """
    GET /api/milk/quality-visualization/?period=week|month|year

    period=week (default): Sat→Fri, group by date (daily)
    period=month: current month, group by date (daily)
    period=year: current year, group by month (monthly)

    Returns four series (average per bucket):
      - Average Fat (%)
      - Average Protein (%)
      - Average pH
      - Average SCC
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            period = (request.GET.get("period") or "week").lower()
            today = timezone.localdate()

            # ---------- Resolve range ----------
            if period == "week":
                # Most recent Saturday as start
                dow = today.weekday()  # Mon=0..Sun=6, Sat=5
                days_since_sat = (dow - 5) % 7
                start = today - timedelta(days=days_since_sat)
                days = [start + timedelta(days=i) for i in range(7)]
                end_inclusive = days[-1]
                end_exclusive = end_inclusive + timedelta(days=1)

            elif period == "month":
                start = today.replace(day=1)
                # next month
                next_month = (start + timedelta(days=32)).replace(day=1)
                end_inclusive = next_month - timedelta(days=1)
                end_exclusive = next_month
                days = [start + timedelta(days=i) for i in range((end_inclusive - start).days + 1)]

            elif period == "year":
                start = date(today.year, 1, 1)
                end_exclusive = date(today.year + 1, 1, 1)
                end_inclusive = end_exclusive - timedelta(days=1)
            else:
                return failure_response("Invalid period. Use 'week', 'month', or 'year'.", status=400)

            # ---------- Base queryset ----------
            qs = MilkCollection.objects.filter(
                date__gte=start,
                date__lt=end_exclusive,
                supplier__user__isnull=False
            )

            dec0 = Value(0, output_field=DecimalField(max_digits=12, decimal_places=2))

            # ---------- Aggregation ----------
            if period in ("week", "month"):
                # Group by date (DateField, no TruncDate needed on SQLite)
                agg = (
                    qs.values("date")
                      .annotate(
                          fat=Coalesce(Avg("fat_percentage"), dec0),
                          protein=Coalesce(Avg("protein_percentage"), dec0),
                          ph=Coalesce(Avg("ph"), dec0),
                          scc=Coalesce(Avg("scc"), dec0),
                      )
                      .values("date", "fat", "protein", "ph", "scc")
                )

                # map: date -> metrics
                by_bucket = {
                    r["date"]: {
                        "fat": float(r["fat"]),
                        "protein": float(r["protein"]),
                        "ph": float(r["ph"]),
                        "scc": float(r["scc"]),
                    } for r in agg
                }

                # Labels
                if period == "week":
                    labels = ["Sat", "Sun", "Mon", "Tue", "Wed", "Thu", "Fri"]
                    buckets = days
                else:  # month
                    labels = [str(d.day) for d in days]
                    buckets = days

                fat_data = []
                protein_data = []
                ph_data = []
                scc_data = []

                for b in buckets:
                    vals = by_bucket.get(b, {"fat": 0.0, "protein": 0.0, "ph": 0.0, "scc": 0.0})
                    fat_data.append(vals["fat"])
                    protein_data.append(vals["protein"])
                    ph_data.append(vals["ph"])
                    scc_data.append(vals["scc"])

            else:
                # period == "year": group by month number (1..12)
                agg = (
                    qs.annotate(m=ExtractMonth("date"))
                      .values("m")
                      .annotate(
                          fat=Coalesce(Avg("fat_percentage"), dec0),
                          protein=Coalesce(Avg("protein_percentage"), dec0),
                          ph=Coalesce(Avg("ph"), dec0),
                          scc=Coalesce(Avg("scc"), dec0),
                      )
                      .values("m", "fat", "protein", "ph", "scc")
                )
                by_bucket = {
                    r["m"]: {
                        "fat": float(r["fat"]),
                        "protein": float(r["protein"]),
                        "ph": float(r["ph"]),
                        "scc": float(r["scc"]),
                    } for r in agg
                }

                labels = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
                fat_data = [by_bucket.get(i+1, {"fat":0.0})["fat"] for i in range(12)]
                protein_data = [by_bucket.get(i+1, {"protein":0.0})["protein"] for i in range(12)]
                ph_data = [by_bucket.get(i+1, {"ph":0.0})["ph"] for i in range(12)]
                scc_data = [by_bucket.get(i+1, {"scc":0.0})["scc"] for i in range(12)]

            # ---------- Totals / Averages over buckets ----------
            n = len(labels)
            avg_fat = round(sum(fat_data) / n, 2) if n else 0.0
            avg_protein = round(sum(protein_data) / n, 2) if n else 0.0
            avg_ph = round(sum(ph_data) / n, 2) if n else 0.0
            avg_scc = round(sum(scc_data) / n, 2) if n else 0.0

            payload = {
                "range": {"start": str(start), "end": str(end_inclusive)},
                "labels": labels,
                "series": [
                    {"name": "Average Fat (%)", "data": fat_data},
                    {"name": "Average Protein (%)", "data": protein_data},
                    {"name": "Average pH", "data": ph_data},
                    {"name": "Average SCC", "data": scc_data},
                ],
                "totals": {
                    "average": {
                        "fat": avg_fat,
                        "protein": avg_protein,
                        "ph": avg_ph,
                        "scc": avg_scc
                    },
                    "by_bucket": {
                        "fat": fat_data,
                        "protein": protein_data,
                        "ph": ph_data,
                        "scc": scc_data
                    }
                },
                "filters": {"period": period}
            }

            return success_response(
                f"Milk quality visualization fetched successfully for {period}.",
                data=payload,
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return failure_response(f"Unexpected error: {str(e)}", status=500)



class SCCVisualizationAPIView(APIView):
    """
    GET /api/milk/scc-visualization/?period=week|month|year
    Returns average SCC over selected period.
    - week: Sat→Fri (daily)
    - month: current month (daily)
    - year: current year (monthly)
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            period = request.GET.get("period", "week").lower()  # default = week
            today = timezone.localdate()
            dec0 = Value(0, output_field=DecimalField(max_digits=14, decimal_places=2))

            # ---------- WEEKLY VIEW ----------
            if period == "week":
                dow = today.weekday()  # Mon=0..Sun=6
                days_since_sat = (dow - 5) % 7
                start = today - timedelta(days=days_since_sat)
                days = [start + timedelta(days=i) for i in range(7)]
                end_inclusive = days[-1]
                end_exclusive = end_inclusive + timedelta(days=1)

                qs = MilkCollection.objects.filter(date__gte=start, date__lt=end_exclusive)

                agg = (
                    qs.values("date")
                      .annotate(avg_scc=Coalesce(Avg("scc"), dec0))
                      .values("date", "avg_scc")
                )
                by_date = {row["date"]: float(row["avg_scc"]) for row in agg}

                labels = ["Sat", "Sun", "Mon", "Tue", "Wed", "Thu", "Fri"]
                scc_data = [by_date.get(day, 0.0) for day in days]
                avg_scc = round(sum(scc_data) / 7, 2)

                payload = {
                    "range": {"start": str(start), "end": str(end_inclusive)},
                    "labels": labels,
                    "series": [{"name": "Average SCC", "data": scc_data}],
                    "totals": {
                        "average_scc": avg_scc,
                        "by_day": scc_data
                    },
                    "filters": {"period": "week"}
                }

            # ---------- MONTHLY VIEW ----------
            elif period == "month":
                start = today.replace(day=1)
                next_month = (start + timedelta(days=32)).replace(day=1)
                end_exclusive = next_month

                qs = MilkCollection.objects.filter(date__gte=start, date__lt=end_exclusive)

                agg = (
                    qs.values("date")
                      .annotate(avg_scc=Coalesce(Avg("scc"), dec0))
                      .values("date", "avg_scc")
                )
                by_date = {row["date"]: float(row["avg_scc"]) for row in agg}

                # Day-by-day for full month
                days = [start + timedelta(days=i) for i in range((next_month - start).days)]
                labels = [str(day.day) for day in days]
                scc_data = [by_date.get(day, 0.0) for day in days]
                avg_scc = round(sum(scc_data) / len(days), 2)

                payload = {
                    "range": {"start": str(start), "end": str(days[-1])},
                    "labels": labels,
                    "series": [{"name": "Average SCC", "data": scc_data}],
                    "totals": {
                        "average_scc": avg_scc,
                        "by_day": scc_data
                    },
                    "filters": {"period": "month"}
                }

            # ---------- YEARLY VIEW ----------
            elif period == "year":
                start = date(today.year, 1, 1)
                end_exclusive = date(today.year + 1, 1, 1)

                qs = MilkCollection.objects.filter(date__gte=start, date__lt=end_exclusive)

                agg = (
                    qs.annotate(month=TruncMonth("date"))
                      .values("month")
                      .annotate(avg_scc=Coalesce(Avg("scc"), dec0))
                      .values("month", "avg_scc")
                )

                by_month = {row["month"].month: float(row["avg_scc"]) for row in agg}

                labels = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
                scc_data = [by_month.get(i+1, 0.0) for i in range(12)]
                avg_scc = round(sum(scc_data) / 12, 2)

                payload = {
                    "range": {"start": str(start), "end": str(end_exclusive.replace(day=1))},
                    "labels": labels,
                    "series": [{"name": "Average SCC", "data": scc_data}],
                    "totals": {
                        "average_scc": avg_scc,
                        "by_month": scc_data
                    },
                    "filters": {"period": "year"}
                }

            else:
                return failure_response("Invalid period. Use 'week', 'month', or 'year'.", status=400)

            # ---------- Final Response ----------
            return success_response(
                f"Average SCC visualization fetched successfully for {period}.",
                data=payload,
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return failure_response(f"Unexpected error: {str(e)}", status=500)



class MilkQualityFromSuplier(APIView):
    """
    GET /api/milk/weekly-ph/?start=YYYY-MM-DD
    - Calculates average pH value per day (Sat→Fri) across all suppliers.
    - Default window: most recent Saturday to Friday.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            tz_today = timezone.localdate()
            start_param = request.GET.get("start")

            # --- Determine start date (default: last Saturday) ---
            if start_param:
                try:
                    start = datetime.strptime(start_param, "%Y-%m-%d").date()
                except ValueError:
                    return failure_response(
                        "Invalid start format. Use YYYY-MM-DD.",
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                dow = tz_today.weekday()  # Monday=0..Sunday=6
                days_since_sat = (dow - 5) % 7  # Saturday index = 5
                start = tz_today - timedelta(days=days_since_sat)

            # --- Build 7-day window (Sat→Fri) ---
            days = [start + timedelta(days=i) for i in range(7)]
            end_inclusive = days[-1]
            end_exclusive = end_inclusive + timedelta(days=1)

            # --- Query & aggregate ---
            qs = MilkCollection.objects.filter(
                date__gte=days[0],
                date__lt=end_exclusive,
                supplier__user__isnull=False
            )

            dec0 = Value(0, output_field=DecimalField(max_digits=6, decimal_places=2))

            agg = (
                qs.values("date")
                  .annotate(avg_ph=Coalesce(Avg("ph"), dec0))
                  .values("date", "avg_ph")
            )

            # --- Map date → avg pH ---
            by_date = {row["date"]: float(row["avg_ph"]) for row in agg}

            labels = ["Sat", "Sun", "Mon", "Tue", "Wed", "Thu", "Fri"]
            ph_data = [by_date.get(day, 0.0) for day in days]

            # --- Compute overall weekly average ---
            avg_ph_week = round(sum(ph_data) / 7, 2)

            # --- Build final payload ---
            payload = {
                "range": {"start": str(days[0]), "end": str(end_inclusive)},
                "labels": labels,
                "series": [
                    {"name": "Average pH", "data": ph_data}
                ],
                "totals": {
                    "average_ph_week": avg_ph_week,
                    "by_day": ph_data
                },
                "filters": {}
            }

            return success_response(
                "Weekly average pH fetched successfully",
                data=payload,
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return failure_response(
                f"Unexpected error: {str(e)}",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class MilkWualityBySupplier(APIView):
    """
    GET /api/milk/weekly-fat-protein/?start=YYYY-MM-DD
    - Calculates the daily average fat% and protein% across all suppliers.
    - Default window: most recent Saturday → Friday.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            tz_today = timezone.localdate()
            start_param = request.GET.get("start")

            # --- Determine start date (default: last Saturday) ---
            if start_param:
                try:
                    start = datetime.strptime(start_param, "%Y-%m-%d").date()
                except ValueError:
                    return failure_response(
                        "Invalid start format. Use YYYY-MM-DD.",
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                dow = tz_today.weekday()  # Monday=0..Sunday=6
                days_since_sat = (dow - 5) % 7  # Saturday index = 5
                start = tz_today - timedelta(days=days_since_sat)

            # --- Build 7-day window ---
            days = [start + timedelta(days=i) for i in range(7)]
            end_inclusive = days[-1]
            end_exclusive = end_inclusive + timedelta(days=1)

            # --- Query & aggregate ---
            qs = MilkCollection.objects.filter(
                date__gte=days[0],
                date__lt=end_exclusive,
                supplier__user__isnull=False
            )

            dec0 = Value(0, output_field=DecimalField(max_digits=12, decimal_places=2))

            agg = (
                qs.values("date")
                  .annotate(
                      avg_fat=Coalesce(Avg("fat_percentage"), dec0),
                      avg_protein=Coalesce(Avg("protein_percentage"), dec0)
                  )
                  .values("date", "avg_fat", "avg_protein")
            )

            # --- Convert to {date: {...}} map ---
            by_date = {
                row["date"]: {
                    "fat": float(row["avg_fat"]),
                    "protein": float(row["avg_protein"])
                }
                for row in agg
            }

            # --- Build chart data ---
            labels = ["Sat", "Sun", "Mon", "Tue", "Wed", "Thu", "Fri"]
            fat_data, protein_data = [], []

            for day in days:
                vals = by_date.get(day, {"fat": 0.0, "protein": 0.0})
                fat_data.append(vals["fat"])
                protein_data.append(vals["protein"])

            # --- Compute weekly averages ---
            avg_fat_week = round(sum(fat_data) / 7, 2)
            avg_protein_week = round(sum(protein_data) / 7, 2)

            # --- Prepare payload ---
            payload = {
                "range": {"start": str(days[0]), "end": str(end_inclusive)},
                "labels": labels,
                "series": [
                    {"name": "Average Fat (%)", "data": fat_data},
                    {"name": "Average Protein (%)", "data": protein_data}
                ],
                "totals": {
                    "average_fat_week": avg_fat_week,
                    "average_protein_week": avg_protein_week,
                    "by_day": {
                        "fat": fat_data,
                        "protein": protein_data
                    }
                },
                "filters": {}
            }

            return success_response(
                "Weekly average fat and protein percentage fetched successfully",
                data=payload,
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return failure_response(
                f"Unexpected error: {str(e)}",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MilkPurchaseFromSuppliers(APIView):
    """
    GET /api/milk/weekly-supplier-quantities/?start=YYYY-MM-DD&suppliers=customer1,customer2
    - 7-day window (Sat→Fri) by default from the most recent Saturday
    - Optional filter: ?suppliers=<comma-separated usernames>
    - Output: labels=7 days, series=[{name:<supplier>, data:[gallons x7]}]
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            tz_today = timezone.localdate()
            start_param = request.GET.get("start")

            # --- Determine start date (default: most recent Saturday) ---
            if start_param:
                try:
                    start = datetime.strptime(start_param, "%Y-%m-%d").date()
                except ValueError:
                    return failure_response(
                        "Invalid start format. Use YYYY-MM-DD.",
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                dow = tz_today.weekday()  # Mon=0..Sun=6, Sat=5
                days_since_sat = (dow - 5) % 7
                start = tz_today - timedelta(days=days_since_sat)

            # --- Build 7-day range (Sat..Fri) ---
            days = [start + timedelta(days=i) for i in range(7)]
            end_inclusive = days[-1]
            end_exclusive = end_inclusive + timedelta(days=1)

            qs = MilkCollection.objects.filter(
                date__gte=days[0],
                date__lt=end_exclusive,
                supplier__user__isnull=False
            )

            dec0 = Value(0, output_field=DecimalField(max_digits=12, decimal_places=2))

            # --- Aggregate by date (sum all suppliers per day) ---
            agg = (
                qs.values("date")
                  .annotate(qty=Coalesce(Sum("quantity_gallon"), dec0))
                  .values("date", "qty")
            )

            by_date = {row["date"]: float(row["qty"]) for row in agg}

            # --- Build data array for Sat→Fri order ---
            labels = ["Sat", "Sun", "Mon", "Tue", "Wed", "Thu", "Fri"]
            data = [by_date.get(day, 0.0) for day in days]

            total_gallon = round(sum(data), 2)
            average_gallon = round(total_gallon / 7, 2)  # 7-day average

            # --- Build response payload ---
            payload = {
                "range": {"start": str(days[0]), "end": str(end_inclusive)},
                "labels": labels,
                "series": [
                    {"name": "Quantity (gallon)", "data": data}
                ],
                "totals": {
                    "quantity_gallon": total_gallon,   # weekly total
                    "average_gallon": average_gallon,   # daily average
                    "by_day": data                      # per-day totals
                },
                "filters": {}
            }

            return success_response(
                "Weekly daily quantity (gallon) fetched successfully",
                data=payload,
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return failure_response(
                f"Unexpected error: {str(e)}",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class YieldAlertAPIView(APIView):
    """
    View to alert users with yield calculations where the variance is <= -10%.
    """
    def get(self, request):
        try:
            # Get yield calculations where variance is <= -10%
            alert_yield_calculations = YieldCalculation.objects.filter(variance__lte=-10)
            
            if not alert_yield_calculations:
                return success_response(
                    "No yield calculations with variance <= -10%.",
                    {},
                )
            
            # Serialize the data
            serializer = YieldCalculationSerializer(alert_yield_calculations, many=True)

            # Return the alert with the yield calculations
            return success_response(
                "Alert: Yield calculations with variance <= -10%.",
                serializer.data,
                status.HTTP_200_OK
            )
        except Exception as e:
            return failure_response(
                f"Unexpected error: {str(e)}", 
                {},
            status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class YieldCalculationListCreateAPIView(APIView):
    """
    View to list all yield calculations or create a new yield calculation.
    """
    
    def get(self, request):
        """
        Get all yield calculations with optional pagination
        """
        yield_calculations = YieldCalculation.objects.all()
        serializer = YieldCalculationSerializer(yield_calculations, many=True)
        return success_response("Yield calculations retrieved successfully.", data=serializer.data)

    def post(self, request):
        """
        Create a new yield calculation and calculate variance.
        """
        serializer = YieldCalculationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()  # Calls save method which calculates variance
            return success_response("Yield calculation created successfully.", data=serializer.data, status=status.HTTP_201_CREATED)
        return failure_response("Failed to create yield calculation.", error=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AllSuppliersAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """
        GET method to fetch only suppliers with user accounts
        """
        try:
            # Get only suppliers who have user accounts
            suppliers = Customer.objects.select_related('user').filter(
                user__isnull=False
            ).order_by('business_name')

            # Prepare supplier data
            supplier_data = []
            for supplier in suppliers:
                user_roles = []
                if supplier.user.is_superuser:
                    user_roles.append('admin')
                if supplier.user.is_staff:
                    user_roles.append('staff')
                user_roles.append('user')

                supplier_data.append({
                    "id": supplier.id,
                    "username": supplier.user.username,
                    "email": supplier.user.email,
                    "roles": user_roles,
                    "is_active": supplier.user.is_active,
                    "created_at": supplier.created_at,
                })

            return success_response(
                "All suppliers with user accounts fetched successfully",
                data={
                    "total_suppliers": len(supplier_data),
                    "suppliers": supplier_data
                },
                status=status.HTTP_200_OK
            )
        
        except Exception as e:
            return failure_response(
                f"Unexpected error: {str(e)}", 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AllMilkCollectionHistoryAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """
        GET method to fetch the full milk collection history for all suppliers.
        """
        try:
            milk_collections = MilkCollection.objects.all().order_by('-date_time')

            if not milk_collections.exists():
                return success_response(
                    "No milk collection records found.",
                )

            # Serialize the milk collection data
            milk_collection_data = MilkCollectionSerializer(milk_collections, many=True).data

            return success_response(
                "All milk collection history fetched successfully.",
                data=milk_collection_data,
                status=status.HTTP_200_OK
            )
        
        except Exception as e:
            return failure_response(
                f"Unexpected error: {str(e)}", 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TodayMilkCollectionAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """
        GET method to fetch today's milk collection history.
        Query params: supplier_name (optional) - filter by supplier business name
        """
        try:
            # Get today's date
            today = timezone.now().date()
            
            # Get supplier_name from query params
            supplier_name = request.query_params.get('supplier_name', None)

            # Base query for today
            milk_collections = MilkCollection.objects.filter(date=today)

            # Apply supplier name filter if provided
            if supplier_name:
                milk_collections = milk_collections.filter(
                    supplier__business_name__icontains=supplier_name
                )

            # Order by latest first
            milk_collections = milk_collections.order_by('-date_time')

            if not milk_collections.exists():
                message = f"No milk collection records found for today"
                if supplier_name:
                    message += f" with supplier name containing '{supplier_name}'"
                return success_response(
                    message,
                )

            # Serialize the milk collection data
            milk_collection_data = MilkCollectionSerializer(milk_collections, many=True).data

            # Calculate totals
            total_weight = milk_collections.aggregate(
                total=Sum('weight_kg')
            )['total'] or 0
            
            total_quantity = milk_collections.aggregate(
                total=Sum('quantity_gallon')
            )['total'] or 0
            
            total_price = milk_collections.aggregate(
                total=Sum('total_price')
            )['total'] or 0

            response_data = {
                "date": str(today),
                "count": milk_collections.count(),
                "summary": {
                    "total_weight_kg": float(total_weight),
                    "total_quantity_gallon": float(total_quantity),
                    "total_price": float(total_price)
                },
                "collections": milk_collection_data
            }

            # Add filter info if applied
            if supplier_name:
                response_data['filter_applied'] = {
                    'supplier_name': supplier_name
                }

            return success_response(
                "Today's milk collection fetched successfully.",
                data=response_data,
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return failure_response(
                f"Unexpected error: {str(e)}", 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class NextDayMilkCollectionAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """
        GET method to fetch next day's milk collection history.
        Query params: supplier_name (optional) - filter by supplier business name
        """
        try:
            # Get next day's date
            today = timezone.now().date()
            next_day = today + timedelta(days=1)
            
            # Get supplier_name from query params
            supplier_name = request.query_params.get('supplier_name', None)

            # Base query for next day
            milk_collections = MilkCollection.objects.filter(date=next_day)

            # Apply supplier name filter if provided
            if supplier_name:
                milk_collections = milk_collections.filter(
                    supplier__business_name__icontains=supplier_name
                )

            # Order by latest first
            milk_collections = milk_collections.order_by('-date_time')

            if not milk_collections.exists():
                message = f"No milk collection records found for next day ({next_day})"
                if supplier_name:
                    message += f" with supplier name containing '{supplier_name}'"
                return success_response(
                    message,
                )

            # Serialize the milk collection data
            milk_collection_data = MilkCollectionSerializer(milk_collections, many=True).data

            # Calculate totals
            total_weight = milk_collections.aggregate(
                total=Sum('weight_kg')
            )['total'] or 0
            
            total_quantity = milk_collections.aggregate(
                total=Sum('quantity_gallon')
            )['total'] or 0
            
            total_price = milk_collections.aggregate(
                total=Sum('total_price')
            )['total'] or 0

            response_data = {
                "date": str(next_day),
                "count": milk_collections.count(),
                "summary": {
                    "total_weight_kg": float(total_weight),
                    "total_quantity_gallon": float(total_quantity),
                    "total_price": float(total_price)
                },
                "collections": milk_collection_data
            }

            # Add filter info if applied
            if supplier_name:
                response_data['filter_applied'] = {
                    'supplier_name': supplier_name
                }

            return success_response(
                "Next day's milk collection fetched successfully.",
                data=response_data,
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return failure_response(
                f"Unexpected error: {str(e)}", 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class WeeklyMilkCollectionHistoryAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """
        GET: Weekly (Saturday..Friday) collection & payment totals.
        - The week is fixed: starts on the most recent Saturday (including today if Saturday),
          ends on Friday. It only changes every 7 days (not daily).
        - Response returns a single 'data' object (no current/previous wrapper).
        """
        try:
            today = timezone.now().date()

            # Most recent Saturday (Saturday=5 for date.weekday(), where Monday=0)
            days_since_sat = (today.weekday() - 5) % 7
            week_start = today - timedelta(days=days_since_sat)         # Saturday (inclusive)
            week_end_excl = week_start + timedelta(days=7)              # next Saturday (exclusive)

            def build_week_payload(start_date, end_exclusive):
                rows = (
                    MilkCollection.objects
                    .filter(
                        date__gte=start_date,
                        date__lt=end_exclusive,
                        supplier__isnull=False
                    )
                    .values('supplier__id', 'supplier__business_name')
                    .annotate(
                        collection_count=Count('id'),
                        total_weight=Sum('weight_kg'),
                        total_quantity_gallon=Sum('quantity_gallon'),
                        total_base_price=Sum('total_price'),
                        total_bonus=Sum('bonus_price'),
                        total_penalty=Sum('penalty_price'),
                        total_payment=Sum(F('total_price') + F('bonus_price') - F('penalty_price')),
                    )
                    .order_by('supplier__business_name')
                )

                suppliers = []
                for r in rows:
                    base = float(r['total_base_price'] or 0)
                    bonus = float(r['total_bonus'] or 0)
                    penalty = float(r['total_penalty'] or 0)
                    final_payment = float(r['total_payment'] or 0)

                    suppliers.append({
                        "week_start": start_date.isoformat(),
                        "week_end": (end_exclusive - timedelta(days=1)).isoformat(),  # Friday
                        "supplier_id": r['supplier__id'],
                        "supplier_name": r['supplier__business_name'],
                        "collection_count": int(r['collection_count'] or 0),
                        "total_weight": float(r['total_weight'] or 0),
                        "total_quantity": float(r['total_quantity_gallon'] or 0),
                        "payment_details": {
                            "base_price": base,
                            "bonus": bonus,
                            "penalty": penalty,
                            "final_payment": final_payment,
                        },
                        "breakdown": f"Base: {base} + Bonus: {bonus} - Penalty: {penalty} = {final_payment}",
                    })

                summary = {
                    "total_collections": sum(s["collection_count"] for s in suppliers),
                    "total_weight": sum(s["total_weight"] for s in suppliers),
                    "total_quantity": sum(s["total_quantity"] for s in suppliers),
                    "total_base_price": sum(s["payment_details"]["base_price"] for s in suppliers),
                    "total_bonus": sum(s["payment_details"]["bonus"] for s in suppliers),
                    "total_penalty": sum(s["payment_details"]["penalty"] for s in suppliers),
                    "total_payment": sum(s["payment_details"]["final_payment"] for s in suppliers),
                }

                return {
                    "week_start": start_date.isoformat(),
                    "week_end": (end_exclusive - timedelta(days=1)).isoformat(),
                    "summary": summary,
                    "suppliers": suppliers,
                }

            data = build_week_payload(week_start, week_end_excl)

            return success_response(
                message="Weekly collection data fetched successfully.",
                data=data,
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return failure_response(
                message=f"Unexpected error: {str(e)}",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class WeeklyCollectionCountAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """
        GET method to fetch weekly collection count for current week and previous week
        Based on supplier's user (username and id)
        """
        try:
            # Get the start and end of the current week
            today = timezone.now().date()
            current_start_of_week = today - timedelta(days=today.weekday())  # Monday
            current_end_of_week = current_start_of_week + timedelta(days=7)  # Sunday

            # Get the start and end of the previous week
            previous_start_of_week = current_start_of_week - timedelta(days=7)
            previous_end_of_week = current_start_of_week  # Previous week ends when current week starts

            # Function to get weekly data
            def get_weekly_data(start_date, end_date):
                supplier_user_collections = (
                    MilkCollection.objects.filter(
                        date__gte=start_date,
                        date__lt=end_date,
                        supplier__user__isnull=False
                    )
                    .values('supplier__user__id', 'supplier__user__username', 'supplier__business_name')
                    .annotate(
                        collection_count=Count('id'),
                        total_weight=Sum('weight_kg'),
                        total_quantity_gallon=Sum('quantity_gallon'),
                        total_base_price=Sum('total_price'),
                        total_bonus=Sum('bonus_price'),
                        total_penalty=Sum('penalty_price'),
                        total_payment=Sum(F('bonus_price') - F('penalty_price') + F('total_price'))
                    )
                    .order_by('supplier__user__username')
                )

                supplier_user_data = []
                for supplier_user in supplier_user_collections:
                    base_price = float(supplier_user['total_base_price'] or 0)
                    bonus = float(supplier_user['total_bonus'] or 0)
                    penalty = float(supplier_user['total_penalty'] or 0)
                    final_payment = float(supplier_user['total_payment'] or 0)
                    
                    supplier_user_data.append({
                        "week_start": start_date,
                        "week_end": end_date - timedelta(days=1),
                        'user_id': supplier_user['supplier__user__id'],
                        'username': supplier_user['supplier__user__username'],
                        'business_name': supplier_user['supplier__business_name'],
                        'collection_count': supplier_user['collection_count'],
                        'total_weight': float(supplier_user['total_weight'] or 0),
                        'total_quantity_gallon': float(supplier_user['total_quantity_gallon'] or 0),
                        'payment_details': {
                            'base_price': base_price,
                            'bonus': bonus,
                            'penalty': penalty,
                            'final_payment': final_payment
                        },
                        'breakdown': f"Base: {base_price} + Bonus: {bonus} - Penalty: {penalty} = {final_payment}"
                    })

                # ✅ accurate totals (fixes summary zeros)
                summary = {
                    "total_volume": sum(s['collection_count'] for s in supplier_user_data),
                    "total_weight": sum(s['total_weight'] for s in supplier_user_data),
                    "total_quantity_gallon": sum(s['total_quantity_gallon'] for s in supplier_user_data),
                    "total_base_price": sum(s['payment_details']['base_price'] for s in supplier_user_data),
                    "total_bonus": sum(s['payment_details']['bonus'] for s in supplier_user_data),
                    "total_penalty": sum(s['payment_details']['penalty'] for s in supplier_user_data),
                    "total_payment": sum(s['payment_details']['final_payment'] for s in supplier_user_data),
                }

                return {
                    "week_start": start_date,
                    "week_end": end_date - timedelta(days=1),
                    "summary": summary,
                    "suppliers": supplier_user_data
                }


            # Get data for both weeks
            current_week_data = get_weekly_data(current_start_of_week, current_end_of_week)
            previous_week_data = get_weekly_data(previous_start_of_week, previous_end_of_week)

            return success_response(
                "Weekly collection count with payment details fetched successfully for current and previous week (by supplier user).",
                data={
                    "current_week": current_week_data,
                    "previous_week": previous_week_data
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return failure_response(
                f"Unexpected error: {str(e)}", 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
# ========== Milk Collection CRUD with Success and Error Responses ==========
class MilkCollectionListCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """
        GET method to fetch the full milk collection history for all suppliers.
        """
        try:
            # Get query parameters for date filtering
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            
            milk_collections = MilkCollection.objects.all().order_by('-date_time')

            # Apply date filters using the date field
            if start_date:
                try:
                    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
                    milk_collections = milk_collections.filter(date__gte=start_date_obj)
                except ValueError:
                    return failure_response(
                        "Invalid start_date format. Use YYYY-MM-DD.",
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            if end_date:
                try:
                    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
                    milk_collections = milk_collections.filter(date__lte=end_date_obj)
                except ValueError:
                    return failure_response(
                        "Invalid end_date format. Use YYYY-MM-DD.",
                        status=status.HTTP_400_BAD_REQUEST
                    )

            if not milk_collections.exists():
                return success_response(
                    "No milk collection records found for the selected date range.",
                )

            # Serialize the milk collection data
            milk_collection_data = MilkCollectionSerializer(milk_collections, many=True).data

            # Prepare response data
            response_data = {
                "count": milk_collections.count(),
                "data": milk_collection_data
            }

            # Add applied filters info
            filters_applied = {}
            if start_date:
                filters_applied['start_date'] = start_date
            if end_date:
                filters_applied['end_date'] = end_date
                
            if filters_applied:
                response_data['filters_applied'] = filters_applied

            return success_response(
                "All milk collection history fetched successfully.",
                data=response_data,
                status=status.HTTP_200_OK
            )
        
        except Exception as e:
            return failure_response(
                f"Unexpected error: {str(e)}", 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request):
        """
        POST method to create a new MilkCollection.
        """
        try:
            with transaction.atomic():
                # Deserialize and validate input data
                ser = MilkCollectionSerializer(data=request.data)
                if ser.is_valid():
                    # Save the milk collection with the current user as the collector
                    ser.save(collected_by=request.user)

                    # Return success response with created data
                    return success_response(
                        "Milk collection created successfully.",
                        ser.data,
                        status=status.HTTP_201_CREATED,
                    )

                # If validation fails, return failure response with errors
                return failure_response(
                    "Validation failed for milk collection.",
                    ser.errors,
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except (IntegrityError, ValidationError) as e:
            # Handle known database and validation exceptions
            return failure_response(
                "Could not create milk collection due to integrity or validation error.",
                str(e),
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            # Catch any unexpected exceptions
            return failure_response(
                "Unexpected error while creating milk collection.",
                str(e),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class MilkCollectionDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, pk):
        """
        Helper function to fetch MilkCollection object by ID.
        """
        return MilkCollection.objects.select_related("supplier", "collected_by").get(
            pk=pk
        )

    def get(self, request, pk):
        """
        GET method to fetch a specific MilkCollection by ID.
        """
        try:
            obj = self.get_object(pk)
            ser = MilkCollectionSerializer(obj)

            # Return success response with serialized data
            return success_response(
                "Milk collection fetched successfully.",
                ser.data,
                status=status.HTTP_200_OK,
            )
        except ObjectDoesNotExist:
            # Return failure response if MilkCollection not found
            return success_response(
                "Milk collection not found.",
                f"No record found with ID {pk}",
            )
        except Exception as e:
            # Catch other exceptions
            return failure_response(
                "Failed to fetch milk collection.",
                str(e),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def put(self, request, pk):
        """
        PUT method to update an existing MilkCollection by ID.
        """
        try:
            with transaction.atomic():
                obj = self.get_object(pk)
                ser = MilkCollectionSerializer(obj, data=request.data, partial=True)

                if ser.is_valid():
                    # Save the updated data
                    ser.save()

                    # Return success response with updated data
                    return success_response(
                        "Milk collection updated successfully.",
                        ser.data,
                        status=status.HTTP_200_OK,
                    )

                # If validation fails, return failure response with errors
                return failure_response(
                    "Validation failed for milk collection update.",
                    ser.errors,
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except ObjectDoesNotExist:
            # Return failure response if MilkCollection not found
            return success_response(
                "Milk collection not found.",
                f"No record found with ID {pk}",
            )
        except (IntegrityError, ValidationError) as e:
            # Handle known database and validation exceptions
            return failure_response(
                "Could not update milk collection due to integrity or validation error.",
                str(e),
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            # Catch any unexpected exceptions
            return failure_response(
                "Unexpected error while updating milk collection.",
                str(e),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def delete(self, request, pk):
        """
        DELETE method to delete a specific MilkCollection by ID.
        """
        try:
            with transaction.atomic():
                obj = self.get_object(pk)
                obj.delete()

                # Return success response on successful deletion
                return success_response(
                    "Milk collection deleted successfully.",
                    status=status.HTTP_204_NO_CONTENT,
                )
        except ObjectDoesNotExist:
            # Return failure response if MilkCollection not found
            return success_response(
                "Milk collection not found.",
                f"No record found with ID {pk}",
            )
        except Exception as e:
            # Catch any unexpected exceptions
            return failure_response(
                "Unexpected error while deleting milk collection.",
                str(e),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
