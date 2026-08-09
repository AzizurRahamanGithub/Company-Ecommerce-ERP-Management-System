from django.contrib import admin
from .models import Milk_Setup, Milk_Quality
from django.utils import timezone

# ----------------------
# Milk_Setup Admin
# ----------------------
class Milk_SetupAdmin(admin.ModelAdmin):
    list_display = ('setup_name', 'value', 'created_at', 'updated_at')
    list_filter = ('setup_name', 'value', 'created_at', 'updated_at')  # tuple or list
    search_fields = ('setup_name', 'value')

    # Make timestamps read-only (non-editable fields)
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        (None, {'fields': ('setup_name', 'value')}),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['mark_as_updated']

    # Action to manually update updated_at timestamp
    def mark_as_updated(self, request, queryset):
        queryset.update(updated_at=timezone.now())
    mark_as_updated.short_description = "Mark selected setups as updated"


# ----------------------
# Milk_Quality Admin
# ----------------------
class Milk_QualityAdmin(admin.ModelAdmin):
    list_display = ('quality_name', 'lower_limit', 'upper_limit', 'created_at', 'updated_at')
    list_filter = ('quality_name', 'lower_limit', 'upper_limit', 'created_at', 'updated_at')
    search_fields = ('quality_name',)

    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        (None, {'fields': ('quality_name', 'lower_limit', 'upper_limit')}),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['mark_as_updated']

    def mark_as_updated(self, request, queryset):
        queryset.update(updated_at=timezone.now())
    mark_as_updated.short_description = "Mark selected qualities as updated"


# ----------------------
# Register Models
# ----------------------
admin.site.register(Milk_Setup, Milk_SetupAdmin)
admin.site.register(Milk_Quality, Milk_QualityAdmin)
    