from rest_framework import serializers
from .models import Order, OrderItem, PaymentHistory, DeliveryNote, Invoice, Review
from datetime import date
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "username", "image"]


class ReviewSerializer(serializers.ModelSerializer):
    user_info = UserSerializer(read_only=True, source="user")
    order_id = serializers.PrimaryKeyRelatedField(read_only=True)  # mark order_id as read-only

    class Meta:
        model = Review
        fields = ["id", "user", "order_id", "rating", "comment", "created_at", "user_info"]
        read_only_fields = ["user", "order_id", "created_at", "user_info"]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)
    
class OrderItemSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source="product.category", read_only=True)
    class Meta:
        model = OrderItem
        fields = ["id", "product", "quantity", "price",'category', "total_price"]


class PaymentHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentHistory
        fields = [
            "id",
            "payment_method",
            "amount",
            "return_amount",
            "payment_status",
            "transaction_id",
            "payment_date",
        ]


class OrderListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "order_status",
            "ordered_date",
            "delivery_date",
            "payment_method",
            "total_amount",
            "delivery_area",
            "customer_info",
            "order_items",
        ]


class OrderSerializer(serializers.ModelSerializer):
    payments = PaymentHistorySerializer(many=True, read_only=True)
    customer_code = serializers.CharField(source="user.customer_code", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "user",
            "customer_code",
            "total_amount",
            "payment_method",
            "order_status",
            "ordered_date",
            "delivery_date",
            "delivery_area",
            "customer_info",
            "delivery_address",
            "payments",
            "order_items",
            "delivery_info",
            "return_info",
            "signature",
        ]


class DeliveryNoteSerializer(serializers.ModelSerializer):
    order = OrderSerializer(read_only=True)

    class Meta:
        model = DeliveryNote
        fields = ["id", "order", "delivery_details", "created_at"]


class AllInvoiceSerializer(serializers.ModelSerializer):
    order = OrderSerializer(read_only=True)

    class Meta:
        model = Invoice
        fields = [
            "id",
            "invoice_number",
            "invoice_date",
            "payment_status",
            "invoice_type",
            "created_at",
            "order",
        ]
