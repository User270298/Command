"""
URL configuration for equipment_tracking project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

# Импортируем разделенные URL-маршруты
from equipment.urls import api_urlpatterns as equipment_api_urls, urlpatterns as equipment_urls
from trips.urls import api_urlpatterns as trips_api_urls, urlpatterns as trips_urls
from users.urls import api_urlpatterns as users_api_urls, urlpatterns as users_urls

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API маршруты
    path('api/users/', include(users_api_urls)),
    path('api/trips/', include(trips_api_urls)),
    path('api/equipment/', include(equipment_api_urls)),
    
    # Маршруты шаблонов
    path('users/', include(users_urls)),
    path('trips/', include(trips_urls)),
    path('equipment/', include(equipment_urls)),
    path('', RedirectView.as_view(url='users/dashboard/', permanent=False)),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
