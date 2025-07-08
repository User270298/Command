from django import forms
from django_select2.forms import Select2Widget
from .models import EquipmentRecord

class EquipmentRecordForm(forms.ModelForm):
    name = forms.CharField(widget=Select2Widget)
    device_type = forms.CharField(widget=Select2Widget)
    tech_name = forms.CharField(widget=Select2Widget)
    notes = forms.CharField(required=False, widget=Select2Widget)

    class Meta:
        model = EquipmentRecord
        fields = '__all__' 