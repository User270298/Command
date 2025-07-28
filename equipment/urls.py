from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import MeasurementTypeViewSet, EquipmentRecordViewSet, autocomplete_name, autocomplete_device_type, autocomplete_tech_name, autocomplete_notes
from .views_templates import (
    measurement_type_list_view, equipment_record_create_view, my_records_view,
    export_csv_view, measurement_type_create_view, search_records_view,
    clear_equipment_records, equipment_record_edit_view, equipment_record_delete_view
)

# API routes
router = DefaultRouter()
router.register(r'measurement-types', MeasurementTypeViewSet, basename='measurement-type-api')
router.register(r'equipment-records', EquipmentRecordViewSet, basename='equipment-record-api')

# Разделяем API и шаблонные URL-маршруты
api_urlpatterns = [
    path('', include(router.urls)),
]

# URL-маршруты для шаблонов
urlpatterns = [
    path('measurement-types/', measurement_type_list_view, name='measurement_type_list'),
    path('measurement-types/create/', measurement_type_create_view, name='measurement_type_create'),
    path('record/create/', equipment_record_create_view, name='equipment_record_create'),
    path('my-records/', my_records_view, name='my_records'),
    path('export-csv/', export_csv_view, name='export_csv'),
    path('search/', search_records_view, name='search_records'),
    path('organization/<int:org_id>/clear/', clear_equipment_records, name='clear_equipment_records'),
    path('record/<int:record_id>/edit/', equipment_record_edit_view, name='equipment_record_edit'),
    path('record/<int:record_id>/delete/', equipment_record_delete_view, name='equipment_record_delete'),
]

urlpatterns += [
    path('autocomplete-name/', autocomplete_name, name='autocomplete_name'),
    path('autocomplete-device-type/', autocomplete_device_type, name='autocomplete_device_type'),
    path('autocomplete-tech-name/', autocomplete_tech_name, name='autocomplete_tech_name'),
    path('autocomplete-notes/', autocomplete_notes, name='autocomplete_notes'),
] 