from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model
from django.utils import timezone
from trips.models import BusinessTrip, Organization
from trips.forms import TechnicalStaffRecordForm
from trips.models import TechnicalStaffRecord
from .forms import CustomUserCreationForm
from trips.views_templates import get_current_week_start

User = get_user_model()

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Проверяем существование пользователя
        try:
            user = User.objects.get(username=username)
            if not user.is_active:
                messages.error(request, 'Ваш аккаунт неактивен. Пожалуйста, обратитесь к администратору.')
                return render(request, 'users/login.html')
        except User.DoesNotExist:
            messages.error(request, 'Пользователь с таким именем не существует')
            return render(request, 'users/login.html')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Update last login date
            user.last_login_date = timezone.now()
            user.save()
            
            return redirect('dashboard')
        else:
            messages.error(request, 'Неверный пароль')
    
    return render(request, 'users/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

def register_view(request):
    VALID_CODES = ["knNiQwceyNDXGtY-M50b"]  # Можно вынести в настройки или БД
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data.get("invite_code", "")
            if code not in VALID_CODES:
                form.add_error("invite_code", "Неверный уникальный код!")
            else:
                user = form.save()
                login(request, user)
                return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'users/register.html', {'form': form})

@login_required
def profile_view(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.save()
        
        messages.success(request, 'Профиль успешно обновлен')
        return redirect('profile')
    
    return render(request, 'users/profile.html')

@login_required
@require_http_methods(["POST"])
def change_password(request):
    user = request.user
    old_password = request.POST.get('old_password')
    new_password1 = request.POST.get('new_password1')
    new_password2 = request.POST.get('new_password2')
    
    if not user.check_password(old_password):
        messages.error(request, 'Неверный текущий пароль')
        return redirect('profile')
    
    if new_password1 != new_password2:
        messages.error(request, 'Новые пароли не совпадают')
        return redirect('profile')
    
    user.set_password(new_password1)
    user.save()
    
    # Re-authenticate
    login(request, authenticate(username=user.username, password=new_password1))
    
    messages.success(request, 'Пароль успешно изменен')
    return redirect('profile')

@login_required
def dashboard_view(request):
    user = request.user
    
    # Проверяем, нужно ли перелогиниться
    if hasattr(user, 'should_relogin') and callable(user.should_relogin) and user.should_relogin():
        logout(request)
        messages.warning(request, 'Вы не заходили в систему более 5 дней. Пожалуйста, войдите снова.')
        return redirect('login')
    
    # Get active trip for current user
    active_trip = None
    try:
        trips_as_member = BusinessTrip.objects.filter(members=user, end_date=None).first()
        trips_as_senior = BusinessTrip.objects.filter(senior=user, end_date=None).first()
        
        # Сначала проверяем, является ли пользователь старшим в командировке
        if trips_as_senior:
            active_trip = trips_as_senior
        # Если нет, то проверяем, является ли участником
        elif trips_as_member:
            active_trip = trips_as_member
    except Exception as e:
        # Если возникает ошибка с полем city, временно игнорируем её
        print(f"Ошибка при получении активной командировки: {e}")

    # Get organizations for active trip (filter: незакрытые и с приборами за неделю)
    organizations = []
    tech_staff_by_org = {}
    forms_list = []
    senior_week_stats = None
    if active_trip and hasattr(active_trip, 'organizations'):
        from datetime import timedelta
        from equipment.models import EquipmentRecord
        now = timezone.now()
        week_start = get_current_week_start(now)
        week_end = week_start + timedelta(days=7)
        all_orgs = active_trip.organizations.all()
        organizations = list(all_orgs)  # Показываем все организации (включая закрытые)
        if user == getattr(active_trip, 'senior', None):
            tech_staff_records = TechnicalStaffRecord.objects.filter(organization__in=organizations, created_at__gte=week_start, created_at__lt=week_end)
            tech_staff_by_org = {rec.organization_id: rec for rec in tech_staff_records}
            if request.method == 'POST':
                org_id = request.POST.get('org_id')
                value = request.POST.get('value')
                if org_id and value:
                    org = next((o for o in organizations if str(o.id) == str(org_id)), None)
                    if org and org.id not in tech_staff_by_org:
                        form = TechnicalStaffRecordForm({'organization': org.id, 'value': value})
                        if form.is_valid():
                            rec = form.save(commit=False)
                            rec.user = user
                            rec.week = week_start
                            rec.save()
                            tech_staff_by_org[org.id] = rec
                            messages.success(request, f"Данные по тех. составу для '{org.name}' успешно внесены!")
                            return redirect('dashboard')
                        else:
                            forms_list.append((org, form, True))
            for org in organizations:
                if org.id not in tech_staff_by_org:
                    has_records = EquipmentRecord.objects.filter(
                        organization=org,
                        date_created__gte=week_start,
                        date_created__lt=week_end
                    ).exists()
                    form = TechnicalStaffRecordForm(organization=org)
                    forms_list.append((org, form, has_records))
            from collections import defaultdict
            senior_week_stats = []
            for org in organizations:
                org_stats = {
                    'id': org.id,
                    'name': org.name,
                    'workers': defaultdict(lambda: defaultdict(int)),
                    'details': defaultdict(lambda: defaultdict(list)),
                    'tech_staff': tech_staff_by_org.get(org.id),
                }
                records = EquipmentRecord.objects.filter(
                    organization=org,
                    date_created__gte=week_start,
                    date_created__lt=week_end
                ).select_related('user', 'measurement_type')
                for rec in records:
                    org_stats['workers'][rec.user.get_full_name() or rec.user.username][rec.measurement_type.name] += rec.quantity
                    org_stats['details'][rec.user.get_full_name() or rec.user.username][rec.measurement_type.name].append(rec)
                org_stats['workers'] = {k: dict(v) for k, v in org_stats['workers'].items()}
                org_stats['details'] = {k: dict(v) for k, v in org_stats['details'].items()}
                senior_week_stats.append(org_stats)
    # Get recent equipment records
    recent_records = []
    if hasattr(user, 'equipment_records'):
        recent_records = user.equipment_records.order_by('-date_created')[:5]
    context = {
        'active_trip': active_trip,
        'organizations': organizations,
        'recent_records': recent_records,
        'senior_week_stats': senior_week_stats,
        'forms_list': forms_list,
        'tech_staff_by_org': tech_staff_by_org,
    }
    return render(request, 'dashboard.html', context)

@login_required
def add_user_view(request):
    if not request.user.is_staff:
        messages.error(request, 'У вас нет прав для добавления пользователей')
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Пользователь {user.username} успешно создан')
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'users/add_user.html', {'form': form}) 