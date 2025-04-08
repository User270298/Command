from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, HttpResponse
from django.utils import timezone
from django.db.models import Count, Q
import csv
import io

from .models import MeasurementType, EquipmentRecord
from trips.models import Organization, BusinessTrip

@login_required
def measurement_type_list_view(request):
    measurement_types = MeasurementType.objects.all().annotate(
        records_count=Count('equipment_records')
    )
    
    context = {
        'measurement_types': measurement_types
    }
    
    return render(request, 'equipment/measurement_type_list.html', context)

@login_required
def equipment_record_create_view(request):
    user = request.user
    organization_id = request.GET.get('organization')
    organization = None
    
    if organization_id:
        try:
            organization = Organization.objects.get(id=organization_id)
            # Check if user is a member of this organization's trip
            if not (user == organization.trip.senior or user in organization.trip.members.all()):
                messages.error(request, 'У вас нет доступа к этой организации')
                return redirect('trip_list')
            
            if organization.is_closed:
                messages.error(request, 'Организация закрыта, невозможно добавить новые записи')
                return redirect('organization_detail', org_id=organization.id)
        except Organization.DoesNotExist:
            pass
    
    if request.method == 'POST':
        measurement_type_id = request.POST.get('measurement_type')
        organization_id = request.POST.get('organization')
        value = request.POST.get('value')
        notes = request.POST.get('notes', '')
        
        if not all([measurement_type_id, organization_id, value]):
            messages.error(request, 'Пожалуйста, заполните все обязательные поля')
            return redirect('equipment_record_create')
        
        try:
            measurement_type = MeasurementType.objects.get(id=measurement_type_id)
            organization = Organization.objects.get(id=organization_id)
            
            # Check if user is a member of this organization's trip
            if not (user == organization.trip.senior or user in organization.trip.members.all()):
                messages.error(request, 'У вас нет доступа к этой организации')
                return redirect('trip_list')
            
            if organization.is_closed:
                messages.error(request, 'Организация закрыта, невозможно добавить новые записи')
                return redirect('organization_detail', org_id=organization.id)
            
            # Create equipment record
            EquipmentRecord.objects.create(
                measurement_type=measurement_type,
                organization=organization,
                user=user,
                value=value,
                notes=notes
            )
            
            messages.success(request, 'Запись об оборудовании успешно создана')
            return redirect('organization_detail', org_id=organization.id)
            
        except (MeasurementType.DoesNotExist, Organization.DoesNotExist):
            messages.error(request, 'Ошибка при создании записи')
            return redirect('equipment_record_create')
    
    # Get active organizations where user is a member
    # Получение всех поездок, в которых пользователь является участником или старшим
    trips_as_member = BusinessTrip.objects.filter(
        Q(members=user) | Q(senior=user),
        end_date=None  # Активные командировки не имеют даты окончания
    ).distinct()
    
    active_organizations = Organization.objects.filter(
        trip__in=trips_as_member,
        is_closed=False
    )
    
    # Get all measurement types
    measurement_types = MeasurementType.objects.all()
    
    context = {
        'active_organizations': active_organizations,
        'measurement_types': measurement_types,
        'selected_organization': organization
    }
    
    return render(request, 'equipment/equipment_record_create.html', context)

@login_required
def my_records_view(request):
    user = request.user
    
    # Get all records created by the user
    records = EquipmentRecord.objects.filter(user=user).select_related(
        'measurement_type', 'organization', 'organization__trip'
    ).order_by('-date_created')
    
    # Filter by date (last day, last week, last month, all time)
    timeframe = request.GET.get('timeframe', 'all')
    now = timezone.now()
    
    if timeframe == 'day':
        start_date = now - timezone.timedelta(days=1)
        records = records.filter(date_created__gte=start_date)
    elif timeframe == 'week':
        start_date = now - timezone.timedelta(days=7)
        records = records.filter(date_created__gte=start_date)
    elif timeframe == 'month':
        start_date = now - timezone.timedelta(days=30)
        records = records.filter(date_created__gte=start_date)
    
    # Statistics
    record_count = records.count()
    measurement_type_counts = records.values('measurement_type__name').annotate(
        count=Count('id')
    ).order_by('-count')
    
    context = {
        'records': records,
        'record_count': record_count,
        'measurement_type_counts': measurement_type_counts,
        'selected_timeframe': timeframe
    }
    
    return render(request, 'equipment/my_records.html', context)

@login_required
def export_csv_view(request):
    user = request.user
    timeframe = request.GET.get('timeframe', 'all')
    
    # Get all records created by the user
    records = EquipmentRecord.objects.filter(user=user).select_related(
        'measurement_type', 'organization', 'organization__trip'
    ).order_by('-date_created')
    
    # Filter by date (last day, last week, last month, all time)
    now = timezone.now()
    
    if timeframe == 'day':
        start_date = now - timezone.timedelta(days=1)
        records = records.filter(date_created__gte=start_date)
    elif timeframe == 'week':
        start_date = now - timezone.timedelta(days=7)
        records = records.filter(date_created__gte=start_date)
    elif timeframe == 'month':
        start_date = now - timezone.timedelta(days=30)
        records = records.filter(date_created__gte=start_date)
    
    # Create CSV response
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    
    # Write header
    writer.writerow([
        'Дата создания', 
        'Тип измерения',
        'Значение',
        'Организация',
        'Командировка', 
        'Заметки'
    ])
    
    # Write data
    for record in records:
        writer.writerow([
            record.date_created.strftime('%Y-%m-%d %H:%M'),
            record.measurement_type.name,
            record.name,
            record.organization.name,
            record.organization.trip.name,
            record.notes
        ])
    
    # Create response
    response = HttpResponse(buffer.getvalue(), content_type='text/csv')
    filename = f'my_records_{timezone.now().strftime("%Y%m%d_%H%M")}.csv'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response

@login_required
def measurement_type_create_view(request):
    # Only admins can create measurement types
    if not request.user.is_staff:
        messages.error(request, 'Только администраторы могут создавать типы измерений')
        return redirect('measurement_type_list')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        unit = request.POST.get('unit')
        
        if not name or not unit:
            messages.error(request, 'Пожалуйста, заполните все поля')
            return redirect('measurement_type_create')
        
        # Create measurement type
        MeasurementType.objects.create(
            name=name,
            unit=unit
        )
        
        messages.success(request, 'Тип измерения успешно создан')
        return redirect('measurement_type_list')
    
    return render(request, 'equipment/measurement_type_create.html')

@login_required
def search_records_view(request):
    user = request.user
    query = request.GET.get('q', '')
    
    if query:
        # Search in records (notes, measurement type name, organization name)
        records = EquipmentRecord.objects.filter(
            Q(notes__icontains=query) |
            Q(measurement_type__name__icontains=query) |
            Q(organization__name__icontains=query) |
            Q(organization__trip__name__icontains=query)
        ).select_related('measurement_type', 'organization', 'organization__trip', 'user')
        
        # Only show records from trips where user is a member
        user_trips = BusinessTrip.objects.filter(
            Q(members=user) | Q(senior=user)
        ).distinct()
        
        records = records.filter(
            Q(organization__trip__in=user_trips) |
            Q(user=user)  # User can always see their own records
        ).distinct()
    else:
        records = EquipmentRecord.objects.none()
    
    context = {
        'records': records,
        'query': query,
        'record_count': records.count()
    }
    
    return render(request, 'equipment/search_records.html', context)

@login_required
def clear_equipment_records(request, org_id):
    organization = get_object_or_404(Organization, id=org_id)
    
    # Check if user has permission
    if not (request.user == organization.trip.senior or request.user in organization.trip.members.all()):
        messages.error(request, 'У вас нет прав для очистки записей')
        return redirect('organization_detail', org_id=org_id)
    
    if request.method == 'POST':
        # Delete all equipment records for this organization
        organization.equipment_records.all().delete()
        messages.success(request, 'Все записи об оборудовании успешно удалены')
        return redirect('organization_detail', org_id=org_id)
    
    return render(request, 'equipment/clear_records_confirm.html', {'organization': organization}) 