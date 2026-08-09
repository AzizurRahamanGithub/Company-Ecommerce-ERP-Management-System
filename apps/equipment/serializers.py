from rest_framework import serializers
from .models import EquipmentCleaning, AreaCleaning

class EquipmentCleaningSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentCleaning
        fields = [
            'id','cleaner_name', 'equipment_name', 'equipment_location', 'cleaning_frequency', 
            'tools_needed', 'cleaning_agent', 'cleaning_method', 'notes', 
            'warning', 'image', 'cleaning_date', 'cleaning_time'
        ]
        read_only_fields = ['id']  # Make the ID and timestamps read-only

class AreaCleaningSerializer(serializers.ModelSerializer):
    class Meta:
        model = AreaCleaning
        fields = [
            'id', 'cleaner_name', 'area_name', 'area_location', 'cleaning_frequency', 
            'tools_needed', 'cleaning_agent', 'cleaning_method', 'notes', 
            'warning', 'image', 'cleaning_date', 'cleaning_time'
        ]
        read_only_fields = ['id']  # Make the ID and timestamps read-only


