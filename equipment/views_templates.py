from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, HttpResponse, JsonResponse
from django.utils import timezone
from django.db.models import Count, Q
from django.urls import reverse
import csv
import io

from .models import MeasurementType, EquipmentRecord
from trips.models import Organization, BusinessTrip
from .forms import EquipmentRecordForm

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
    organization = None
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    form = EquipmentRecordForm()
    
    def json_response(success, error=None, redirect_url=None, details=None):
        if is_ajax:
            response_data = {'success': success}
            if error:
                response_data['error'] = error
            if redirect_url:
                response_data['redirect_url'] = redirect_url
            if details:
                response_data['details'] = details
            return JsonResponse(response_data)
        else:
            if error:
                messages.error(request, error)
            elif success:
                messages.success(request, 'Записи об оборудовании успешно созданы')
            return redirect(redirect_url or 'equipment_record_create')
    
    # Get organization from URL if provided
    org_id = request.GET.get('organization')
    if org_id:
        try:
            organization = Organization.objects.get(id=org_id)
        except Organization.DoesNotExist:
            return json_response(False, 'Организация не найдена')
    
    if request.method == 'POST':
        try:
            # Check if this is a duplicate submission
            if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
                return json_response(False, 'Invalid request type')
            
            # Get organization
            organization_id = request.POST.get('organization')
            if not organization_id:
                return json_response(False, 'Пожалуйста, выберите организацию')
            
            try:
                organization = Organization.objects.get(id=organization_id)
            except Organization.DoesNotExist:
                return json_response(False, 'Организация не найдена')
            
            # Check if user is a member of this organization's trip
            if not (user == organization.trip.senior or user in organization.trip.members.all()):
                return json_response(False, 'У вас нет доступа к этой организации')
            
            if organization.is_closed:
                return json_response(False, 'Организация закрыта, невозможно добавить новые записи')
            
            # Get number of equipment fields
            try:
                num_fields = int(request.POST.get('equipment-fields', 0))
            except (TypeError, ValueError):
                return json_response(False, 'Неверное количество полей оборудования')
            
            if num_fields < 1:
                return json_response(False, 'Не найдены поля оборудования')
            
            created_records = []
            for i in range(1, num_fields + 1):
                measurement_type_id = request.POST.get(f'measurement_type_{i}')
                name = request.POST.get(f'name_{i}')
                device_type = request.POST.get(f'device_type_{i}')
                serial_number = request.POST.get(f'serial_number_{i}')
                quantity = request.POST.get(f'quantity_{i}')
                tech_name = request.POST.get(f'tech_name_{i}')
                notes = request.POST.get(f'notes_{i}')
                
                if not all([measurement_type_id, name, device_type, quantity, tech_name]):
                    missing_fields = []
                    if not measurement_type_id: missing_fields.append('тип измерения')
                    if not name: missing_fields.append('наименование')
                    if not device_type: missing_fields.append('тип прибора')
                    if not quantity: missing_fields.append('количество')
                    if not tech_name: missing_fields.append('наименование техники')
                    
                    error_message = f'Пожалуйста, заполните все обязательные поля для прибора {i}: {", ".join(missing_fields)}'
                    return json_response(False, error_message)
                
                try:
                    measurement_type = MeasurementType.objects.get(id=measurement_type_id)
                except MeasurementType.DoesNotExist:
                    return json_response(False, f'Тип измерения с ID {measurement_type_id} не найден')
                
                # Check for duplicate record
                duplicate = EquipmentRecord.objects.filter(
                    organization=organization,
                    measurement_type=measurement_type,
                    name=name,
                    device_type=device_type,
                    serial_number=serial_number,
                    tech_name=tech_name
                ).exists()
                
                if duplicate:
                    return json_response(False, f'Запись с такими параметрами уже существует для прибора {i}')
                
                try:
                    # Create equipment record
                    record = EquipmentRecord.objects.create(
                        measurement_type=measurement_type,
                        organization=organization,
                        user=user,
                        name=name,
                        device_type=device_type,
                        serial_number=serial_number,
                        quantity=quantity,
                        tech_name=tech_name,
                        notes=notes
                    )
                    created_records.append(record)
                except Exception as e:
                    import traceback
                    return json_response(False, f'Ошибка при создании записи для прибора {i}: {str(e)}', details=traceback.format_exc())
            
            if not created_records:
                return json_response(False, 'Не удалось создать записи об оборудовании')
            
            return json_response(True, redirect_url=reverse('organization_detail', args=[organization.id]))
            
        except Exception as e:
            import traceback
            return json_response(False, f'Произошла ошибка при сохранении: {str(e)}', details=traceback.format_exc())
    
    # Get active organizations where user is a member
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
        'selected_organization': organization,
        'form': form,
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