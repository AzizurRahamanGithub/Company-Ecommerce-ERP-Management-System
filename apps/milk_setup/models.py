from django.db import models

class Milk_Setup(models.Model):
    setup_name = models.CharField(max_length=255, blank=True, null=True)
    value = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)  # Automatically set when the object is created
    updated_at = models.DateTimeField(auto_now=True)      # Automatically set to current time whenever the object is updated

    def __str__(self):
        return self.setup_name


class Milk_Quality(models.Model):
    quality_name = models.CharField(max_length=255)
    lower_limit = models.DecimalField(max_digits=10, decimal_places=2)
    upper_limit = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)  # Automatically set when the object is created
    updated_at = models.DateTimeField(auto_now=True)      # Automatically set to current time whenever the object is updated

    def __str__(self):
        return self.quality_name
