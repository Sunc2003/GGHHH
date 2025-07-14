from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from .forms import CustomUserCreationForm
from .models import CustomUser
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from datetime import timedelta
from .models import SolicitudCodigo
from .forms import SolicitudCodigoForm
from django.views.generic import CreateView, ListView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View


class IniciarSesionView(LoginView):
    template_name = 'login.html'  # Ruta al template
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Usuario'})
        form.fields['password'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Contraseña'})
        return form
    

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
    solicitudes_enviadas = SolicitudCodigo.objects.filter(solicitante=request.user)
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
    template_name = 'solicitud_form.html'
    success_url = reverse_lazy('panel_admin_usuarios')

    def form_valid(self, form):
        form.instance.solicitante = self.request.user
        return super().form_valid(form)

class SolicitudesRecibidasView(LoginRequiredMixin, ListView):
    model = SolicitudCodigo
    template_name = 'solicitudes_recibidas.html'

    def get_queryset(self):
        return SolicitudCodigo.objects.filter(receptor=self.request.user)

class SolicitudDetailView(LoginRequiredMixin, DetailView):
    model = SolicitudCodigo
    template_name = 'solicitud_detalle.html'

class CambiarEstadoView(View):
    def get(self, request, pk):
        solicitud = get_object_or_404(SolicitudCodigo, pk=pk)

        if request.user == solicitud.receptor and solicitud.estado == 'pendiente':
            solicitud.estado = 'creado'
            solicitud.save()

        return redirect('panel_admin_usuarios')  # Asegúrate que esta URL existe
