from django.contrib import admin
from .models import EquipmentCleaning, AreaCleaning
from django.contrib.admin import ModelAdmin
from .forms import SingleImageForm, MultipleImagesForm



class EquipmentCleaningAdmin(ModelAdmin):

    form = type(
        'EquipmentCleaningSingleImageForm',
        (SingleImageForm,), 
        {
            'Meta': type('Meta', (SingleImageForm.Meta,), {'model': EquipmentCleaning}),
            'image_folder': 'equipmentCleaning'  # Custom folder for images
        }
    )

    model = EquipmentCleaning  

    list_display = (
        'equipment_name', 'equipment_location', 'cleaning_frequency', 'tools_needed',
        'cleaning_agent', 'cleaning_method'  # Removed 'created_at' if not added to model
    )

    list_filter = ('equipment_location', 'cleaning_frequency', 'cleaning_agent')

    search_fields = ('equipment_name', 'equipment_location', 'cleaning_agent', 'tools_needed')

    ordering = ('equipment_name',)  # Remove 'created_at' unless added to the model

    fieldsets = (
        ('For Admin', {
            'fields': (('equipment_name', 'equipment_location', 'cleaning_frequency', 'tools_needed'), 'warning', 'upload_image', 'delete_image')
        }),
        ('For Employee', {
            'fields': (('cleaner_name', 'cleaning_date', 'cleaning_time'), 'notes')
        }),
        ('Status', {
            'fields': ('cleaning_agent',)
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('equipment_name', 'equipment_location', 'cleaning_frequency', 'tools_needed', 'cleaning_agent')
        }),
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

# Register the EquipmentCleaning model with its admin configuration
admin.site.register(EquipmentCleaning, EquipmentCleaningAdmin)



class AreaCleaningAdmin(ModelAdmin):

    form = type(
        'AreaCleaningSingleImageForm',
        (SingleImageForm,), 
        {
            'Meta': type('Meta', (SingleImageForm.Meta,), {'model': AreaCleaning}),
            'image_folder': 'areaCleaning'  # Custom folder for images
        }
    )

    model = EquipmentCleaning  

    list_display = (
        'area_name', 'area_location', 'cleaning_frequency', 'tools_needed',
        'cleaning_agent', 'cleaning_method'  # Removed 'created_at' if not added to model
    )

    list_filter = ('area_location', 'cleaning_frequency', 'cleaning_agent')

    search_fields = ('area_name', 'area_location', 'cleaning_agent', 'tools_needed')

    ordering = ('area_name',)  # Remove 'created_at' unless added to the model

    fieldsets = (
        ('For Admin', {
            'fields': (('area_name', 'area_location', 'cleaning_frequency', 'tools_needed'), 'warning', 'upload_image', 'delete_image')
        }),
        ('For Employee', {
            'fields': (('cleaner_name', 'cleaning_date', 'cleaning_time'), 'notes')
        }),
        ('Status', {
            'fields': ('cleaning_agent',)
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('area_name', 'area_location', 'cleaning_frequency', 'tools_needed', 'cleaning_agent')
        }),
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

# Register the EquipmentCleaning model with its admin configuration
admin.site.register(AreaCleaning, AreaCleaningAdmin)
