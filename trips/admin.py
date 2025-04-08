from django.contrib import admin
from .models import BusinessTrip, Organization

@admin.register(BusinessTrip)
class BusinessTripAdmin(admin.ModelAdmin):
    list_display = ['name', 'senior', 'start_date', 'end_date', 'is_active_display']
    list_filter = ['end_date', 'start_date']
    search_fields = ['name']
    
    def is_active_display(self, obj):
        return obj.is_active()
    
    is_active_display.short_description = 'Активна'
    is_active_display.boolean = True

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['name', 'trip', 'created_date', 'is_closed']
    list_filter = ['is_closed', 'created_date']
    search_fields = ['name']
