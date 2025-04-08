from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class User(AbstractUser):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('occupied', 'Occupied'),
    ]
    
    is_senior = models.BooleanField(default=False)
    last_login_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    
    def should_relogin(self):
        """Check if user should relogin (inactive for more than 5 days)"""
        if self.last_login_date:
            days_inactive = (timezone.now() - self.last_login_date).days
            return days_inactive > 5
        return False
    
    def __str__(self):
        return self.username
