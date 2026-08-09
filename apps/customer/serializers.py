from rest_framework import serializers
from apps.auths.models import CustomUser, Role
from .models import Customer, CustomerContact, DeliveryArea
from django.db import transaction


class DeliveryAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryArea
        fields = [ 'name' ]
        read_only_fields = ['id', 'created_at']

class CustomerContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerContact
        fields = ['id', 'role', 'first_name', 'middle_name', 'phone_number', 'billing_email', 'billing_address', 'billing_businnes_name']
        
        
# class CustomerSerializer(serializers.ModelSerializer):
#     # Nested/related bits
#     contacts = CustomerContactSerializer(many=True, required=False)

#     # Inputs for creating/updating the related CustomUser
#     username = serializers.CharField(write_only=True, required=False, allow_blank=True)
#     user_email_in = serializers.EmailField(write_only=True, required=True)     # input email
#     password = serializers.CharField(write_only=True, required=True)

#     # Outputs from the related CustomUser
#     email = serializers.EmailField(source='user.email', read_only=True)
#     is_active = serializers.BooleanField(source='user.is_active', read_only=True)

#     class Meta:
#         model = Customer
#         fields = [
#             'id', 'business_name', 'business_type', 'assign_price',
#             'customer_discount', 'tax_rate', 'delivery_address',
#             'customer_code', 'delivery_area', 'status', 'can_order',
#             'email', 'is_active',                       # outputs
#             'username', 'user_email_in', 'password',    # inputs
#             'contacts', 'created_at', 'updated_at'
#         ]
#         read_only_fields = ['id', 'created_at', 'updated_at', 'email', 'is_active']

#     # --- Validation against CustomUser uniqueness
#     def validate_username(self, value):
#         if value and CustomUser.objects.filter(username=value).exists():
#             raise serializers.ValidationError("Username already exists.")
#         return value

#     def validate_user_email_in(self, value):
#         if CustomUser.objects.filter(email=value).exists():
#             raise serializers.ValidationError("Email already exists.")
#         return value

#     def validate_customer_code(self, value):
#         if value and Customer.objects.filter(customer_code=value).exists():
#             raise serializers.ValidationError("Customer code already exists.")
#         return value

#     @transaction.atomic
#     def create(self, validated_data):
#         contacts_data = validated_data.pop('contacts', [])
#         username = validated_data.pop('username', None)
#         email_in = validated_data.pop('user_email_in')  # required=True so it exists
#         password = validated_data.pop('password')

#         user = CustomUser.objects.create_user(
#             email=email_in,
#             username=username or email_in.split('@')[0],
#             password=password,
#             role=Role.CUSTOMER,
#             is_active=True,
#         )

#         customer = Customer.objects.create(user=user, **validated_data)

#         for contact in contacts_data:
#             CustomerContact.objects.create(customer=customer, **contact)

#         return customer

#     @transaction.atomic
#     def update(self, instance, validated_data):
#         contacts_data = validated_data.pop('contacts', None)
#         username = validated_data.pop('username', None)
#         email_in = validated_data.pop('user_email_in', None)
#         password = validated_data.pop('password', None)

#         # Update related user if any user-field provided
#         if instance.user and any([username, email_in, password]):
#             if username:
#                 instance.user.username = username
#             if email_in:
#                 # enforce uniqueness on update
#                 if CustomUser.objects.filter(email=email_in).exclude(pk=instance.user.pk).exists():
#                     raise serializers.ValidationError({"user_email_in": "Email already exists."})
#                 instance.user.email = email_in
#             if password:
#                 instance.user.set_password(password)
#             instance.user.save()

#         # Update customer fields
#         for attr, value in validated_data.items():
#             setattr(instance, attr, value)
#         instance.save()

#         # Replace contacts if provided
#         if contacts_data is not None:
#             instance.contacts.all().delete()
#             for contact in contacts_data:
#                 CustomerContact.objects.create(customer=instance, **contact)

#         return instance



class CustomerContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerContact
        fields = ['id','role','first_name','middle_name','phone_number',
                  'billing_email','billing_address','billing_businnes_name']

class CustomerSerializer(serializers.ModelSerializer):
    contacts = CustomerContactSerializer(many=True, required=False)

    # WRITE-ONLY input fields for account
    account_email = serializers.EmailField(required=False, write_only=True)
    account_is_active = serializers.BooleanField(required=False, write_only=True)
    username = serializers.CharField(required=False, write_only=True, allow_blank=True)
    password = serializers.CharField(required=False, write_only=True, allow_blank=True)

    # READ-ONLY output fields (always shown)
    email = serializers.SerializerMethodField(read_only=True)
    is_active = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Customer
        fields = [
            'id','business_name','business_type','assign_price',
            'customer_discount','tax_rate','delivery_address',
            'customer_code','delivery_area','status','can_order',
            # output
            'email','is_active',
            # input for account mgmt
            'account_email','account_is_active','username','password',
            'contacts','created_at','updated_at'
        ]
        read_only_fields = ['id','created_at','updated_at','email','is_active']

    # ----- Output -----
    def get_email(self, obj):
        return obj.user.email if obj.user else None

    def get_is_active(self, obj):
        return obj.user.is_active if obj.user else False

    # ----- Validations -----
    def validate_customer_code(self, value):
        instance = getattr(self, 'instance', None)
        if instance:
            if Customer.objects.filter(customer_code=value).exclude(pk=instance.pk).exists():
                raise serializers.ValidationError("Customer code already exists.")
        else:
            if Customer.objects.filter(customer_code=value).exists():
                raise serializers.ValidationError("Customer code already exists.")
        return value

    # ----- Create -----
    def create(self, validated_data):
        contacts_data = validated_data.pop('contacts', [])
        account_email = validated_data.pop('account_email', None)
        account_is_active = validated_data.pop('account_is_active', True)
        username = validated_data.pop('username', None)
        password = validated_data.pop('password', None)

        user = None
        if account_email:
            if CustomUser.objects.filter(email=account_email).exists():
                raise serializers.ValidationError({"account_email": "Email already exists."})
            final_username = (username or account_email.split('@')[0])
            if CustomUser.objects.filter(username=final_username).exists():
                raise serializers.ValidationError({"username": "Username already exists."})
            if not password:
                raise serializers.ValidationError({"password": "Password is required when creating an account."})

            user = CustomUser.objects.create_user(
                email=account_email,
                username=final_username,
                password=password,
                role='user',
                is_active=bool(account_is_active),
            )

        customer = Customer.objects.create(user=user, **validated_data)

        for c in contacts_data:
            CustomerContact.objects.create(customer=customer, **c)

        return customer

    # ----- Update -----
    def update(self, instance, validated_data):
        contacts_data = validated_data.pop('contacts', None)
        account_email = validated_data.pop('account_email', None)
        account_is_active = validated_data.pop('account_is_active', None)
        username = validated_data.pop('username', None)
        password = validated_data.pop('password', None)

        user = instance.user

        # Create user if not exists but account fields provided
        if (account_email or username or password or account_is_active is not None) and user is None:
            if not account_email:
                raise serializers.ValidationError({"account_email": "Email is required to create user."})
            if CustomUser.objects.filter(email=account_email).exists():
                raise serializers.ValidationError({"account_email": "Email already exists."})
            final_username = (username or account_email.split('@')[0])
            if CustomUser.objects.filter(username=final_username).exists():
                raise serializers.ValidationError({"username": "Username already exists."})
            if not password:
                raise serializers.ValidationError({"password": "Password is required to create user."})
            user = CustomUser.objects.create_user(
                email=account_email,
                username=final_username,
                password=password,
                role=Role.CUSTOMER,
                is_active=bool(account_is_active) if account_is_active is not None else True,
            )
            instance.user = user

        # Update existing user
        if user:
            if account_email:
                if CustomUser.objects.filter(email=account_email).exclude(pk=user.pk).exists():
                    raise serializers.ValidationError({"account_email": "Email already exists."})
                user.email = account_email
            if username:
                if CustomUser.objects.filter(username=username).exclude(pk=user.pk).exists():
                    raise serializers.ValidationError({"username": "Username already exists."})
                user.username = username
            if password:
                user.set_password(password)
            if account_is_active is not None:
                user.is_active = bool(account_is_active)
            user.save()

        # Update customer fields
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()

        # Replace contacts if provided
        if contacts_data is not None:
            instance.contacts.all().delete()
            for c in contacts_data:
                CustomerContact.objects.create(customer=instance, **c)

        return instance