from rest_framework import serializers
from .models import EmployeeProfile
from django.contrib.auth import get_user_model
from apps.auths.models import Role

User = get_user_model()

class EmployeeProfileSerializer(serializers.ModelSerializer):
    # write-only fields to create CustomUser
    username = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True, min_length=6)
    is_active = serializers.BooleanField(write_only=True, required=False, default=True)

    # read-only fields from linked user
    user_username = serializers.CharField(source="user.username", read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_role = serializers.CharField(source="user.role", read_only=True)
    user_is_active = serializers.BooleanField(source="user.is_active", read_only=True)

    # Status and employment type choices as read-only fields for frontend
    # status_choices = serializers.SerializerMethodField(read_only=True)
    # employment_type_choices = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = EmployeeProfile
        fields = [
            # write-only for user creation
            "username", "email", "password", "is_active",

            # read-only mapped from user
            "user_username", "user_email", "user_role", "user_is_active",

            # choices for frontend
            # "status_choices", "employment_type_choices",

            # profile fields
            "id", "first_name", "middle_name", "last_name", "address",
            "mobile_number", "telephone", "extension", "date_of_birth",
            "tin_number", "nis_number",
            "job_category", "employment_type", "start_date", "status", "note",
            "wage_period", "current_wage_rate", "allowance_name", "total_compensation",
            "last_increase_date", "previous_rate",
            
            # permission fields
            "can_view_admin","can_edit_admin",
            "can_view_employee","can_edit_employee",
            "can_view_customer","can_edit_customer",
            "can_view_order","can_edit_order",
            "can_view_sales","can_edit_sales",
            "can_view_delivery","can_edit_delivery",
            "can_view_delivery_mnt","can_edit_delivery_mnt",
            "can_view_invoicing","can_edit_invoicing",
            "can_view_milk_collection","can_edit_milk_collection",
            "can_view_supplier_payment","can_edit_supplier_payment",
            "can_view_production","can_edit_production",
            "can_view_sanitation","can_edit_sanitation",
            "can_view_notification","can_edit_notification",
            "can_view_notification_mnt","can_edit_notification_mnt",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "user_username", "user_email", "user_role", "user_is_active",
            "status_choices", "employment_type_choices", "created_at", "updated_at"
        ]

    def get_status_choices(self, obj):
        """Get status choices for frontend"""
        return [choice[0] for choice in EmployeeProfile.STATUS_CHOICES]

    def get_employment_type_choices(self, obj):
        """Get employment type choices for frontend"""
        return [choice[0] for choice in EmployeeProfile.EMPLOYMENT_TYPE_CHOICES]

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists.")
        return value

    def validate_email(self, value):
        if value and User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists.")
        return value

    def create(self, validated_data):
        # pop write-only user fields
        username = validated_data.pop("username")
        email = validated_data.pop("email", None)
        password = validated_data.pop("password")
        is_active = validated_data.pop("is_active", True)

        # create the CustomUser with role=employee
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            role=Role.EMPLOYEE,
            is_active=is_active,
            is_staff=False,
            is_superuser=False,
        )

        # create employee profile linked to that user
        profile = EmployeeProfile.objects.create(user=user, **validated_data)
        return profile

    def update(self, instance, validated_data):
        # Handle user fields update
        username = validated_data.pop("username", None)
        email = validated_data.pop("email", None)
        password = validated_data.pop("password", None)
        is_active = validated_data.pop("is_active", None)

        # Update user fields if provided
        if username and instance.user.username != username:
            instance.user.username = username
        if email and instance.user.email != email:
            instance.user.email = email
        if password:
            instance.user.set_password(password)
        if is_active is not None:
            instance.user.is_active = is_active
        
        if username or email or password or is_active is not None:
            instance.user.save()

        # Update profile fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        return instance