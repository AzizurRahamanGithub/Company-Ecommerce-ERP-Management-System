from django.db import models
from apps.auths.models import CustomUser  # তোমার main user model
from apps.employee.models import EmployeeProfile

class Production(models.Model):
    product_name = models.CharField(max_length=200)
    quantity_produced_kg = models.DecimalField(max_digits=10, decimal_places=2)
    batch_number = models.CharField(max_length=50, unique=True)
    quantity_milk_used_kg = models.DecimalField(max_digits=10, decimal_places=2)
    note = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='productions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product_name} ({self.batch_number})"


class ProductionIngredient(models.Model):
    production = models.ForeignKey(Production, on_delete=models.CASCADE, related_name="ingredients")
    ingredient_name = models.CharField(max_length=255)
    quantity_gallon = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.ingredient_name} - {self.quantity_gallon} gallon"
