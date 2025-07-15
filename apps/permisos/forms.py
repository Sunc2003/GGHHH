# permisos/forms.py
from django import forms
from apps.permisos.models import Permiso
from apps.usuarios.models import CustomUser

class PermisoForm(forms.ModelForm):
    class Meta:
        model = Permiso
        fields = ['codigo', 'nombre', 'descripcion']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class AsignarPermisosUsuarioForm(forms.ModelForm):
    permisos_directos = forms.ModelMultipleChoiceField(
        queryset=Permiso.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Permisos asignados"
    )

    class Meta:
        model = CustomUser
        fields = ['permisos_directos']