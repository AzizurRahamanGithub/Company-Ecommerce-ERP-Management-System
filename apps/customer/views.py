from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from .models import Customer, DeliveryArea
from .serializers import CustomerSerializer,CustomerContactSerializer, DeliveryAreaSerializer
from rest_framework.permissions import IsAuthenticated
from django.db import models




class DeliveryAreaListView(APIView):
    def get(self, request):
        """
        GET request to list all delivery areas with error handling.
        """
        try:
            # Retrieve all delivery areas from the database
            delivery_areas = DeliveryArea.objects.all()

            # Serialize the data
            serializer = DeliveryAreaSerializer(delivery_areas, many=True)

            # Return a success response with the serialized data
            return Response({
                "status": "success",
                "status_code": status.HTTP_200_OK,
                "message": "Delivery areas retrieved successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            # Catch any unexpected exceptions and return a failure response
            return Response({
                "status": "error",
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "An error occurred while retrieving delivery areas.",
                "error": str(e)  # Include the error message for debugging (in a real production setting, avoid exposing raw error messages)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CustomerListCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            # Get query parameters for filtering
            is_active = request.query_params.get('is_active')
            search = request.query_params.get('search', '').strip()
            
            # Retrieve the customer data along with related contacts
            qs = Customer.objects.prefetch_related("contacts").order_by("-created_at")
            
            # Apply active/inactive filters (based on user's is_active)
            if is_active is not None:
                if is_active.lower() == 'true':
                    qs = qs.filter(user__is_active=True)
                elif is_active.lower() == 'false':
                    qs = qs.filter(user__is_active=False)
            
            # Apply search filter
            if search:
                qs = qs.filter(
                    models.Q(business_name__icontains=search) |
                    models.Q(customer_code__icontains=search) |
                    models.Q(business_type__icontains=search) |
                    models.Q(delivery_area__icontains=search) |
                    models.Q(contacts__first_name__icontains=search) |
                    models.Q(contacts__phone_number__icontains=search)
                ).distinct()
            
            ser = CustomerSerializer(qs, many=True)
            
            response_data = {
                "status": "success",
                "status_code": status.HTTP_200_OK,
                "message": "Customer retrieve successfully",
                "count": qs.count(),
                "data": ser.data
            }
            
            # Add filter info to response if any filter was applied
            filters_applied = {}
            if filters_applied:
                response_data["filters_applied"] = filters_applied
            if is_active is not None:
                filters_applied["is_active"] = is_active
            if search:
                filters_applied["search"] = search
                
            
            
            return Response(response_data, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                "status": "error",
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": f"Unexpected error: {str(e)}",
                "data": None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        ser = CustomerSerializer(data=request.data)
        if ser.is_valid():
            ser.save()
            return Response({
                "status": "success",
                "status_code": status.HTTP_201_CREATED,
                "message": "Customer created successfully",
                "data": ser.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": "error",
            "status_code": status.HTTP_400_BAD_REQUEST,
            "message": "Customer not created successfully",
            "errors": ser.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class CustomerDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        # Get the customer with related contacts
        obj = get_object_or_404(Customer.objects.prefetch_related("contacts"), pk=pk)
        ser = CustomerSerializer(obj)
        return Response({
            "status": "success",
            "status_code": status.HTTP_200_OK,
            "message": "Customer retieve successfully",
            "data": ser.data
        }, status=status.HTTP_200_OK)

    def put(self, request, pk):
        obj = get_object_or_404(Customer, pk=pk)
        ser = CustomerSerializer(obj, data=request.data, partial=True)
        if ser.is_valid():
            ser.save()
            return Response({
                "status": "success",
                "status_code": status.HTTP_200_OK,
                "message": "Customer updated successfully",
                "data": ser.data
            }, status=status.HTTP_200_OK)
        return Response({
            "status": "error",
            "status_code": status.HTTP_400_BAD_REQUEST,
            "message": "Customer not updated successfully",
            "errors": ser.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        obj = get_object_or_404(Customer, pk=pk)
        obj.delete()
        return Response(
            {
                "status": "success",
                "status_code": status.HTTP_204_NO_CONTENT,
                "message": "Customer deleted successfully",
            },
            status=status.HTTP_204_NO_CONTENT,
        )


class CustomerInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            customer = Customer.objects.get(user=request.user)
            contacts = customer.contacts.all()  
            contact_serializer = CustomerContactSerializer(contacts, many=True)

            return Response({
                'success': True,
                'statusCode': 200,
                'message': 'Customer information retrieved successfully',
                'data': {
                    'contacts': contact_serializer.data
                }
            }, status=200)

        except Customer.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Customer not found'
            }, status=404)