from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),
    path('trips/', include('trips.urls')),
    path('equipment/', include('equipment.urls')),
    path('', RedirectView.as_view(url='users/dashboard/', permanent=False)),
] 