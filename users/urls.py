from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, CustomTokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView
from .views_templates import (
    login_view, logout_view, register_view, 
    profile_view, change_password, dashboard_view,
    add_user_view
)

# API routes
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

# Разделяем API и шаблонные URL-маршруты
api_urlpatterns = [
    path('', include(router.urls)),
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair_api'),
]

# URL-маршруты для шаблонов
urlpatterns = [
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('register/', register_view, name='register'),
    path('profile/', profile_view, name='profile'),
    path('change-password/', change_password, name='change_password'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('add-user/', add_user_view, name='add_user'),
] 