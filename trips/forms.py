from django import forms
from .models import TechnicalStaffRecord, Organization
from django.utils import timezone

class TechnicalStaffRecordForm(forms.ModelForm):
    class Meta:
        model = TechnicalStaffRecord
        fields = ['organization', 'value']
        widgets = {
            'organization': forms.HiddenInput(),
            'value': forms.NumberInput(attrs={'min': 0, 'class': 'form-control', 'placeholder': 'Число тех. состава'}),
        }

    def __init__(self, *args, **kwargs):
        org = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        if org:
            self.fields['organization'].initial = org.id

    def clean(self):
        cleaned_data = super().clean()
        # Проверка на дублирование записи за неделю
        org = cleaned_data.get('organization')
        week = timezone.now().date() - timezone.timedelta(days=timezone.now().weekday())
        if TechnicalStaffRecord.objects.filter(organization=org, week=week).exists():
            raise forms.ValidationError('Запись за эту неделю уже существует.')
        return cleaned_data 