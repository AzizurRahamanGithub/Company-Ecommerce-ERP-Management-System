from django.db import models
from apps.auths.models import CustomUser  # optional link for credentials


class Customer(models.Model):
    # Core info
    business_name = models.CharField(max_length=255)
    business_type = models.CharField(max_length=100, blank=True, null=True)
    assign_price = models.CharField(max_length=120)
    customer_discount = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    delivery_address = models.TextField(blank=True, null=True)
    customer_code = models.CharField(max_length=50, unique=True)
    delivery_area = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=120, blank=True, null=True)
    can_order = models.CharField(blank=True, null=True)
    
    # One-to-one relationship with CustomUser
    user = models.OneToOneField(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name="customer_account")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["customer_code"], name="customer_code_idx"),
            models.Index(fields=["assign_price"], name="customer_price_idx"),
        ]

    def save(self, *args, **kwargs):
        """
        Automatically set the username for the related CustomUser instance 
        using the email before saving.
        """
        if self.user and self.user.email and not self.user.username:
            # Set username based on the first part of the email (before @)
            self.user.username = self.user.email.split('@')[0]
            self.user.save()  # Save the CustomUser instance to persist the username

        super().save(*args, **kwargs)  # Call the parent save() method

    @property
    def is_active(self):
        """Get active status from the related user model"""
        return self.user.is_active if self.user else False

    @property
    def email(self):
        """Get email from the related user model"""
        return self.user.email if self.user else None

    @is_active.setter
    def is_active(self, value):
        """Set active status to the related user model"""
        if self.user:
            self.user.is_active = value
            self.user.save()

    def activate(self):
        """Activate the customer (enable login)"""
        if self.user:
            self.user.is_active = True
            self.user.save()

    def deactivate(self):
        """Deactivate the customer (disable login)"""
        if self.user:
            self.user.is_active = False
            self.user.save()

    def __str__(self):
        return self.business_name



class CustomerContact(models.Model):
    ROLE_CHOICES = [
        ("primary", "Primary"),
        ("owner_manager", "Owner/Manager"),
        ("billing", "Billing")
        
    ]
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="contacts"
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=20)  # telephone or mobile, unified
    billing_address = models.TextField(blank=True, null=True)
    billing_email = models.EmailField(blank=True, null= True)
    billing_businnes_name= models.CharField(max_length=300, blank=True, null=True)

    def __str__(self):
        return f"{self.customer.business_name} - {self.role} - {self.first_name}"


class DeliveryArea(models.Model):
    # Name of the delivery area
    name = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=200, blank=True, null=True)
    region = models.CharField(max_length=200, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    
class DeliveryCustOff(models.Model):
    # Name of the delivery area
    name = models.CharField(max_length=200, blank=True, null=True)
    date = models.DateField(blank=True, null=True) 

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name    