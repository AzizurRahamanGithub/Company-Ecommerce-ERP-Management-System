from django.urls import path
from .views import CartView, AddToCartView, RemoveFromCartView, ClearCartView,CartItemQuantityView,UpdateCartProductQuantityView

urlpatterns = [
    path('', CartView.as_view(), name='cart-detail'),
    path('add/', AddToCartView.as_view(), name='cart-add'),
    path('remove/<int:product_id>/', RemoveFromCartView.as_view(), name='cart-remove'),
    path('clear/', ClearCartView.as_view(), name='cart-clear'),
    path('update/<int:product_id>/', CartItemQuantityView.as_view(), name='cart-update'),
    path('update-quantity/<int:product_id>/', UpdateCartProductQuantityView.as_view(), name='cart-update-quantity'),
]
