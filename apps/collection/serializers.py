# apps/milk/serializers.py
from rest_framework import serializers
from .models import MilkCollection, YieldCalculation
from apps.customer.models import Customer

class MilkCollectionSerializer(serializers.ModelSerializer):
    # Write-only helpers
    supplier_username = serializers.CharField(write_only=True, required=False)
    supplier_id = serializers.IntegerField(write_only=True, required=False)

    # Read-only projection
    supplier = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = MilkCollection
        fields = [
            "id",
            "supplier",           # read-only: resolved snapshot
            "supplier_username",  # write-only: one of (username or id) required
            "supplier_id",        # write-only
            "collected_by",
            "date_time",
            "weight_kg",
            "fat_percentage",
            "protein_percentage",
            'date',
            "ph",
            "scc",
            "non_fat_solid",
            "conductivity",
            "quantity_gallon",
            "has_penalty",
            "penalty_reason",
            "penalty_amount",
            "total_price",
            "bonus_price",
            "penalty_price",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ("id", "created_at", "updated_at")

    def get_supplier(self, obj):
        c = obj.supplier
        return {
            "id": c.id,
            "business_name": c.business_name,
            "customer_code": c.customer_code,
            "username": getattr(c.user, "username", None),
        }

    def _resolve_supplier(self, attrs):
        supplier_username = attrs.pop("supplier_username", None)
        supplier_id = attrs.pop("supplier_id", None)

        if not supplier_username and not supplier_id:
            raise serializers.ValidationError(
                {"supplier": "Provide either supplier_username or supplier_id (Customer.id)."}
            )

        if supplier_username:
            try:
                return Customer.objects.select_related("user").get(user__username__iexact=supplier_username)
            except Customer.DoesNotExist:
                raise serializers.ValidationError({"supplier_username": "No customer found with this username."})

        # else supplier_id
        try:
            return Customer.objects.get(pk=supplier_id)
        except Customer.DoesNotExist:
            raise serializers.ValidationError({"supplier_id": "No customer found with this id."})

    def create(self, validated_data):
        supplier = self._resolve_supplier(validated_data)
        
        # Automatically set the date field from date_time
        if 'date' not in validated_data or not validated_data.get('date'):
            from django.utils import timezone
            validated_data['date'] = timezone.now().date()
        
        return MilkCollection.objects.create(supplier=supplier, **validated_data)

    def update(self, instance, validated_data):
        # allow changing supplier via username/id (optional)
        if "supplier_username" in validated_data or "supplier_id" in validated_data:
            instance.supplier = self._resolve_supplier(validated_data)

        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()
        return instance

from rest_framework import serializers
from datetime import datetime
from .models import YieldCalculation

class YieldCalculationSerializer(serializers.ModelSerializer):
    date = serializers.DateField(format="%Y-%m-%d")

    class Meta:
        model = YieldCalculation
        fields = ['id', 'product_name', 'forecasted_yield', 'actual_yield', 'variance', 'date', 'created_at', 'updated_at']
    
    # Optional date validation if you want additional checks
    def validate_date(self, value):
        # Ensure the date is in the correct format (Django handles this by default)
        if isinstance(value, str):
            try:
                datetime.strptime(value, '%Y-%m-%d')
            except ValueError:
                raise serializers.ValidationError("Invalid date format. Please use YYYY-MM-DD.")
        return value

    def create(self, validated_data):
        # Remove the 'date' field if it's included, but the model already handles it
        date = validated_data.pop('date', None)

        # Create the YieldCalculation object (the variance will be automatically calculated by the model)
        yield_calculation = YieldCalculation.objects.create(**validated_data, date=date)
        
        return yield_calculation
