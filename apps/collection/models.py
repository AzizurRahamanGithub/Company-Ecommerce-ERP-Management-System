# apps/milk/models.py (or apps/customer/models.py if you keep it there)
from django.db import models
from apps.customer.models import Customer               # existing Customer (has OneToOne to CustomUser)
from apps.auths.models import CustomUser    
from datetime import date# collected_by

class MilkCollection(models.Model):
    supplier = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="milk_collections"
    )
    collected_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, related_name="milk_collections"
    )

    date_time = models.DateTimeField(auto_now_add=True)
    weight_kg = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fat_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    protein_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    ph = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    scc = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    non_fat_solid = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    conductivity = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    quantity_gallon = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    has_penalty = models.BooleanField(default=False)
    penalty_reason = models.CharField(max_length=255, blank=True, null=True)
    penalty_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    penalty_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    bonus_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # other fields...
    date=models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["date_time"], name="mc_datetime_idx"),
            models.Index(fields=["total_price"], name="mc_price_idx"),
        ]

    def __str__(self):
        sup = getattr(self.supplier, "business_name", "Unknown")
        return f"{sup} - {self.date_time.strftime('%Y-%m-%d %H:%M')}"





class YieldCalculation(models.Model):
    product_name = models.CharField(max_length=255)
    forecasted_yield = models.DecimalField(max_digits=10, decimal_places=2)
    actual_yield = models.DecimalField(max_digits=10, decimal_places=2)
    variance = models.DecimalField(max_digits=5, decimal_places=2, editable=False)  # Make variance read-only

    # other fields...
    date = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Calculate the variance between forecasted and actual yields
        if self.forecasted_yield != 0:
            self.variance = ((self.actual_yield - self.forecasted_yield) / self.forecasted_yield) * 100
        else:
            self.variance = None  # Or assign some specific value like None, -1, etc.
        super(YieldCalculation, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.product_name} - {self.date}"

