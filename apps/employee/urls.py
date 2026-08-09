from django.urls import path
from .views import (
    EmployeeListCreateAPIView,
    EmployeeDetailAPIView,
)

urlpatterns = [
    # Employee list & create
    path("employee/", EmployeeListCreateAPIView.as_view(), name="employee-list-create"),

    # Employee detail, update, delete
    path("employee/<int:pk>/", EmployeeDetailAPIView.as_view(), name="employee-detail"),
]
