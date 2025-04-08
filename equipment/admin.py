from django.contrib import admin
from .models import MeasurementType, EquipmentRecord

@admin.register(MeasurementType)
class MeasurementTypeAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']

@admin.register(EquipmentRecord)
class EquipmentRecordAdmin(admin.ModelAdmin):
    list_display = ['name', 'device_type', 'measurement_type', 'organization', 'user', 'quantity', 'date_created']
    list_filter = ['measurement_type', 'date_created', 'organization']
    search_fields = ['name', 'device_type', 'serial_number', 'tech_name']
