from django.urls import path
from .views import ProductLoadView,ProductLoadOrderMatchView,AllProductLoadView

urlpatterns = [
    path("product-load/", ProductLoadView.as_view(), name="product-load-create"),
    path("product-load/all/", AllProductLoadView.as_view(), name="product-load-all"),
    path('product-load/match/<int:load_id>/', ProductLoadOrderMatchView.as_view(), name='product-load-match'),
]
