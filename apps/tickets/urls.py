# apps/tickets/urls.py
from django.urls import path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    # Lista principal (/tickets/)
    path("", views.lista_tickets, name="tickets_lista"),

    # Alias legible (/tickets/lista/)
    path("lista/", views.lista_tickets, name="lista_tickets"),

    # Compatibilidad con enlaces viejos que apuntaban a /tickets/tickets/
    path("tickets/", RedirectView.as_view(pattern_name="tickets_lista", permanent=True)),

    # Flujo del solicitante: crear y ver sus tickets (/tickets/ayuda/)
    path("ayuda/", views.solicitar_ayuda, name="tickets_solicitar_ayuda"),

    # (Opcional) Alias legacy de "tickets_crear" si algún template lo usa
    # Redirige a la pantalla de "Nuevo ticket"
    path(
        "crear/",
        RedirectView.as_view(url="/tickets/ayuda/?tab=crear&new=1", permanent=False),
        name="tickets_crear",
    ),

    # Bandeja para agentes TI (/tickets/bandeja/)
    path("bandeja/", views.tickets_bandeja, name="tickets_bandeja"),

    # Detalle que ve el solicitante (/tickets/m/<id>/)
    path("m/<int:pk>/", views.mi_ticket_detalle, name="mi_ticket_detalle"),

    # Ver adjunto con control de permisos (/tickets/adjunto/<id>/)
    path("adjunto/<int:adjunto_id>/", views.adjunto_ver, name="tickets_adjunto_ver"),

    # Detalle interno para TI (/tickets/<id>/) y cambio de estado
    path("<int:pk>/", views.tickets_detalle, name="tickets_detalle"),
    path("<int:pk>/cambiar-estado/", views.tickets_cambiar_estado, name="tickets_cambiar_estado"),
]
