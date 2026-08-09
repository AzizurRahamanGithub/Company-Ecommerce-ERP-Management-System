from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotFound
from .models import EquipmentCleaning, AreaCleaning
from .serializers import EquipmentCleaningSerializer, AreaCleaningSerializer
from rest_framework.permissions import IsAuthenticated
from ..core.response import failure_response, success_response
from apps.auths.models import CustomUser, Role
from .utils import norm_date_str, norm_time_str

# apps/equipment/views.py
from datetime import datetime, timedelta, time
from django.utils import timezone
from django.db.models import Q
from datetime import time as dtime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import CleaningSnapshot

def _score_from_time(t: time) -> float:
    """Return 1.0 if cleaned before 10:00, 0.5 if after 10:00, 0 if missing."""
    if t is None:
        return 0.5
    cutoff = time(10, 0, 0)
    return 1.0 if t < cutoff else 0.5


def _score_from_time_str(tstr: str) -> float:
    """
    Rules:
    - no date/time => 0
    - time < 10:00 => 1.0
    - time >= 10:00 => 0.5
    """
    if not tstr:
        return 0.0
    # tstr is "HH:MM[:SS]"
    try:
        hh, mm, *rest = tstr.split(":")
        ss = rest[0] if rest else "00"
        t = dtime(int(hh), int(mm), int(ss))
    except Exception:
        return 0.0
    cutoff = dtime(10, 0, 0)
    return 1.0 if t < cutoff else 0.5

def _label(overall_100: float) -> str:
    if overall_100 < 40:
        return "Poor"
    elif overall_100 < 70:
        return "Fair"
    return "Excellent"

class CleaningOverallScoreAPIView(APIView):
    """
    GET /api/cleaning/overall-score-snapshot/
    Uses latest snapshots of all equipment & areas to compute:
      - per-item score (1/0.5/0)
      - overall_score_100 (avg * 100)
      - performance label
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = CleaningSnapshot.objects.all()

        items = []
        scores = []

        for s in qs:
            # If no date => 0 (missed)
            if not s.cleaning_date_str:
                sc = 0.0
            else:
                sc = _score_from_time_str(s.cleaning_time_str) if s.cleaning_time_str else 0.0

            scores.append(sc)
            items.append({
                "kind": s.kind,
                "ref_id": s.ref_id,
                "date": s.cleaning_date_str,
                "time": s.cleaning_time_str,
                "score": sc
            })

        overall_100 = round((sum(scores) / len(scores) * 100.0), 2) if scores else 0.0
        comment = _label(overall_100)

        payload = {
            "items": items,
            "overall_score_100": overall_100,
            "comment": comment
        }
        return Response({
            "status": "success",
            "message": "Overall snapshot score calculated",
            "data": payload
        }, status=status.HTTP_200_OK)


class CleaningKPIAPIView(APIView):
    """
    GET /api/cleaning/kpi/
    Calculates:
      - day-wise scores (1 / 0.5 / 0)
      - per-item weekly scores (0–100)
      - combined overall score and performance rating
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            today = timezone.localdate()
            start_param = request.GET.get("start")

            # Determine start of 7-day range (Sat→Fri)
            if start_param:
                try:
                    start = datetime.strptime(start_param, "%Y-%m-%d").date()
                except ValueError:
                    return failure_response("Invalid start format. Use YYYY-MM-DD.", status=400)
            else:
                dow = today.weekday()  # Mon=0..Sun=6
                days_since_sat = (dow - 5) % 7
                start = today - timedelta(days=days_since_sat)

            days = [start + timedelta(days=i) for i in range(7)]
            end_inclusive = days[-1]

            # ---------- Helper ----------
            def build_block(model, label_fields):
                rows = (
                    model.objects
                    .filter(cleaning_date__gte=days[0], cleaning_date__lte=end_inclusive)
                    .values('cleaning_date', 'cleaning_time', *label_fields)
                )

                item_keys = set()
                for r in rows:
                    key = tuple(r[f] for f in label_fields)
                    item_keys.add(key)

                # Compute per-day score per item
                day_map = {}
                for r in rows:
                    d = r['cleaning_date']
                    s = _score_from_time(r['cleaning_time'])
                    key = tuple(r[f] for f in label_fields)
                    prev = day_map.get((key, d))
                    if prev is None or s > prev:
                        day_map[(key, d)] = s

                items = []
                for key in sorted(item_keys):
                    daily = [day_map.get((key, d), 0.0) for d in days]
                    weekly_score = round((sum(daily) / 7) * 100, 2)
                    items.append({
                        "name": " - ".join([str(x) for x in key if x]),
                        "daily": daily,
                        "weekly_score_100": weekly_score
                    })

                return items

            # ---------- Compute for equipment & area ----------
            eq_items = build_block(EquipmentCleaning, ("equipment_name", "equipment_location"))
            ar_items = build_block(AreaCleaning, ("area_name", "area_location"))

            # Combine all item scores
            all_scores = [x["weekly_score_100"] for x in eq_items + ar_items]
            overall_score = round(sum(all_scores) / len(all_scores), 2) if all_scores else 0.0

            # Determine performance level
            if overall_score < 40:
                level = "Poor"
            elif overall_score < 70:
                level = "Fair"
            else:
                level = "Excellent"

            payload = {
                "range": {"start": str(days[0]), "end": str(end_inclusive)},
                "equipment": eq_items,
                "area": ar_items,
                "overall": {
                    "overall_score_100": overall_score,
                    "performance_level": level
                }
            }

            return success_response(
                "Cleaning KPI with performance rating fetched successfully",
                data=payload,
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return failure_response(f"Unexpected error: {str(e)}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class AllSenitizersAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        GET method to fetch only users with sanitizer role
        """
        try:
            # Get only users with sanitizer role
            sanitizers = CustomUser.objects.filter(
                role=Role.SANITIZER
            ).order_by('username')

            # Prepare sanitizer data
            sanitizer_data = []
            for sanitizer in sanitizers:
                user_roles = [sanitizer.role]  # Get the role from the role field
                
                if sanitizer.is_superuser:
                    user_roles.append('admin')
                if sanitizer.is_staff:
                    user_roles.append('staff')

                sanitizer_data.append({
                    "id": sanitizer.id,
                    "username": sanitizer.username,
                    "email": sanitizer.email,
                    "role": sanitizer.role,  # Main role
                    "roles": user_roles,     # All roles including admin/staff
                    "is_active": sanitizer.is_active,
                    "is_staff": sanitizer.is_staff,
                    "is_superuser": sanitizer.is_superuser,
                    "full_name": sanitizer.full_name,
                    "phone_number": sanitizer.phone_number,
                    "address": sanitizer.address,
                    "customer_code": sanitizer.customer_code,
                    "created_at": sanitizer.created_at,
                })

            return success_response(
                "All sanitizers fetched successfully",
                data={
                    "total_sanitizers": len(sanitizer_data),
                    "sanitizers": sanitizer_data
                },
                status=status.HTTP_200_OK
            )
        
        except Exception as e:
            return failure_response(
                f"Unexpected error: {str(e)}", 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# Equipment Cleaning Views
class EquipmentCleaningListCreateAPIView(APIView):
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """GET method to list all equipment cleanings"""
        cleanings = EquipmentCleaning.objects.all()
        serializer = EquipmentCleaningSerializer(cleanings, many=True)
        return Response({
            'status': 'success',
            'data': serializer.data
        }, status=status.HTTP_200_OK)  # 200 OK for success

    def post(self, request):
        """POST method to create a new equipment cleaning"""
        serializer = EquipmentCleaningSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'status': 'success',
                'message': 'Equipment cleaning created successfully',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)  # 201 Created when successfully created
        return Response({
            'status': 'error',
            'message': 'Validation failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)  # 400 Bad Request if validation fails


class EquipmentCleaningDetailAPIView(APIView):
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        """GET method to fetch a specific equipment cleaning by ID"""
        try:
            cleaning = EquipmentCleaning.objects.get(pk=pk)
            serializer = EquipmentCleaningSerializer(cleaning)
            return Response({
                'status': 'success',
                'message': 'Equipment Cleaning fetched successfully',
                'data': serializer.data
            }, status=status.HTTP_200_OK)  # 200 OK when record is found
        except EquipmentCleaning.DoesNotExist:
            raise NotFound(detail="Equipment Cleaning not found.", code=status.HTTP_404_NOT_FOUND)  # 404 Not Found if not found

    def put(self, request, pk):
        """PUT method to update a specific equipment cleaning by ID"""
        try:
            cleaning = EquipmentCleaning.objects.get(pk=pk)
        except EquipmentCleaning.DoesNotExist:
            raise NotFound(detail="Equipment Cleaning not found.", code=status.HTTP_404_NOT_FOUND)

        serializer = EquipmentCleaningSerializer(cleaning, data=request.data, partial=True)
        if serializer.is_valid():
            updated = serializer.save()  # Save the updated data

            # ✅ NEW: overwrite latest snapshot for this equipment (simple string snapshot)
            cd = norm_date_str(getattr(updated, "cleaning_date", None))   # "YYYY-MM-DD" or None
            ct = norm_time_str(getattr(updated, "cleaning_time", None))   # "HH:MM:SS" or None

            CleaningSnapshot.objects.update_or_create(
                kind="equipment",
                ref_id=updated.id,
                defaults={
                    "cleaning_date_str": cd,
                    "cleaning_time_str": ct,
                }
            )

            return Response({
                'status': 'success',
                'message': 'Equipment Cleaning updated successfully',
                'data': serializer.data
            }, status=status.HTTP_200_OK)

        return Response({
            'status': 'error',
            'message': 'Validation failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)



# Area Cleaning Views
class AreaCleaningListCreateAPIView(APIView):
    def get(self, request):
        """GET method to list all area cleanings"""
        cleanings = AreaCleaning.objects.all()
        serializer = AreaCleaningSerializer(cleanings, many=True)
        return Response({
            'status': 'success',
            'data': serializer.data
        }, status=status.HTTP_200_OK)  # 200 OK when successfully retrieved

    def post(self, request):
        """POST method to create a new area cleaning"""
        serializer = AreaCleaningSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'status': 'success',
                'message': 'Area cleaning created successfully',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)  # 201 Created for successful creation
        return Response({
            'status': 'error',
            'message': 'Validation failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)  # 400 Bad Request if validation fails


class AreaCleaningDetailAPIView(APIView):
    def get(self, request, pk):
        """GET method to fetch a specific area cleaning by ID"""
        try:
            cleaning = AreaCleaning.objects.get(pk=pk)
            serializer = AreaCleaningSerializer(cleaning)
            return Response({
                'status': 'success',
                'message': 'Area Cleaning fetched successfully',
                'data': serializer.data
            }, status=status.HTTP_200_OK)  # 200 OK when record is found
        except AreaCleaning.DoesNotExist:
            raise NotFound(detail="Area Cleaning not found.", code=status.HTTP_404_NOT_FOUND)  # 404 Not Found if not found

    def put(self, request, pk):
        try:
            cleaning = AreaCleaning.objects.get(pk=pk)
        except AreaCleaning.DoesNotExist:
            raise NotFound(detail="Area Cleaning not found.", code=status.HTTP_404_NOT_FOUND)

        serializer = AreaCleaningSerializer(cleaning, data=request.data, partial=True)
        if serializer.is_valid():
            updated = serializer.save()  # <-- existing line

            # ------------ NEW: update latest snapshot (always overwrite) ------------
            cd = norm_date_str(getattr(updated, "cleaning_date", None))
            ct = norm_time_str(getattr(updated, "cleaning_time", None))

            CleaningSnapshot.objects.update_or_create(
                kind="area",
                ref_id=updated.id,
                defaults={
                    "cleaning_date_str": cd,   # "YYYY-MM-DD" or None
                    "cleaning_time_str": ct,   # "HH:MM:SS" or None
                }
            )
            # ------------------------------------------------------------------------

            return Response({
                'status': 'success',
                'message': 'Area Cleaning updated successfully',
                'data': serializer.data
            }, status=status.HTTP_200_OK)

        return Response({
            'status': 'error',
            'message': 'Validation failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
