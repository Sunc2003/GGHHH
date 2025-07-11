from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, SolicitudCodigo


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'area',
            'cargo',
            'usuario_ad',
            'usuario_office',
            'usuario_sap',
            'equipo_a_cargo',
            'impresora_a_cargo',
            'movil',
        ]
        widgets = {
            'area': forms.Select(attrs={'class': 'form-control'}),
            'cargo': forms.Select(attrs={'class': 'form-control'}),
            'usuario_ad': forms.TextInput(attrs={'class': 'form-control'}),
            'usuario_office': forms.TextInput(attrs={'class': 'form-control'}),
            'usuario_sap': forms.TextInput(attrs={'class': 'form-control'}),
            'equipo_a_cargo': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'impresora_a_cargo': forms.TextInput(attrs={'class': 'form-control'}),
            'movil': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super(CustomUserCreationForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if not field.widget.attrs.get('class'):
                field.widget.attrs['class'] = 'form-control'


class SolicitudCodigoForm(forms.ModelForm):
    class Meta:
        model = SolicitudCodigo
        fields = ['receptor', 'titulo', 'descripcion']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 4}),
        }