
from django.urls import reverse_lazy
from apps.usuarios.forms import CustomUserCreationForm
from apps.usuarios.models import CustomUser
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from datetime import timedelta
from apps.usuarios.models import SolicitudCodigo
from apps.usuarios.forms import SolicitudCodigoForm
from django.views.generic import CreateView, ListView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from apps.organizaciones.models import Area, Cargo
from django.utils.decorators import method_decorator
from apps.permisos.decorators import permiso_requerido 
from .forms import CambiarEstadoForm
import os
from apps.utils.supabase_storage import SupabaseStorage





class IniciarSesionView(LoginView):
    template_name = 'login.html'  # Ruta al template
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Usuario'})
        form.fields['password'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Contraseña'})
        return form
    
@method_decorator(permiso_requerido('CREACION_USUARIO'), name='dispatch')
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
    ##solicitudes_enviadas = SolicitudCodigo.objects.filter(solicitante=request.user)
    solicitudes_recibidas = SolicitudCodigo.objects.filter(receptor=request.user)

    context = {
        'usuarios': usuarios,
        ##'solicitudes_enviadas': solicitudes_enviadas,
        'solicitudes_recibidas': solicitudes_recibidas,
    }

    return render(request, 'panel_admin.html', context)


##DESCOMENTAR PARA CUANDO TENGAMOS LOS PERMISOS CONFIGURADOSdef solicitud_form(request):
    usuarios = CustomUser.objects.all()

    context = {
        'usuarios': usuarios,
    }

    if request.user.tiene_permiso('SOLICITUD_CODIGO'):
        context['solicitudes_enviadas'] = SolicitudCodigo.objects.filter(solicitante=request.user)

    if request.user.tiene_permiso('VER_SOLICITUDES_RECIBIDAS'):
        context['solicitudes_recibidas'] = SolicitudCodigo.objects.filter(receptor=request.user)

    return render(request, 'solicitud_form.html', context)

##def solicitud_form(request):  ##CUANDO SE HABILITE LA DE ARRIBA BORRAR ESTA
    print("Usuario autenticado:", request.user)
    print("Solicitudes enviadas:", SolicitudCodigo.objects.filter(solicitante=request.user).count())
    usuarios = CustomUser.objects.all()

    solicitudes_enviadas = SolicitudCodigo.objects.filter(solicitante=request.user)
    solicitudes_recibidas = SolicitudCodigo.objects.filter(receptor=request.user)

    context = {
        'usuarios': usuarios,
        'solicitudes_enviadas': solicitudes_enviadas,
        'solicitudes_recibidas': solicitudes_recibidas,
    }

    return render(request, 'solicitud_form.html', context)

##@login_required
##def solicitudes_enviadas_view(request):
    solicitudes_enviadas = SolicitudCodigo.objects.filter(solicitante=request.user).order_by('-fecha_creacion')

    return render(request, 'solicitud_form.html', {
        'usuario': request.user,
        'solicitudes_enviadas': solicitudes_enviadas
    })

##@method_decorator(permiso_requerido('SOLICITUD_CODIGO'), name='dispatch')
##class SolicitudCreateView(LoginRequiredMixin, CreateView):
    model = SolicitudCodigo
    form_class = SolicitudCodigoForm
    template_name = 'solicitud_form.html'
    success_url = reverse_lazy('panel_admin_usuarios')

    def form_valid(self, form):
        form.instance.solicitante = self.request.user
        return super().form_valid(form)

@method_decorator(permiso_requerido('SOLICITUD_CODIGO'), name='dispatch')    
class SolicitudCreateView(LoginRequiredMixin, CreateView):
    model = SolicitudCodigo
    form_class = SolicitudCodigoForm
    template_name = 'solicitud_form.html'
    success_url = reverse_lazy('panel_admin_usuarios')

    def form_valid(self, form):
        form.instance.solicitante = self.request.user
        solicitud = form.save(commit=False)  # aún no guardamos los archivos
        storage = SupabaseStorage()

        # Guardar la solicitud sin archivos todavía
        solicitud.save()

        # Subida forzada a Supabase Storage
        archivo = self.request.FILES.get('archivo_cotizacion')
        if archivo:
            ruta = f"cotizaciones/{archivo.name}"
            storage._save(ruta, archivo)
            solicitud.archivo_cotizacion.name = ruta  # asigna ruta manualmente

        imagen = self.request.FILES.get('imagen_whatsapp')
        if imagen:
            ruta_img = f"cotizaciones/img/{imagen.name}"
            storage._save(ruta_img, imagen)
            solicitud.imagen_whatsapp.name = ruta_img

        solicitud.save()  # ahora sí guarda con los campos de archivo

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['solicitudes_enviadas'] = SolicitudCodigo.objects.filter(
            solicitante=self.request.user
        ).order_by('-fecha_creacion')
        context['usuario'] = self.request.user
        return context


class SolicitudesRecibidasView(LoginRequiredMixin, ListView):
    model = SolicitudCodigo
    template_name = 'solicitudes_recibidas.html'
    context_object_name = 'solicitudes_recibidas'

    def get_queryset(self):
        qs = SolicitudCodigo.objects.filter(receptor=self.request.user)
        print("Filtradas antes:", qs.count())
        pendientes = qs.filter(estado='pendiente')
        print("Solo pendientes:", pendientes.count())
        for s in pendientes:
            print(s.id, s.estado)
        return pendientes       
        
        
class SolicitudDetailView(DetailView):
    model = SolicitudCodigo
    template_name = 'solicitud_detalle.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        archivo = self.object.archivo_cotizacion.name.lower()

        context['es_pdf'] = archivo.endswith('.pdf')
        context['es_imagen'] = archivo.endswith(('.jpg', '.jpeg', '.png'))

        return context

class CambiarEstadoView(UpdateView):
    model = SolicitudCodigo
    form_class = CambiarEstadoForm
    template_name = 'cambiar_estado.html'

    def form_valid(self, form):
        solicitud = form.save(commit=False)
        solicitud.estado = 'creado'
        solicitud.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('detalle_solicitud', kwargs={'pk': self.object.pk})


class UsuariosADListView(ListView):
    model = CustomUser
    template_name = 'usuarios_ad.html'
    context_object_name = 'usuarios'
    paginate_by = 10

    def get_queryset(self):
        qs = super().get_queryset()
        area_id = self.request.GET.get('area')
        cargo_id = self.request.GET.get('cargo')

        if area_id:
            qs = qs.filter(area_id=area_id)
        if cargo_id:
            qs = qs.filter(cargo_id=cargo_id)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['areas'] = Area.objects.all()
        context['cargos'] = Cargo.objects.all()
        context['filtro_area'] = self.request.GET.get('area', '')
        context['filtro_cargo'] = self.request.GET.get('cargo', '')
        return context
    
def perfil_usuario(request):
    return render(request, 'perfil.html', {'usuario': request.user})

def solicitudes_enviadas_view(request):
    solicitudes = SolicitudCodigo.objects.filter(solicitante=request.user).order_by('-fecha_envio')
    
    context = {
        'usuario': request.user,  # 👈 necesario para que funcione {{ usuario. ... }}
        'solicitudes': solicitudes
    }
    return render(request, 'perfil.html', context)