from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from .forms import CustomUserCreationForm
from .models import CustomUser
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from .models import SolicitudCodigo
from .forms import SolicitudCodigoForm
from django.views.generic import CreateView, ListView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin


class IniciarSesionView(LoginView):
    template_name = 'login.html'  # Ruta al template

class RegistroUsuarioView(CreateView):
    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = 'registro.html'
    success_url = reverse_lazy('login')  # Redirige al login después de registrarse

class CerrarSesionView(LogoutView):
    next_page = reverse_lazy('login')

def es_admin(user):
    return user.is_authenticated and user.tipo_usuario == 'admin'

##@user_passes_test(es_admin)

def panel_admin_usuarios(request):
    usuarios = CustomUser.objects.all()
    ahora = timezone.now()
    minutos_activo = 5

    for u in usuarios:
        u.en_linea = False
        if u.last_login and (ahora - u.last_login) < timedelta(minutes=minutos_activo):
            u.en_linea = True

    # Lógica para solicitudes
    solicitudes_enviadas = SolicitudCodigo.objects.filter(emisor=request.user)
    solicitudes_recibidas = SolicitudCodigo.objects.filter(receptor=request.user)

    context = {
        'usuarios': usuarios,
        'solicitudes_enviadas': solicitudes_enviadas,
        'solicitudes_recibidas': solicitudes_recibidas,
    }

    return render(request, 'panel_admin.html', context)

class SolicitudCreateView(LoginRequiredMixin, CreateView):
    model = SolicitudCodigo
    form_class = SolicitudCodigoForm
    template_name = 'usuarios/solicitud_form.html'
    success_url = reverse_lazy('solicitudes_enviadas')

    def form_valid(self, form):
        form.instance.solicitante = self.request.user
        return super().form_valid(form)

class SolicitudesRecibidasView(LoginRequiredMixin, ListView):
    model = SolicitudCodigo
    template_name = 'usuarios/solicitudes_recibidas.html'

    def get_queryset(self):
        return SolicitudCodigo.objects.filter(receptor=self.request.user)

class SolicitudDetailView(LoginRequiredMixin, DetailView):
    model = SolicitudCodigo
    template_name = 'usuarios/solicitud_detalle.html'

class CambiarEstadoView(LoginRequiredMixin, UpdateView):
    model = SolicitudCodigo
    fields = ['estado']
    template_name = 'usuarios/cambiar_estado.html'
    success_url = reverse_lazy('solicitudes_recibidas')
