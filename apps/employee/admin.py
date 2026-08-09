from django.contrib import admin
from .models import EmployeeProfile

class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'job_category', 'employment_type', 'status')
    search_fields = ('first_name', 'last_name', 'email', 'username')

admin.site.register(EmployeeProfile, EmployeeAdmin)
