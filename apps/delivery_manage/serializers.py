from rest_framework import serializers
from .models import ProductLoad, LoadItem
from apps.shop.models import Products
from apps.order.models import OrderItem


class ProductListsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Products
        fields = ["id", "name", "price", "images"]


class LoadItemSerializer(serializers.ModelSerializer):
    product_details = ProductListsSerializer(read_only=True, source="product")

    class Meta:
        model = LoadItem
        fields = [
            "id",
            "product",
            # "unit_type",
            "quantity",
            "box",
            "load",
            "product_details",
        ]


class ProductLoadSerializer(serializers.ModelSerializer):
    load_items = LoadItemSerializer(
        many=True
    )  # Use the correct field name: `load_items`

    class Meta:
        model = ProductLoad
        fields = [
            "id",
            "selected_delivery_date",
            "chosen_delivery_time",
            "assigned_driver",
            "delivery_area",
            "notes",
            "load_items",
        ]  # Use `load_items` here

    def create(self, validated_data):
        load_items_data = validated_data.pop("load_items")
        product_load = ProductLoad.objects.create(**validated_data)

        for item_data in load_items_data:
            LoadItem.objects.create(load=product_load, **item_data)

        return product_load


class LoadItemSerializerSummary(serializers.ModelSerializer):
    product_details = ProductListsSerializer(read_only=True, source="product")

    class Meta:
        model = LoadItem
        fields = [
            "id",
            # "unit_type",
            "quantity",
            "box",
            "product_details",
        ]
        
        