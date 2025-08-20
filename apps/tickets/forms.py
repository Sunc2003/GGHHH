from django import forms
from .models import Ticket, TicketMensaje

class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ["titulo", "descripcion"]  # solo los campos reales del modelo
        widgets = {
            "titulo": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Título del problema",
            }),
            "descripcion": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Describe lo ocurrido",
            }),
        }

class TicketMensajeForm(forms.ModelForm):
    class Meta:
        model = TicketMensaje
        fields = ["mensaje"]
        widgets = {
            "mensaje": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Escribe tu respuesta…",
            }),
        }
