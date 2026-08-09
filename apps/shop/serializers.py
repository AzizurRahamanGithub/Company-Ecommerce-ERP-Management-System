from rest_framework import serializers
from .models import Products

class ProductsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Products
        fields = '__all__'

class ProductListsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Products
        fields = ['product_id', 'name', 'category','original_price', 'price', 'images']
