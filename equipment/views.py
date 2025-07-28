from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import JsonResponse
from django.db.models import Q
from .models import MeasurementType, EquipmentRecord
from .serializers import MeasurementTypeSerializer, EquipmentRecordSerializer


class MeasurementTypeViewSet(viewsets.ModelViewSet):
    queryset = MeasurementType.objects.all()
    serializer_class = MeasurementTypeSerializer


class EquipmentRecordViewSet(viewsets.ModelViewSet):
    queryset = EquipmentRecord.objects.all()
    serializer_class = EquipmentRecordSerializer


@api_view(['GET'])
def autocomplete_name(request):
    """Автодополнение для поля наименования"""
    term = request.GET.get('term', '')
    if len(term) < 2:
        return JsonResponse([], safe=False)
    
    names = EquipmentRecord.objects.filter(
        name__icontains=term
    ).values_list('name', flat=True).distinct()[:10]
    
    return JsonResponse(list(names), safe=False)


@api_view(['GET'])
def autocomplete_device_type(request):
    """Автодополнение для поля типа прибора"""
    term = request.GET.get('term', '')
    if len(term) < 2:
        return JsonResponse([], safe=False)
    
    device_types = EquipmentRecord.objects.filter(
        device_type__icontains=term
    ).values_list('device_type', flat=True).distinct()[:10]
    
    return JsonResponse(list(device_types), safe=False)


@api_view(['GET'])
def autocomplete_tech_name(request):
    """Автодополнение для поля наименования техники"""
    term = request.GET.get('term', '')
    if len(term) < 2:
        return JsonResponse([], safe=False)
    
    tech_names = EquipmentRecord.objects.filter(
        tech_name__icontains=term
    ).values_list('tech_name', flat=True).distinct()[:10]
    
    return JsonResponse(list(tech_names), safe=False)


@api_view(['GET'])
def autocomplete_notes(request):
    """Автодополнение для поля примечаний"""
    term = request.GET.get('term', '')
    if len(term) < 2:
        return JsonResponse([], safe=False)
    
    notes = EquipmentRecord.objects.filter(
        notes__icontains=term
    ).exclude(notes__isnull=True).exclude(notes='').values_list('notes', flat=True).distinct()[:10]
    
    return JsonResponse(list(notes), safe=False) 