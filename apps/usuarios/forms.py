from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, SolicitudCodigo
from django.core.exceptions import ValidationError
from apps.organizaciones.models import Area, Cargo


class CustomUserCreationForm(UserCreationForm):
    area = forms.ModelChoiceField(
        queryset=Area.objects.all(),
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    cargo = forms.ModelChoiceField(
        queryset=Cargo.objects.none(),
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'email',
            'area', 'cargo',
            'usuario_ad', 'usuario_office', 'usuario_sap',
            'equipo_a_cargo', 'impresora_a_cargo', 'movil',
        ]
        widgets = {
            'usuario_ad':        forms.TextInput(attrs={'class': 'form-control'}),
            'usuario_office':    forms.TextInput(attrs={'class': 'form-control'}),
            'usuario_sap':       forms.TextInput(attrs={'class': 'form-control'}),
            'equipo_a_cargo':    forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'impresora_a_cargo': forms.TextInput(attrs={'class': 'form-control'}),
            'movil':             forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'

        if 'area' in self.data:
            try:
                area_id = int(self.data.get('area'))
                self.fields['cargo'].queryset = Cargo.objects.filter(area_id=area_id).order_by('nombre')
            except (ValueError, TypeError):
                self.fields['cargo'].queryset = Cargo.objects.none()
        elif self.instance.pk and self.instance.area:
            self.fields['cargo'].queryset = Cargo.objects.filter(area=self.instance.area).order_by('nombre')
        else:
            self.fields['cargo'].queryset = Cargo.objects.none()

    # ⬇️ Aquí el PASO B: método save()
    def save(self, commit=True):
        user = super().save(commit=False)

        # Generar username como "Nombre Apellido"
        nombre = self.cleaned_data.get('first_name', '').strip()
        apellido = self.cleaned_data.get('last_name', '').strip()
        base_username = f"{nombre} {apellido}"
        username = base_username
        count = 1
        while CustomUser.objects.filter(username=username).exists():
            username = f"{base_username} {count}"
            count += 1

        user.username = username
        user.email = self.cleaned_data['email']

        if commit:
            user.save()
            self.save_m2m()
        return user


class SolicitudCodigoForm(forms.ModelForm):
    class Meta:
        model = SolicitudCodigo
        exclude = ['solicitante', 'estado', 'fecha_creacion', 'rut_proveedor']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super(SolicitudCodigoForm, self).__init__(*args, **kwargs)

        # Personalizamos etiquetas y orden de campos
        self.fields['receptor'].label = "Selecciona receptor"
        self.fields['empresa'].label = "Empresa"
        self.fields['tipo_solicitud'].label = "Tipo de Solicitud"
        self.fields['cotizacion'].label = "Tipo de Cotización"
        self.fields['archivo_cotizacion'].label = "Archivo Cotización (si aplica)"
        self.fields['imagen_whatsapp'].label = "Imagen WhatsApp (si aplica)"
        self.fields['proveedor'].label = "Proveedor"
        self.fields['marca'].label = "Marca"
        self.fields['udm'].label = "Unidad de Medida (UDM)"

    def clean(self):
        cleaned_data = super().clean()

        tipo_cotizacion = cleaned_data.get('cotizacion')
        archivo_cotizacion = cleaned_data.get('archivo_cotizacion')
        imagen_whatsapp = cleaned_data.get('imagen_whatsapp')

        # Validación condicional: si se selecciona "Por Documento", debe haber archivo
        if tipo_cotizacion == 'documento' and not archivo_cotizacion:
            self.add_error('archivo_cotizacion', "Debes adjuntar el documento de cotización.")

        # Validación condicional: si se selecciona "Por WhatsApp", debe haber imagen
        if tipo_cotizacion == 'whatsapp' and not imagen_whatsapp:
            self.add_error('imagen_whatsapp', "Debes adjuntar la imagen enviada por WhatsApp.")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Rellenar el RUT automáticamente desde el proveedor
        if instance.proveedor:
            instance.rut_proveedor = instance.proveedor.rut

        if commit:
            instance.save()
            self.save_m2m()

        return instance