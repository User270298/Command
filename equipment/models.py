from django.db import models
from django.conf import settings
from trips.models import Organization

# Create your models here.

class MeasurementType(models.Model):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class EquipmentRecord(models.Model):
    STATUS_CHOICES = [
        ('годен', 'Годен'),
        ('брак', 'Брак'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='equipment_records')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='equipment_records')
    measurement_type = models.ForeignKey(MeasurementType, on_delete=models.CASCADE, related_name='equipment_records')
    name = models.CharField(max_length=255)
    device_type = models.CharField(max_length=255)
    serial_number = models.CharField(max_length=255, blank=True, null=True)
    quantity = models.PositiveIntegerField(default=1)
    tech_name = models.CharField(max_length=255)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='годен')
    notes = models.TextField(blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.organization.name}"
    
    class Meta:
        ordering = ['-date_created']
