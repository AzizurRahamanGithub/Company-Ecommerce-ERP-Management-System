from rest_framework import generics
from rest_framework.response import Response
from apps.core.pagination import CustomPagination

class BaseListAPIView(generics.ListAPIView):
    pagination_class = CustomPagination  
      
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        # Use DRF pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        # No pagination
        serializer = self.get_serializer(queryset, many=True)

        # auto-generate success message based on model name
        model_name = queryset.model.__name__
        success_message = f"All {model_name.lower()}s fetched successfully"

        return Response(
            {
                "success": True,
                "statusCode": 200,
                "message": success_message,
                "data": serializer.data,
            }
        )


# class AllPackageList(BaseListAPIView):
#     queryset = Package.objects.all().order_by('-id')
#     serializer_class = PackageSerializer
