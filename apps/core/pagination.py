from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
import math

class CustomPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 1000

    def get_paginated_response(self, data):
        return Response({
            "success": True,
            "statusCode": 200,
            "message": "Data fetched successfully",
            "current_page": self.page.number,  # current active page number
            "total_pages": math.ceil(self.page.paginator.count / self.get_page_size(self.request)),  # total number of pages
            "count": self.page.paginator.count,  # total number of items
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
            "data": data,
        })
