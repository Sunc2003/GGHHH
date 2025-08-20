from django.urls import path
from . import views
from django.urls import path
from .views import adjunto_ver, solicitar_ayuda, mi_ticket_detalle, lista_tickets, tickets_bandeja, tickets_detalle, tickets_cambiar_estado

urlpatterns = [
    # Vista para usuarios que crean tickets y ven sus propios hilos
    path("ayuda/", views.solicitar_ayuda, name="tickets_solicitar_ayuda"),

    # Bandeja para TI (agentes)
    path("bandeja/", views.tickets_bandeja, name="tickets_bandeja"),

    # Detalle para TI (agentes)
    path("<int:pk>/", views.tickets_detalle, name="tickets_detalle"),

    # Cambiar estado / asignar (solo TI)
    path("<int:pk>/cambiar-estado/", views.tickets_cambiar_estado, name="tickets_cambiar_estado"),

    # Detalle que ve el solicitante (su propio hilo y respuestas)
    path("m/<int:pk>/", views.mi_ticket_detalle, name="mi_ticket_detalle"),

    path('tickets/adjunto/<int:adjunto_id>/', adjunto_ver, name='tickets_adjunto_ver'),
]



