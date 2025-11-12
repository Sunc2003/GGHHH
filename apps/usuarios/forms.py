from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.forms import formset_factory
from django.core.files.storage import default_storage
 
from .models import CustomUser, SolicitudCodigo, DetalleCodigo
from apps.organizaciones.models import Area, Cargo
from apps.permisos.models import Permiso
 
 
# =========================
#   MultiFileInput Widget
# =========================
class MultiFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True
 
    def value_from_datadict(self, data, files, name):
        if self.allow_multiple_selected:
            return files.getlist(name)
        return super().value_from_datadict(data, files, name)
 
 
class MultiFileField(forms.FileField):
    widget = MultiFileInput
 
    def clean(self, data, initial=None):
        # Si no hay archivos, devolvemos lista vacía
        if data in self.empty_values:
            return []
        return data
 
 
# =========================
#   Formulario de Usuario
# =========================
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
            'usuario_ad': forms.TextInput(attrs={'class': 'form-control'}),
            'usuario_office': forms.TextInput(attrs={'class': 'form-control'}),
            'usuario_sap': forms.TextInput(attrs={'class': 'form-control'}),
            'equipo_a_cargo': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'impresora_a_cargo': forms.TextInput(attrs={'class': 'form-control'}),
            'movil': forms.TextInput(attrs={'class': 'form-control'}),
        }
 
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
 
        # Aplica la clase CSS por defecto
        for name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'
 
        # Filtra cargos dinámicamente
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
 
    def save(self, commit=True):
        """Genera username dinámico con nombre + apellido"""
        user = super().save(commit=False)
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
 
 
# =========================
#   Formulario de Solicitud Completa
# =========================
class SolicitudCodigoForm(forms.ModelForm):
    archivos = MultiFileField(
        required=False,
        label="Adjuntar documentos"
    )
    imagenes = MultiFileField(
        required=False,
        label="Adjuntar imágenes WhatsApp"
    )
 
    class Meta:
        model = SolicitudCodigo
        exclude = ['solicitante', 'estado', 'fecha_creacion']
        widgets = {
            'mensaje': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Escribe un mensaje...'}),
        }
 
    def __init__(self, *args, **kwargs):
        super(SolicitudCodigoForm, self).__init__(*args, **kwargs)
 
        from django.contrib.auth import get_user_model
        User = get_user_model()
 
        try:
            area_sistemas = Area.objects.get(nombre__iexact="Sistemas")
            self.fields['receptor'].queryset = User.objects.filter(area=area_sistemas)
            self.fields['receptor'].queryset = self.fields['receptor'].queryset.exclude(
                username__in=[
                    'Valeria Godoy', 'Felipe Leiva', 'Iván Henríquez',
                    'Juan Leiva', 'Valentina Pérez'
                ]
            )
        except Area.DoesNotExist:
            self.fields['receptor'].queryset = User.objects.none()
 
        # Etiquetas personalizadas
        self.fields['receptor'].label = "Selecciona receptor"
        self.fields['empresa'].label = "Empresa"
        self.fields['tipo_solicitud'].label = "Tipo de Solicitud"
        self.fields['cotizacion'].label = "Tipo de Cotización"
        self.fields['mensaje'].label = "Mensaje para el receptor"
 
    def clean(self):
        cleaned_data = super().clean()
        tipo_cotizacion = cleaned_data.get('cotizacion')
 
        archivos = cleaned_data.get('archivos', [])
        imagenes = cleaned_data.get('imagenes', [])
 
        print("🟢 Cleaned data archivos:", archivos)
        print("🟢 Cleaned data imagenes:", imagenes)
 
        if tipo_cotizacion == 'documento' and not archivos:
            self.add_error('archivos', "Debes adjuntar al menos un documento de cotización.")
        if tipo_cotizacion == 'whatsapp' and not imagenes:
            self.add_error('imagenes', "Debes adjuntar al menos una imagen de WhatsApp.")
 
        return cleaned_data
 
 
# =========================
#   Formulario de Detalles
# =========================
class DetalleCodigoForm(forms.ModelForm):
    class Meta:
        model = DetalleCodigo
        exclude = ['solicitud']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 2}),
        }
 
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Etiquetas personalizadas
        self.fields['origen'].label = "Origen"
        self.fields['proveedor'].label = "Proveedor"
        self.fields['marca'].label = "Marca"
        self.fields['udm'].label = "Unidad de Medida"
        self.fields['largo'].label = "Largo (cm)"
        self.fields['ancho'].label = "Ancho (cm)"
        self.fields['alto'].label = "Alto (cm)"
        self.fields['peso'].label = "Peso (kg)"
        self.fields['costo'].label = "Costo ($)"
        self.fields['sku_proveedor'].label = "SKU Proveedor"
        self.fields['sku_fabricante'].label = "SKU Fabricante"
 
        # Placeholders
        self.fields['descripcion'].widget.attrs.update({'placeholder': 'Descripción del producto'})
        self.fields['costo'].widget.attrs.update({'placeholder': 'Ej: 25000'})
        self.fields['sku_proveedor'].widget.attrs.update({'placeholder': 'Código del proveedor'})
        self.fields['sku_fabricante'].widget.attrs.update({'placeholder': 'Código del fabricante'})
 
 
DetalleCodigoFormSet = formset_factory(DetalleCodigoForm, extra=0, can_delete=False)
 
 
# =========================
#   Cambiar Estado
# =========================
class CambiarEstadoForm(forms.ModelForm):
    comentario_estado = forms.CharField(
        label="Comentario",
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Adjunta Código y Descripción...'
        })
    )
 
    class Meta:
        model = SolicitudCodigo
        fields = ['comentario_estado']
 
 
# =========================
#   Perfil y Permisos
# =========================
class PerfilYPermisosUsuarioForm(forms.ModelForm):
    permisos_directos = forms.ModelMultipleChoiceField(
        queryset=Permiso.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Permisos"
    )
 
    class Meta:
        model = CustomUser
        fields = [
            'first_name','last_name','email','area','cargo',
            'usuario_ad','usuario_office','usuario_sap',
            'equipo_a_cargo','impresora_a_cargo','movil',
            'permisos_directos'
        ]
 
    def _build_unique_username(self, base: str, user_pk=None) -> str:
        base = (base or "").strip() or (self.cleaned_data.get('email','').split('@')[0] or 'usuario')
        username, i = base, 1
        qs = CustomUser.objects.all()
        if user_pk:
            qs = qs.exclude(pk=user_pk)
        while qs.filter(username=username).exists():
            username = f"{base} {i}"; i += 1
        return username
 
    def save(self, commit=True):
        old_first = (self.instance.first_name or "").strip()
        old_last  = (self.instance.last_name  or "").strip()
 
        user = super().save(commit=False)
 
        new_first = (self.cleaned_data.get('first_name') or "").strip()
        new_last  = (self.cleaned_data.get('last_name')  or "").strip()
 
        old_base = f"{old_first} {old_last}".strip()
        new_base = f"{new_first} {new_last}".strip()
 
        if not self.instance.pk or old_base != new_base:
            user.username = self._build_unique_username(new_base, user_pk=user.pk)
 
        if commit:
            user.save()
            self.save_m2m()
        return user
 
 
# =========================
#   Formulario de Activación
# =========================
# =========================
#   Formulario de Activación / Modificación
# =========================
class SolicitudActivacionForm(forms.ModelForm):
    codigo_extra = forms.CharField(
        label="Código",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Escribe el código o descripción",
            }
        )
    )
 
    class Meta:
        model = SolicitudCodigo
        fields = ["receptor", "empresa", "codigo_extra", "mensaje"]
        widgets = {
            "receptor": forms.Select(attrs={"class": "form-select"}),
            "empresa": forms.Select(attrs={"class": "form-select"}),
            "mensaje": forms.Textarea(
                attrs={"class": "form-control", "rows": 3, "placeholder": "Agrega un detalle adicional"}
            ),
        }
 
# =========================
#   Formulario de Producción (EXCLUSIVO)
# =========================
 
from apps.sap.models import Proveedor, Marca, UDM  # ajusta import según tu estructura real
 
class ProduccionDetalleForm(forms.ModelForm):
    TIPO_PADRE_HIJO = (
        ("PADRE", "Padre"),
        ("HIJO", "Hijo"),
    )
    tipo_padre_hijo = forms.ChoiceField(choices=TIPO_PADRE_HIJO, label="¿Padre o Hijo?")
    sin_sku = forms.BooleanField(required=False, label="Sin SKU (Proveedor)")
    sin_codigo = forms.BooleanField(required=False, label="Sin código (Fabricante)")
 
    # FKs como ModelChoiceField (OBLIGATORIO por tu modelo)
    proveedor = forms.ModelChoiceField(queryset=Proveedor.objects.all(), label="Nombre Proveedor")
    marca = forms.ModelChoiceField(queryset=Marca.objects.all(), label="Marca")
    # UDM **NO** se muestra en UI (lo seteamos en la vista con un default), pero si prefieres mostrarlo:
    # udm = forms.ModelChoiceField(queryset=UDM.objects.all(), label="Unidad de Medida")
 
    class Meta:
        model = DetalleCodigo
        fields = [
            "origen",
            "proveedor",
            "descripcion",
            "marca",
            "largo", "ancho", "alto", "peso",
            "costo",
            # "udm",  # si decides mostrarlo, descomenta aquí y arriba
        ]
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 2, "placeholder": "Descripción del producto"}),
        }
 
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["origen"].label = "Origen"
        self.fields["largo"].label = "Largo (cm)"
        self.fields["ancho"].label = "Ancho (cm)"
        self.fields["alto"].label = "Alto (cm)"
        self.fields["peso"].label = "Peso (kg)"
        self.fields["costo"].label = "Costo ($)"
        for name, field in self.fields.items():
            css = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (css + " form-control").strip()
 
    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("descripcion"):
            raise ValidationError("La descripción es obligatoria.")
        if cleaned.get("costo") in (None, ""):
            raise ValidationError("El costo es obligatorio.")
        return cleaned
 
    def build_detalle_kwargs(self):
        data = self.cleaned_data.copy()
        return {
            "origen": data["origen"],
            "proveedor": data["proveedor"],
            "descripcion": data["descripcion"],
            "marca": data["marca"],
            "largo": data.get("largo"),
            "ancho": data.get("ancho"),
            "alto": data.get("alto"),
            "peso": data.get("peso"),
            "costo": data["costo"],
            # 'udm' lo seteamos en la vista (default) si no lo muestras en UI
        }
        
# =========================
#   Cabecera Producción: receptor + empresa
# =========================
from django import forms
from django.contrib.auth import get_user_model
 
class ProduccionHeaderForm(forms.Form):
    receptor = forms.ModelChoiceField(
        queryset=get_user_model().objects.none(),
        label="Enviar a",
        widget=forms.Select(attrs={"class": "form-select"})
    )
    empresa = forms.ChoiceField(
        choices=SolicitudCodigo.EMPRESAS,
        initial="marsella",
        required=True,
        label="Empresa",
        widget=forms.Select(attrs={"class": "form-select"})
    )
 
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        User = get_user_model()
        # Por defecto: usuarios del área "Sistemas" excluyendo los que ya filtras
        try:
            area_sistemas = Area.objects.get(nombre__iexact="Sistemas")
            qs = User.objects.filter(area=area_sistemas).exclude(
                username__in=['Valeria Godoy','Felipe Leiva','Iván Henríquez','Juan Leiva','Valentina Pérez']
            )
            if not qs.exists():
                qs = User.objects.all()
        except Area.DoesNotExist:
            qs = User.objects.all()
        self.fields["receptor"].queryset = qs.order_by("first_name", "last_name", "username")