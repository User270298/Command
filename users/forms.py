from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import User

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True, max_length=30)
    last_name = forms.CharField(required=True, max_length=30)
    is_senior = forms.BooleanField(required=False, label='Старший группы')
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'is_senior', 'password1', 'password2')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Добавляем русские labels
        self.fields['username'].label = 'Имя пользователя'
        self.fields['email'].label = 'Email'
        self.fields['first_name'].label = 'Имя'
        self.fields['last_name'].label = 'Фамилия'
        self.fields['password1'].label = 'Пароль'
        self.fields['password2'].label = 'Подтверждение пароля'
        
        # Добавляем подсказки
        self.fields['username'].help_text = 'Обязательное поле. Только буквы, цифры и @/./+/-/_'
        self.fields['password1'].help_text = 'Минимум 8 символов'
        self.fields['password2'].help_text = 'Введите тот же пароль, что и выше' 

class CustomUserChangeForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'is_senior', 'isAdmin') 