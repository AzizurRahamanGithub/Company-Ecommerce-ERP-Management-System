from django.urls import path
from .views import CustomerListCreateAPIView, CustomerDetailAPIView,CustomerInfoView, DeliveryAreaListView

urlpatterns = [
    path('customer/', CustomerListCreateAPIView.as_view(), name='customer-list-create'),
    path('customer/<int:pk>/', CustomerDetailAPIView.as_view(), name='customer-detail'),
    path('my/info/', CustomerInfoView.as_view(), name='customer-info'),
    path('customer/area/', DeliveryAreaListView.as_view(), name='customer-info'),
]
