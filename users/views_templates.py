from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model
from django.utils import timezone
from trips.models import BusinessTrip
from .forms import CustomUserCreationForm
from django.contrib.auth.decorators import user_passes_test

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
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
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
    
    # Get organizations for active trip
    organizations = []
    if active_trip and hasattr(active_trip, 'organizations'):
        organizations = active_trip.organizations.all()

    # --- Новый блок: статистика для старшего как в admin_stats ---
    senior_trip_stats = None
    if user == getattr(active_trip, 'senior', None) and organizations:
        from collections import defaultdict
        from equipment.models import EquipmentRecord
        from datetime import timedelta
        now = timezone.now()
        senior_trip_stats = []
        trip = active_trip
        trip_info = {
            'name': trip.name,
            'city': trip.city,
            'senior': trip.senior,
            'organizations': [],
        }
        for org in organizations:
            org_info = {
                'id': org.id,
                'name': org.name,
                'workers': defaultdict(lambda: defaultdict(int)),
                'records': [],
                'last_fixed_at': org.last_fixed_at,
            }
            # Только новые записи после последней фиксации
            if org.last_fixed_at:
                records = org.equipment_records.filter(date_created__gt=org.last_fixed_at).select_related('user', 'measurement_type')
            else:
                records = org.equipment_records.all().select_related('user', 'measurement_type')
            for rec in records:
                org_info['workers'][rec.user.get_full_name() or rec.user.username][rec.measurement_type.name] += rec.quantity
                org_info['records'].append(rec)
            org_info['workers'] = {k: dict(v) for k, v in org_info['workers'].items()}
            trip_info['organizations'].append(org_info)
        senior_trip_stats.append(trip_info)

    # Статистика за неделю для старшего группы
    senior_week_stats = None
    if user == getattr(active_trip, 'senior', None) and organizations:
        from collections import defaultdict
        from equipment.models import EquipmentRecord
        from datetime import timedelta
        now = timezone.now()
        monday = now - timedelta(days=now.weekday())
        monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)
        sunday = monday + timedelta(days=6, hours=23, minutes=59, seconds=59)
        senior_week_stats = []
        for org in organizations:
            org_stats = {
                'id': org.id,
                'name': org.name,
                'workers': defaultdict(lambda: defaultdict(int)),  # {user: {measurement_type: count}}
                'details': defaultdict(lambda: defaultdict(list)),  # {user: {measurement_type: [EquipmentRecord, ...]}}
            }
            records = EquipmentRecord.objects.filter(
                organization=org,
                date_created__gte=monday,
                date_created__lte=sunday
            ).select_related('user', 'measurement_type')
            for rec in records:
                org_stats['workers'][rec.user.get_full_name() or rec.user.username][rec.measurement_type.name] += rec.quantity
                org_stats['details'][rec.user.get_full_name() or rec.user.username][rec.measurement_type.name].append(rec)
            # Преобразуем defaultdict в dict для шаблона
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
        'senior_trip_stats': senior_trip_stats,
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

@user_passes_test(lambda u: u.is_authenticated and getattr(u, 'isAdmin', False))
def admin_stats_view(request):
    from collections import defaultdict
    from equipment.models import EquipmentRecord, MeasurementType
    from trips.models import BusinessTrip, Organization
    from django.contrib.auth import get_user_model
    from django.utils import timezone
    from datetime import timedelta

    trips = BusinessTrip.objects.prefetch_related('organizations', 'organizations__equipment_records', 'members', 'senior')
    trip_stats = []
    now = timezone.now()
    for trip in trips:
        trip_info = {
            'name': trip.name,
            'city': trip.city,
            'senior': trip.senior,
            'organizations': [],
        }
        for org in trip.organizations.all():
            # Принудительно обновим объект из базы
            org_db = Organization.objects.get(pk=org.pk)
            print('org.id:', org_db.id, 'tech_staff_fixed:', org_db.tech_staff_fixed)
            org_info = {
                'id': org.id,
                'name': org.name,
                'workers': defaultdict(lambda: defaultdict(int)),
                'records': [],
                'tech_staff_fixed': org_db.tech_staff_fixed,
                'fixed_until': org.fixed_until,
            }
            if org.last_fixed_at and org.fixed_until and now < org.fixed_until:
                records = org.fixed_records.all().select_related('user', 'measurement_type')
            elif org.last_fixed_at and org.fixed_until and now >= org.fixed_until:
                records = org.equipment_records.filter(date_created__gt=org.last_fixed_at).select_related('user', 'measurement_type')
            else:
                records = org.equipment_records.all().select_related('user', 'measurement_type')
            for rec in records:
                org_info['workers'][rec.user.get_full_name() or rec.user.username][rec.measurement_type.name] += rec.quantity
                org_info['records'].append(rec)
            org_info['workers'] = {k: dict(v) for k, v in org_info['workers'].items()}
            trip_info['organizations'].append(org_info)
        trip_stats.append(trip_info)
    return render(request, 'admin_stats.html', {
        'trip_stats': trip_stats,
        'now': now,
    }) 