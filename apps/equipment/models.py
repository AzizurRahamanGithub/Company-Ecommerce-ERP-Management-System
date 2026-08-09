from django.db import models
from django.utils import timezone
from datetime import time

class EquipmentCleaning(models.Model):
    EQUIPMENT_LOCATIONS = [
        ('kitchen', 'Kitchen'),
        ('warehouse', 'Warehouse'),
    ]
    
    CLEANING_FREQUENCIES = [
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('daily', 'Daily'),
    ]
    
    
    cleaner_name = models.CharField(max_length=50, blank=True, null=True)
    equipment_name = models.CharField(max_length=255, blank=True, null=True)
    equipment_location = models.CharField(choices=EQUIPMENT_LOCATIONS, max_length=50)
    cleaning_frequency = models.CharField(choices=CLEANING_FREQUENCIES, max_length=50)
    tools_needed = models.CharField(max_length=255, blank=True, null=True)
    cleaning_agent = models.CharField(max_length=255, blank=True, null=True)
    cleaning_method = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    warning = models.TextField(blank=True, null=True)
    image = models.JSONField(blank=True, null=True)
    
    cleaning_date = models.DateField(blank=True, null=True)
    cleaning_time = models.TimeField(blank=True, null=True)
    

    
    def __str__(self):
        return f"{self.equipment_name} - {self.equipment_location}"


class AreaCleaning(models.Model):
    AREA_LOCATIONS = [
        ('kitchen', 'Kitchen'),
        ('warehouse', 'Warehouse'),
    ]
    
    CLEANING_FREQUENCIES = [
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('daily', 'Daily'),
    ]
    cleaner_name = models.CharField(max_length=50, blank=True, null=True)
    area_name = models.CharField(max_length=255, blank=True, null=True)
    area_location = models.CharField(choices=AREA_LOCATIONS, max_length=50)
    cleaning_frequency = models.CharField(choices=CLEANING_FREQUENCIES, max_length=50)
    tools_needed = models.CharField(max_length=255, blank=True, null=True)
    cleaning_agent = models.CharField(max_length=255, blank=True, null=True)
    cleaning_method = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    warning = models.TextField(blank=True, null=True)
    image = models.JSONField(blank=True, null=True)
    
    cleaning_date = models.DateField(blank=True, null=True)
    cleaning_time = models.TimeField(blank=True, null=True)
    
    

    
    def __str__(self):
        return f"{self.area_name} - {self.area_location}"
    
    
class CleaningSnapshot(models.Model):
    KIND_CHOICES = [
        ('equipment', 'Equipment'),
        ('area', 'Area'),
    ]
    kind = models.CharField(max_length=16, choices=KIND_CHOICES)
    ref_id = models.PositiveIntegerField()  # EquipmentCleaning.id or AreaCleaning.id

    # Keep them as strings to avoid parsing headaches
    cleaning_date_str = models.CharField(max_length=10, blank=True, null=True)  # "YYYY-MM-DD"
    cleaning_time_str = models.CharField(max_length=8, blank=True, null=True)   # "HH:MM:SS"

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('kind', 'ref_id')
        indexes = [
            models.Index(fields=['kind', 'ref_id']),
        ]

    def __str__(self):
        return f"{self.kind}#{self.ref_id} @ {self.cleaning_date_str} {self.cleaning_time_str or ''}"