from django.db import models
from django.conf import settings
from django.db.models import Q
from django.contrib.auth import get_user_model
import logging
# from equipment.models import EquipmentRecord  # Удаляем прямой импорт

logger = logging.getLogger(__name__)

class BusinessTrip(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название")
    senior = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='led_trips', verbose_name="Старший")
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='trips', verbose_name="Участники")
    start_date = models.DateField(auto_now_add=True, verbose_name="Дата начала")
    end_date = models.DateField(null=True, blank=True, verbose_name="Дата окончания")
    city = models.CharField(max_length=100, verbose_name="Город", default="")
    
    def is_active(self):
        """Командировка считается активной, если нет даты окончания"""
        return self.end_date is None
    
    @classmethod
    def get_available_users(cls, exclude_user=None):
        """Получить пользователей, доступных для командировки (is_active=True, isAdmin=False, не в активной командировке)"""
        User = get_user_model()
        available_users = User.objects.filter(is_active=True, isAdmin=False)
        # Исключаем пользователей, которые уже участвуют в активных командировках
        active_trips = cls.objects.filter(end_date__isnull=True)
        busy_user_ids = set()
        for trip in active_trips:
            busy_user_ids.add(trip.senior_id)
            busy_user_ids.update(trip.members.values_list('id', flat=True))
        if busy_user_ids:
            available_users = available_users.exclude(id__in=busy_user_ids)
        if exclude_user:
            available_users = available_users.exclude(id=exclude_user.id)
        return available_users
    
    def save(self, *args, **kwargs):
        """Обновляем статусы пользователей при сохранении командировки"""
        if self.end_date:
            # Если командировка завершена, обновляем статусы всех участников на 'active'
            for member in self.members.all():
                member.status = 'active'
                member.save()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.name} - {self.start_date}"
    
    class Meta:
        ordering = ['-start_date']
        verbose_name = "Командировка"
        verbose_name_plural = "Командировки"

class Organization(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название")
    trip = models.ForeignKey(BusinessTrip, on_delete=models.CASCADE, related_name='organizations', verbose_name="Командировка")
    created_date = models.DateField(auto_now_add=True, verbose_name="Дата создания")
    is_closed = models.BooleanField(default=False, verbose_name="Закрыта")
    last_fixed_at = models.DateTimeField(null=True, blank=True, verbose_name="Время последней фиксации")
    fixed_until = models.DateTimeField(null=True, blank=True, verbose_name="Показывать фиксированные данные админу до")
    fixed_records = models.ManyToManyField('equipment.EquipmentRecord', blank=True, related_name='fixed_organizations', verbose_name="Зафиксированные записи")
    tech_staff_count = models.IntegerField(default=0, verbose_name="Тех состав (текущее значение)")
    tech_staff_fixed = models.IntegerField(null=True, blank=True, verbose_name="Тех состав (зафиксированное значение)")
    
    def __str__(self):
        return f"{self.name} - {self.trip.name}"
    
    class Meta:
        ordering = ['-created_date']
        verbose_name = "Организация"
        verbose_name_plural = "Организации"
