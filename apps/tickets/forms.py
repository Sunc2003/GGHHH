# apps/tickets/forms.py
from django import forms
from .models import Ticket, TicketMensaje

# Widget múltiple compatible con Django 5.x (no uses ClearableFileInput)
class MultiFileInput(forms.FileInput):
    allow_multiple_selected = True

class TicketForm(forms.ModelForm):
    # Campo "virtual" (NO pertenece al modelo Ticket)
    archivos = forms.FileField(
        required=False,
        widget=MultiFileInput(attrs={"class": "form-control"}),
        help_text="Puedes adjuntar varios archivos."
    )

    class Meta:
        model = Ticket
        # ⚠️ Pon SOLO los campos que EXISTEN en tu modelo.
        # Si tu Ticket NO tiene prioridad/asignado_a, deja SOLO ["titulo", "descripcion"].
        fields = ["titulo", "descripcion"]  # agrega "prioridad", "asignado_a" si tu modelo los tiene
        widgets = {
            "titulo": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Título del problema"
            }),
            "descripcion": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Describe lo ocurrido"
            }),
            # Si tu modelo tiene estos campos, añade sus widgets:
            # "prioridad": forms.Select(attrs={"class": "form-select"}),
            # "asignado_a": forms.Select(attrs={"class": "form-select"}),
        }

class TicketMensajeForm(forms.ModelForm):
    # También “virtual” si quieres adjuntar archivos en las respuestas
    archivos = forms.FileField(
        required=False,
        widget=MultiFileInput(attrs={"class": "form-control"}),
        help_text="Adjunta archivos opcionalmente."
    )

    class Meta:
        model = TicketMensaje
        fields = ["mensaje"]  # NO incluyas 'archivos' aquí (no es del modelo)
        widgets = {
            "mensaje": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Escribe tu respuesta…"
            }),
        }
