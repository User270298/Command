from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model
from django.utils import timezone
from trips.models import BusinessTrip
from .forms import CustomUserCreationForm

User = get_user_model()

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Update last login date
            user.last_login_date = timezone.now()
            user.save()
            
            return redirect('dashboard')
        else:
            messages.error(request, 'Неверное имя пользователя или пароль')
    
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
    
    # Get recent equipment records
    recent_records = []
    if hasattr(user, 'equipment_records'):
        recent_records = user.equipment_records.order_by('-date_created')[:5]
    
    context = {
        'active_trip': active_trip,
        'organizations': organizations,
        'recent_records': recent_records
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