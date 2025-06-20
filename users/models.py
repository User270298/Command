from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class User(AbstractUser):
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )
    
    is_senior = models.BooleanField(default=False)
    last_login_date = models.DateTimeField(default=timezone.now)
    
    def should_relogin(self):
        """Check if user should relogin (inactive for more than 5 days)"""
        if self.last_login_date:
            days_inactive = (timezone.now() - self.last_login_date).days
            return days_inactive > 5
        return False
    
    def __str__(self):
        return self.username
