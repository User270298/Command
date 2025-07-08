from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, HttpResponse
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone
from django.urls import reverse
import logging
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

from .models import BusinessTrip, Organization
from equipment.models import EquipmentRecord

User = get_user_model()

@login_required
def trip_list_view(request):
    """
    Отображает список командировок пользователя
    """
    trips = BusinessTrip.objects.filter(members=request.user).order_by('-start_date')
    return render(request, 'trips/trip_list.html', {'trips': trips})

@login_required
def trip_detail_view(request, trip_id):
    """
    Отображает детальную информацию о командировке
    """
    trip = get_object_or_404(BusinessTrip, id=trip_id, members=request.user)
    return render(request, 'trips/trip_detail.html', {'trip': trip})

@login_required
def create_trip_view(request):
    """
    Отображает форму для создания новой командировки
    """
    # Получаем всех доступных пользователей
    available_users = BusinessTrip.get_available_users()
    
    if not available_users.exists():
        messages.warning(request, 'В данный момент нет доступных пользователей для командировки. Все пользователи уже участвуют в активных командировках.')
        return redirect('trip_list')
    
    context = {
        'available_users': available_users
    }
    
    return render(request, 'trips/create_trip.html', context)

@login_required
def trip_create_view(request):
    user = request.user
    logger = logging.getLogger(__name__)
    
    # Проверяем, не является ли пользователь уже участником или старшим в активной командировке
    active_trips = BusinessTrip.objects.filter(
        Q(senior=user) | Q(members=user),
        end_date__isnull=True
    )
    
    if active_trips.exists():
        messages.error(request, 'Вы уже участвуете в активной командировке')
        return redirect('trip_list')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        city = request.POST.get('city')
        member_ids = request.POST.getlist('members')
        org_names = request.POST.getlist('org_names[]')
        
        if not name or not city:
            messages.error(request, 'Пожалуйста, заполните все обязательные поля')
            return redirect('trip_create')
        
        # Проверяем, что количество участников не превышает 3 (не считая старшего)
        if len(member_ids) > 3:
            messages.error(request, 'Максимальное количество участников в командировке - 4 человека (включая старшего)')
            return redirect('trip_create')
        
        # Проверяем, что есть хотя бы одна организация
        if not org_names or not any(org_name.strip() for org_name in org_names):
            messages.error(request, 'Пожалуйста, укажите хотя бы одну организацию')
            return redirect('trip_create')
        
        try:
            # Создаем командировку
            trip = BusinessTrip.objects.create(
                name=name,
                city=city,
                senior=user
            )
            
            # Добавляем организации
            for org_name in org_names:
                if org_name.strip():  # Проверяем, что название не пустое
                    Organization.objects.create(
                        name=org_name.strip(),
                        trip=trip
                    )
            
            # Добавляем участников
            for member_id in member_ids:
                try:
                    member = User.objects.get(id=member_id)
                    # Проверяем, что участник не в активной командировке
                    if not BusinessTrip.objects.filter(
                        Q(senior=member) | Q(members=member),
                        end_date__isnull=True
                    ).exists():
                        trip.members.add(member)
                    else:
                        messages.warning(
                            request,
                            f'Пользователь {member.get_full_name() or member.username} уже участвует в другой командировке'
                        )
                except User.DoesNotExist:
                    messages.warning(request, f'Пользователь с ID {member_id} не найден')
            
            # Добавляем старшего как участника
            trip.members.add(user)
            
            messages.success(request, 'Командировка успешно создана')
            return redirect('trip_detail', trip_id=trip.id)
            
        except Exception as e:
            messages.error(request, f'Ошибка при создании командировки: {str(e)}')
            return redirect('trip_create')
    
    # Получаем доступных пользователей для выбора
    available_users = BusinessTrip.get_available_users(exclude_user=user)
    logger.debug(f"Доступных пользователей в представлении: {available_users.count()}")
    
    # Проверяем, есть ли вообще пользователи в системе
    all_users = User.objects.all()
    logger.debug(f"Всего пользователей в системе: {all_users.count()}")
    
    # Если нет доступных пользователей, но есть пользователи в системе,
    # показываем форму без выбора участников
    if not available_users.exists() and all_users.exists():
        logger.debug("Нет доступных пользователей, но есть пользователи в системе")
        context = {
            'available_users': User.objects.exclude(id=user.id),
            'user': user,
            'no_available_users': True
        }
    else:
        context = {
            'available_users': available_users,
            'user': user,
            'no_available_users': False
        }
    
    return render(request, 'trips/trip_create.html', context)

@login_required
def close_trip(request, pk):
    trip = get_object_or_404(BusinessTrip, id=pk)
    
    # Проверяем, что пользователь является старшим в этой командировке
    if request.user != trip.senior:
        messages.error(request, "Только старший командировки может завершить её")
        return redirect('trip_list')
    
    # Проверяем, что командировка активна
    if trip.end_date is not None:
        messages.warning(request, "Эта командировка уже завершена")
        return redirect('trip_list')
    
    # Завершаем командировку, устанавливая дату окончания
    trip.end_date = timezone.now().date()
    trip.save()
    
    messages.success(request, f"Командировка '{trip.name}' успешно завершена")
    return redirect('trip_list')

@login_required
def organization_detail_view(request, org_id):
    user = request.user
    organization = get_object_or_404(Organization, id=org_id)
    trip = organization.trip
    if not (user == trip.senior or user in trip.members.all()):
        return HttpResponseForbidden("Вы не имеете доступа к этой организации")

    # Показываем только записи для этой организации
    if user == trip.senior:
        equipment_records = organization.equipment_records.select_related('measurement_type', 'user', 'organization')
    else:
        equipment_records = organization.equipment_records.filter(user=user).select_related('measurement_type')

    # Статистика по типам измерений
    measurement_stats = equipment_records.values('measurement_type__name').distinct()

    is_senior = user == trip.senior
    return render(request, 'trips/organization_detail.html', {
        'organization': organization,
        'equipment_records': equipment_records,
        'measurement_stats': measurement_stats,
        'is_senior': is_senior,
    })

@login_required
def organization_create_view(request):
    user = request.user
    selected_trip_id = request.GET.get('trip')
    selected_trip = None
    
    if selected_trip_id:
        try:
            selected_trip = BusinessTrip.objects.get(id=selected_trip_id)
            # Check if user is the senior
            if user != selected_trip.senior:
                messages.error(request, 'Только старший группы может добавлять организации')
                return redirect('trip_detail', trip_id=selected_trip.id)
        except BusinessTrip.DoesNotExist:
            pass
    
    if request.method == 'POST':
        name = request.POST.get('name')
        trip_id = request.POST.get('trip')
        
        if not name or not trip_id:
            messages.error(request, 'Пожалуйста, заполните все поля')
            return redirect('organization_create')
        
        try:
            trip = BusinessTrip.objects.get(id=trip_id)
            
            # Only senior can add organizations
            if user != trip.senior:
                messages.error(request, 'Только старший группы может добавлять организации')
                return redirect('trip_detail', trip_id=trip.id)
            
            # Create organization
            organization = Organization.objects.create(
                name=name,
                trip=trip
            )
            
            messages.success(request, 'Организация успешно добавлена')
            return redirect('organization_detail', org_id=organization.id)
            
        except BusinessTrip.DoesNotExist:
            messages.error(request, 'Командировка не найдена')
            return redirect('trip_list')
    
    # Get active trips where user is senior
    trips = BusinessTrip.objects.filter(senior=user, end_date=None)
    
    context = {
        'trips': trips,
        'selected_trip': selected_trip
    }
    
    return render(request, 'trips/organization_create.html', context)

@login_required
def close_organization_view(request, org_id):
    user = request.user
    organization = get_object_or_404(Organization, id=org_id)
    
    # Only the trip's senior can close an organization
    if user != organization.trip.senior:
        return HttpResponseForbidden("Только старший группы может закрыть организацию")
    
    if request.method == 'POST':
        # This will create an Excel report and mark the organization as closed
        
        # Отметить организацию как закрытую
        organization.is_closed = True
        organization.save()
        
        messages.success(request, 'Организация успешно закрыта')
        
        # Перенаправить на страницу деталей командировки
        return redirect('trip_detail', trip_id=organization.trip.id)
    
    return redirect('organization_detail', org_id=organization.id)

@login_required
def generate_weekly_report(request, org_id):
    user = request.user
    organization = get_object_or_404(Organization, id=org_id)
    
    # Check if user is the senior of the organization's trip
    if user != organization.trip.senior:
        return HttpResponseForbidden("Только старший группы может выгружать отчеты")
    
    # Get records from the current week (Monday to Sunday)
    today = timezone.now().date()
    monday = today - timezone.timedelta(days=today.weekday())
    sunday = monday + timezone.timedelta(days=6)
    
    records = organization.equipment_records.filter(
        date_created__date__gte=monday,
        date_created__date__lte=sunday
    ).select_related('measurement_type', 'user')
    
    # Group records by user and measurement type
    report_data = {}
    for record in records:
        user_name = record.user.get_full_name() or record.user.username
        if user_name not in report_data:
            report_data[user_name] = {}
        if record.measurement_type.name not in report_data[user_name]:
            report_data[user_name][record.measurement_type.name] = 0
        report_data[user_name][record.measurement_type.name] += record.quantity
    
    # Create Word document
    doc = Document()
    
    # Set default font
    style = doc.styles['Normal']
    style.font.name = 'Times New Roman'
    style.font.size = Pt(10)
    
    doc.add_heading(f'Отчет по организации {organization.name} за неделю', 0)
    doc.add_paragraph(f'Период: с {monday.strftime("%d.%m.%Y")} по {sunday.strftime("%d.%m.%Y")}')
    
    # Add user statistics
    for user_name, measurements in report_data.items():
        doc.add_paragraph(f'Работник (поверитель): {user_name}')
        for measurement_type, count in measurements.items():
            doc.add_paragraph(f'{count} СИ {measurement_type}', style='List Bullet')
        doc.add_paragraph()  # Add empty line between users
    
    # Save the document
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    response['Content-Disposition'] = f'attachment; filename=weekly_report_{organization.name}.docx'
    doc.save(response)
    return response

@login_required
def complete_organization(request, org_id):
    user = request.user
    organization = get_object_or_404(Organization, id=org_id)
    
    # Check if user is the senior of the organization's trip
    if user != organization.trip.senior:
        return HttpResponseForbidden("Только старший группы может завершать организации")
    
    if request.method == 'POST':
        # Get all records for this organization
        records = organization.equipment_records.all().select_related('measurement_type', 'user')
        
        # Create Word document
        doc = Document()
        
        # Set default font for entire document
        style = doc.styles['Normal']
        style.font.name = 'Times New Roman'
        style.font.size = Pt(10)
        
        # Add title and header
        title = doc.add_paragraph()
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title_run = title.add_run('ЭТАЛОНЫ (СИ), АТТЕСТОВАННЫЕ (ПОВЕРЕННЫЕ) СОГЛАСНО ПЛАНА-ГРАФИКА\nПРЕДСТАВЛЕНИЯ ВОИНСКИМИ ЧАСТЯМИ (ПОДРАЗДЕЛЕНИЯМИ) НА АТТЕСТАЦИЮ\nЭТАЛОНОВ (ПОВЕРКУ СИ) В ПЛАНИРУЕМОМ ГОДУ')
        title_run.font.name = 'Times New Roman'
        title_run.font.size = Pt(10)
        title_run.bold = True
        
        # Add table header
        table = doc.add_table(rows=1, cols=9)
        table.style = 'Table Grid'
        
        # Set table header
        header_cells = table.rows[0].cells
        headers = ['№ п/п', 'Наименование', 'Тип', 'Заводской номер', 'Количество', 
                  'Результат аттестации (поверки)', 'Дата выполнения аттестации (поверки)',
                  'Тип ВВСТ, в состав которого входит эталон (СИ)',
                  'Примечание (номер извещения о непригодности к применению (свидетельства об аттестации (о поверке))']
        
        for i, header in enumerate(headers):
            cell = header_cells[i]
            cell.text = header
            cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = cell.paragraphs[0].runs[0]
            run.font.name = 'Times New Roman'
            run.font.size = Pt(10)
            run.bold = True
        
        # Group records by measurement type
        measurement_groups = {}
        for record in records:
            if record.measurement_type.name not in measurement_groups:
                measurement_groups[record.measurement_type.name] = []
            measurement_groups[record.measurement_type.name].append(record)
        
        # Add records
        row_num = 1
        for measurement_type, records in measurement_groups.items():
            # Add measurement type header
            row_cells = table.add_row().cells
            row_cells[0].text = f'Средства измерений {measurement_type}'
            row_cells[0].merge(row_cells[8])  # Merge all cells in the row
            cell = row_cells[0]
            cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = cell.paragraphs[0].runs[0]
            run.font.name = 'Times New Roman'
            run.font.size = Pt(10)
            run.bold = True
            
            # Add records for this measurement type
            for record in records:
                row_cells = table.add_row().cells
                row_cells[0].text = str(row_num)
                row_cells[1].text = record.name
                row_cells[2].text = record.device_type
                row_cells[3].text = record.serial_number or ''
                row_cells[4].text = str(record.quantity)
                row_cells[5].text = record.status
                row_cells[6].text = f'С {timezone.now().strftime("%d.%m.%Y")} по {(timezone.now() + timezone.timedelta(days=365)).strftime("%d.%m.%Y")}'
                row_cells[7].text = record.tech_name
                row_cells[8].text = record.notes or ''
                
                # Center align all cells and set font
                for cell in row_cells:
                    cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
                    for run in cell.paragraphs[0].runs:
                        run.font.name = 'Times New Roman'
                        run.font.size = Pt(10)
                
                row_num += 1
        
        # Save the document
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        response['Content-Disposition'] = f'attachment; filename=final_report_{organization.name}.docx'
        doc.save(response)
        
        # Mark organization as closed
        organization.is_closed = True
        organization.save()
        
        return response
    
    return HttpResponseForbidden("Invalid request method") 