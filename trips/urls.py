from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import BusinessTripViewSet, OrganizationViewSet
from .views_templates import (
    trip_list_view, trip_detail_view, trip_create_view, close_trip,
    organization_detail_view, organization_create_view, close_organization_view
)

# API routes
router = DefaultRouter()
router.register(r'trips', BusinessTripViewSet, basename='trip-api')
router.register(r'organizations', OrganizationViewSet, basename='organization-api')

# Разделяем API и шаблонные URL-маршруты
api_urlpatterns = [
    path('', include(router.urls)),
]

# URL-маршруты для шаблонов
urlpatterns = [
    path('', trip_list_view, name='trip_list'),
    path('<int:trip_id>/', trip_detail_view, name='trip_detail'),
    path('create/', trip_create_view, name='trip_create'),
    path('<int:pk>/close/', close_trip, name='close_trip'),
    
    # Organization views
    path('organization/<int:org_id>/', organization_detail_view, name='organization_detail'),
    path('organization/create/', organization_create_view, name='organization_create'),
    path('organization/<int:org_id>/close/', close_organization_view, name='close_organization'),
] 