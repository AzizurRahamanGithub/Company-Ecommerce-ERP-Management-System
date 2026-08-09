from rest_framework import serializers
from .models import Cart, CartItem
from apps.shop.serializers import ProductListsSerializer as ProductSerializer


class CartItemSerializer(serializers.ModelSerializer):
    product_details = ProductSerializer(read_only=True, source='product')
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity', 'total_price', 'product_details']


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    shipping_cost = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_cost = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'user', 'created_at', 'subtotal', 'shipping_cost', 'total_cost', 'items']
