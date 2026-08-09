from django.db import models
from django.contrib.auth import get_user_model
from apps.shop.models import Products

User = get_user_model()


class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("delivered", "Delivered"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]
    PAYMENT_METHODS = [
        ("stripe", "Stripe"),
        ("charge_account", "Charge Account"),
        ("cash", "Cash on Delivery"),
        ("cheque", "Cheque"),
        ("mmg", "MMG"),
    ]
    payment_method = models.CharField(
        max_length=50, choices=PAYMENT_METHODS, default="stripe"
    )
    order_number = models.CharField(max_length=255, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    customer_info = models.JSONField(default=dict)
    order_items = models.JSONField(default=list)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    order_status = models.CharField(
        max_length=255, choices=STATUS_CHOICES, default="pending"
    )
    ordered_date = models.DateTimeField(auto_now_add=True)
    delivery_date = models.DateField(null=True, blank=True)
    delivery_address = models.JSONField(default=dict)
    delivery_area = models.CharField(max_length=255, blank=True, null=True)
    delivery_info = models.JSONField(default=dict)
    return_info = models.JSONField(default=dict)
    signature = models.JSONField(default=dict)

    def __str__(self):
        return f"Order #{self.order_number}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Products, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    @property
    def total_price(self):
        if self.price is not None and self.quantity is not None:
            return self.price * self.quantity
        return 0

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"


class PaymentHistory(models.Model):
    PAYMENT_METHODS = [
        ("stripe", "Stripe"),
        ("charge_account", "Charge Account"),
        ("cash", "Cash on Delivery"),
        ("cheque", "Cheque"),
        ("mmg", "MMG"),
    ]

    order = models.ForeignKey(
        Order, related_name="payments", on_delete=models.CASCADE, null=True, blank=True
    )
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHODS)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    return_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_status = models.CharField(
        max_length=50, default="pending"
    )  # completed, failed
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    payment_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.payment_method} - {self.amount}"


class DeliveryNote(models.Model):
    order = models.OneToOneField(
        Order, related_name="delivery_note", on_delete=models.CASCADE
    )
    delivery_details = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Delivery Note #{self.order.order_number}"


INVOICE_TYPES = [
    ("payment_receipt", "Payment Receipt"),
    ("delivery_note", "Delivery Note"),
]


class Invoice(models.Model):
    order = models.OneToOneField(
        Order, related_name="invoice", on_delete=models.CASCADE
    )
    invoice_number = models.CharField(max_length=255, unique=True)
    invoice_date = models.DateTimeField(auto_now_add=True)
    payment_status = models.CharField(max_length=50, default="pending")
    invoice_type = models.CharField(
        max_length=50, choices=INVOICE_TYPES, blank=True, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invoice #{self.invoice_number}"

    class Meta:
        verbose_name = "Invoice"
        verbose_name_plural = "Invoices"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = f"INV-{self.order.order_number}"
        super().save(*args, **kwargs)


class Review(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="reviews", null=True, blank=True
    )
    order_id = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="reviews"
    )  # Link the review with an order
    rating = models.PositiveIntegerField()
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review for Order #{self.order_id.order_number} by {self.user}"

    class Meta:
        verbose_name = "Review"
        verbose_name_plural = "Reviews"
