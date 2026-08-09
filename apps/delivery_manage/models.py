from django.db import models
from apps.auths.models import CustomUser
from apps.shop.models import Products


class ProductLoad(models.Model):
    selected_delivery_date = models.DateField()
    chosen_delivery_time = models.TimeField(blank=True, null=True)
    assigned_driver = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    notes = models.TextField()
    delivery_area = models.CharField(max_length=255)

    def __str__(self):
        return f"Load for {self.delivery_area} on {self.selected_delivery_date}"


class LoadItem(models.Model):
    product = models.ForeignKey(Products, on_delete=models.CASCADE)
    # unit_type = models.CharField(
    #     max_length=255,
    #     choices=[("kg", "Kilogram"), ("litre", "Litre"), ("piece", "Piece")],
    # )
    quantity = models.PositiveIntegerField()
    load = models.ForeignKey(
        ProductLoad,
        on_delete=models.CASCADE,
        related_name="load_items",
        blank=True,
        null=True,
    )  # Correct related_name
    box = models.CharField(max_length=255, blank=True, null=True)
