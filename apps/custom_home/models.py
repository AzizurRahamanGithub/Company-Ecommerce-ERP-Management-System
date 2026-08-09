from django.db import models

class CustomDashboard(models.Model):
    class Meta:
        verbose_name = "Dashboard"
        verbose_name_plural = "Dashboard"