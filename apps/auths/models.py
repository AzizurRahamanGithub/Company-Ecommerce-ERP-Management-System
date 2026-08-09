# authapp/models.py
from datetime import timedelta
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone
import string
import random


# ----------------------------------
# Roles
# ----------------------------------
class Role(models.TextChoices):
    ADMIN = "admin", "Admin"
    EMPLOYEE = "employee", "Employee"
    USER = "user", "User"
    SANITIZER = "sanitizer", "Sanitizer"


# ----------------------------------
# Custom User Manager
# ----------------------------------
class CustomUserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, username=None, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        if "is_active" not in extra_fields:
            user.is_active = True
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username=None, password=None, **extra_fields):
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", Role.ADMIN)
        return self.create_user(email, username, password, **extra_fields)


# ----------------------------------
# Custom User Model
# ----------------------------------
class CustomUser(AbstractUser):
    email = models.EmailField(unique=True, null=True, blank=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.USER)

    # Optional profile info
    full_name = models.CharField(max_length=255, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    image = models.JSONField(blank=True, null=True)
    customer_code = models.CharField(max_length=20, blank=True, null=True)
    stripe_customer_id = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    USERNAME_FIELD = "email"  # 👈 Login with username
    REQUIRED_FIELDS = ["username"]  # Still collect email for contact or reset

    objects = CustomUserManager()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        indexes = [
            models.Index(fields=["username"], name="username_idx"),
            models.Index(fields=["email"], name="email_idx"),
            models.Index(fields=["role"], name="role_idx"),
        ]

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        if not self.customer_code:
            self.customer_code = "".join(
                random.choices(string.ascii_uppercase + string.digits, k=8)
            )
        super().save(*args, **kwargs)


# ----------------------------------
# OTP / Reset Profile
# ----------------------------------
class UserProfile(models.Model):
    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name="auth_profile"
    )
    otp = models.CharField(max_length=6, null=True, blank=True)
    otp_created_at = models.DateTimeField(auto_now_add=True)
    reset_token = models.CharField(max_length=100, null=True, blank=True)
    reset_token_expires = models.DateTimeField(null=True, blank=True)

    def generate_otp(self):
        self.otp = str(random.randint(100000, 999999))
        self.otp_created_at = timezone.now()
        self.save()
        return self.otp

    def is_otp_expired(self):
        if self.otp_created_at:
            return timezone.now() > self.otp_created_at + timedelta(minutes=10)
        return True

    def generate_reset_token(self):
        self.reset_token = "".join(
            random.choices(string.ascii_uppercase + string.digits, k=32)
        )
        self.reset_token_expires = timezone.now() + timedelta(minutes=5)
        self.save()
        return self.reset_token

    def is_reset_token_expired(self):
        if self.reset_token_expires:
            return timezone.now() > self.reset_token_expires
        return True

    def __str__(self):
        return f"AuthProfile({self.user.username})"


class MyAddress(models.Model):
    ADDRESS_TYPE_CHOICES = [
        ("billing", "Billing"),
        ("shipping", "Shipping"),
        ("home", "Home"),
        ("office", "Office"),
    ]

    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="addresses"
    )
    type = models.CharField(
        max_length=100, choices=ADDRESS_TYPE_CHOICES, blank=True, null=True
    )
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.user.email} - {self.type}: {self.address}"
