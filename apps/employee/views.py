# employee/views.py
from rest_framework.views import APIView
from rest_framework import status, permissions
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db.utils import IntegrityError

from apps.core.response import success_response, failure_response
from .models import EmployeeProfile
from .serializers import EmployeeProfileSerializer
from .utils import caps_for
from django.db import models
from datetime import datetime


class EmployeeListCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            # Get query parameters for filtering and searching
            status_filter = request.query_params.get('status_filter')
            employment_type = request.query_params.get('employment_type')
            search = request.query_params.get('search', '').strip()
            start_date = request.query_params.get('start_date')  # New
            end_date = request.query_params.get('end_date')      # New
            
            # Debug: Print received parameters
            print(f"Received params - status_filter: '{status_filter}', employment_type: '{employment_type}', search: '{search}', start_date: '{start_date}', end_date: '{end_date}'")
            
            # Start with base queryset
            qs = EmployeeProfile.objects.select_related("user").order_by("-created_at")
            
            # Apply status filter
            if status_filter:
                qs = qs.filter(status=status_filter)
                print(f"Applied status filter: {status_filter}")
            
            # Apply employment type filter
            if employment_type:
                qs = qs.filter(employment_type=employment_type)
                print(f"Applied employment_type filter: {employment_type}")
            
            # Apply general search filter (all fields in one search)
            if search:
                qs = qs.filter(
                    models.Q(user__username__icontains=search) |
                    models.Q(user__email__icontains=search) |
                    models.Q(first_name__icontains=search) |
                    models.Q(last_name__icontains=search) |
                    models.Q(middle_name__icontains=search) |
                    models.Q(mobile_number__icontains=search) |
                    models.Q(telephone__icontains=search) |
                    models.Q(job_category__icontains=search) |
                    models.Q(address__icontains=search) |
                    models.Q(tin_number__icontains=search) |
                    models.Q(nis_number__icontains=search)
                )
                print(f"Applied search filter: {search}")
            
            # Apply date range filter based on start_date field
            if start_date:
                try:
                    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
                    qs = qs.filter(start_date__gte=start_date_obj)
                    print(f"Applied start_date filter: {start_date}")
                except ValueError:
                    return failure_response(
                        message="Invalid start_date format. Use YYYY-MM-DD.",
                        error="Date format error",
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            
            if end_date:
                try:
                    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
                    qs = qs.filter(start_date__lte=end_date_obj)
                    print(f"Applied end_date filter: {end_date}")
                except ValueError:
                    return failure_response(
                        message="Invalid end_date format. Use YYYY-MM-DD.",
                        error="Date format error", 
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            
            print(f"Total records after filtering: {qs.count()}")
            
            ser = EmployeeProfileSerializer(qs, many=True)
            
            
            # Add applied filters info
            filters_applied = {}
            
            if status_filter:
                filters_applied['status'] = status_filter
            if employment_type:
                filters_applied['employment_type'] = employment_type
            if search:
                filters_applied['search'] = search
            if start_date:
                filters_applied['start_date'] = start_date
            if end_date:
                filters_applied['end_date'] = end_date
                
            print(f"Filters to be applied in response: {filters_applied}")
            
            return success_response(
                message="Employee list fetched successfully",
                data=ser.data,
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            print(f"Error in employee list API: {str(e)}")
            return failure_response(
                message="Failed to fetch employees",
                error=str(e),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
            
            
            

    def post(self, request):
        try:
            with transaction.atomic():
                ser = EmployeeProfileSerializer(data=request.data)
                if ser.is_valid():
                    profile = ser.save()  # <-- এখানে আর user=request.user পাঠাচ্ছি না
                    return success_response(
                        message="Employee profile created successfully",
                        data= EmployeeProfileSerializer(profile).data,
                        status=status.HTTP_201_CREATED
                    )
                return failure_response(
                    message="Validation failed",
                    error=ser.errors,
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except (IntegrityError, ValidationError) as e:
            return failure_response(
                message="Could not create employee profile",
                error=str(e),
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return failure_response(
                message="Unexpected error occurred during creation",
                error=str(e),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class EmployeeDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, pk):
        return EmployeeProfile.objects.select_related("user").get(pk=pk)

    def get(self, request, pk):
        try:
            obj = self.get_object(pk)
            ser = EmployeeProfileSerializer(obj)
            return success_response(
                message="Employee profile fetched successfully",
                data= ser.data,
                status=status.HTTP_200_OK
            )
        except ObjectDoesNotExist:
            return failure_response(
                message="Employee profile not found",
                error=f"No employee with ID {pk}",
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return failure_response(
                message="Failed to fetch employee profile",
                error=str(e),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def put(self, request, pk):
        try:
            with transaction.atomic():
                obj = self.get_object(pk)
                ser = EmployeeProfileSerializer(obj, data=request.data, partial=True)
                if ser.is_valid():
                    ser.save()
                    return success_response(
                        message="Employee profile updated successfully",
                        data= ser.data,
                        status=status.HTTP_200_OK
                    )
                return failure_response(
                    message="Validation failed",
                    error=ser.errors,
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except ObjectDoesNotExist:
            return failure_response(
                message="Employee profile not found",
                error=f"No employee with ID {pk}",
                status=status.HTTP_404_NOT_FOUND,
            )
        except (IntegrityError, ValidationError) as e:
            return failure_response(
                message="Could not update employee profile",
                error=str(e),
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return failure_response(
                message="Unexpected error occurred during update",
                error=str(e),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def delete(self, request, pk):
        try:
            with transaction.atomic():
                obj = self.get_object(pk)
                obj.delete()
                return success_response(
                    message="Employee profile deleted successfully",
                    data={},
                    status=status.HTTP_204_NO_CONTENT,
                )
        except ObjectDoesNotExist:
            return failure_response(
                message="Employee profile not found",
                error=f"No employee with ID {pk}",
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return failure_response(
                message="Unexpected error occurred during deletion",
                error=str(e),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
