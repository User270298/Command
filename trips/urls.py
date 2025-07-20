from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import BusinessTripViewSet, OrganizationViewSet
from .views_templates import (
    trip_list_view, trip_detail_view, trip_create_view, close_trip,
    organization_detail_view, organization_create_view, close_organization_view,
    generate_weekly_report, complete_organization, admin_stats_view, tech_staff_entry_view,
    download_organization_list, download_plan_assignment_excel
)

# API routes
router = DefaultRouter()
router.register(r'trips', BusinessTripViewSet, basename='trip-api')
router.register(r'organizations', OrganizationViewSet, basename='organization-api')

# Разделяем API и шаблонные URL-маршруты
api_urlpatterns = [
    path('', include(router.urls)),
]

# URL-маршруты для организаций
organization_urlpatterns = [
    path('<int:org_id>/', organization_detail_view, name='organization_detail'),
    path('create/', organization_create_view, name='organization_create'),
    path('<int:org_id>/close/', close_organization_view, name='close_organization'),
    path('<int:org_id>/weekly-report/', generate_weekly_report, name='generate_weekly_report'),
    path('<int:org_id>/complete/', complete_organization, name='complete_organization'),
    path('<int:org_id>/download-list/', download_organization_list, name='download_organization_list'),
    path('<int:org_id>/download-plan-assignment/', download_plan_assignment_excel, name='download_plan_assignment_excel'),
]

# URL-маршруты для командировок
urlpatterns = [
    path('', trip_list_view, name='trip_list'),
    path('<int:trip_id>/', trip_detail_view, name='trip_detail'),
    path('create/', trip_create_view, name='trip_create'),
    path('<int:pk>/close/', close_trip, name='close_trip'),
    path('organizations/', include(organization_urlpatterns)),
    path('admin-stats/', admin_stats_view, name='admin_stats'),
    path('tech-staff-entry/', tech_staff_entry_view, name='tech_staff_entry'),
] 