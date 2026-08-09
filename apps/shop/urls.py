from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import ProductsViewSet, ProductListView, ProductRetrieveView

router = DefaultRouter()
router.register(r'product', ProductsViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('products/', ProductListView.as_view(), name='product-list'),
    path('products/<int:pk>/', ProductRetrieveView.as_view(), name='product-detail'),
]
