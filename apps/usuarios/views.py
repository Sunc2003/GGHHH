
from django.urls import reverse_lazy
from apps.usuarios.forms import CustomUserCreationForm
from apps.usuarios.models import CustomUser
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from datetime import timedelta
from apps.usuarios.models import SolicitudCodigo, DetalleCodigo, SolicitudAdjunto
from apps.usuarios.forms import SolicitudCodigoForm, DetalleCodigoForm, DetalleCodigoFormSet
from django.views.generic import CreateView, ListView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from apps.organizaciones.models import Area, Cargo
from django.utils.decorators import method_decorator
from apps.permisos.decorators import permiso_requerido 
from .forms import CambiarEstadoForm
import os
from apps.utils.supabase_storage import SupabaseStorage
from decimal import Decimal
from django.contrib import messages
from django.views.generic.detail import DetailView
from django.views.generic.base import TemplateResponseMixin
from django.forms import formset_factory
from django.db.models import Q
from django.core.files.storage import default_storage
from django.conf import settings
from django.db import models


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .forms import ArchivoProcesoForm
from .models import ArchivoProceso
from apps.utils.supabase_storage import SupabaseStorage
import os



from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from apps.utils.supabase_storage import SupabaseStorage
from .forms import ArchivoProcesoForm
from .models import ArchivoProceso
import os

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



@method_decorator(permiso_requerido('SOLICITUD_CODIGO'), name='dispatch')    
class SolicitudConDetallesCreateView(LoginRequiredMixin, View):
    template_name = 'solicitud_form.html'
    success_url = reverse_lazy('panel_admin_usuarios')

    def get(self, request):
        """Mostrar formulario y formset vacío"""
        form = SolicitudCodigoForm()
        DetalleCodigoFormSet = formset_factory(DetalleCodigoForm, extra=0, can_delete=False)
        formset = DetalleCodigoFormSet()

        solicitudes_enviadas = SolicitudCodigo.objects.filter(
            solicitante=request.user
        ).order_by('-fecha_creacion')

        return render(request, self.template_name, {
            'form': form,
            'formset': formset,
            'solicitudes_enviadas': solicitudes_enviadas,
            'usuario': request.user
        })

    def post(self, request):
        """Guardar solicitud, adjuntos y productos en Supabase"""
        DetalleCodigoFormSet = formset_factory(DetalleCodigoForm, extra=0, can_delete=False)
        form = SolicitudCodigoForm(request.POST, request.FILES)
        formset = DetalleCodigoFormSet(request.POST)

        archivos = request.FILES.getlist('archivos')
        imagenes = request.FILES.getlist('imagenes')

        print(f"➡️ Archivos (DOCUMENTOS): {len(archivos)} -> {archivos}")
        print(f"➡️ Archivos (IMÁGENES): {len(imagenes)} -> {imagenes}")

        if form.is_valid() and formset.is_valid():
            solicitud = form.save(commit=False)
            solicitud.solicitante = request.user
            solicitud.save()

            # 🔹 Usar Supabase Storage para subir archivos
            storage = SupabaseStorage()

            # 1️⃣ Documentos
            for archivo in archivos:
                ruta = f"solicitudes/{solicitud.id}/documentos/{archivo.name}"
                storage._save(ruta, archivo)  # sube a Supabase
                SolicitudAdjunto.objects.create(
                    solicitud=solicitud,
                    tipo='documento',
                    archivo=ruta  # guardamos la ruta manualmente
                )

            # 2️⃣ Imágenes
            for imagen in imagenes:
                ruta = f"solicitudes/{solicitud.id}/imagenes/{imagen.name}"
                storage._save(ruta, imagen)
                SolicitudAdjunto.objects.create(
                    solicitud=solicitud,
                    tipo='imagen',
                    archivo=ruta
                )

            print(f"📂 {len(archivos)} documentos y 🖼️ {len(imagenes)} imágenes subidas a Supabase.")

            # 3️⃣ Guardar productos
            productos_guardados = 0
            for f in formset:
                if f.cleaned_data:
                    DetalleCodigo.objects.create(
                        solicitud=solicitud,
                        descripcion=f.cleaned_data.get('descripcion'),
                        marca=f.cleaned_data.get('marca'),
                        udm=f.cleaned_data.get('udm'),
                        origen=f.cleaned_data.get('origen'),
                        proveedor=f.cleaned_data.get('proveedor'),
                        largo=f.cleaned_data.get('largo'),
                        ancho=f.cleaned_data.get('ancho'),
                        alto=f.cleaned_data.get('alto'),
                        peso=f.cleaned_data.get('peso'),
                        costo=f.cleaned_data.get('costo'),
                        sku_proveedor=f.cleaned_data.get('sku_proveedor'),
                        sku_fabricante=f.cleaned_data.get('sku_fabricante'),
                    )
                    productos_guardados += 1

            print(f"📦 {productos_guardados} productos guardados.")

            messages.success(request, "✅ Solicitud registrada y subida a Supabase con éxito.")
            return redirect(self.success_url)

        # 🔹 Si hay errores re-renderizamos
        print("❌ Errores del formulario:", form.errors.as_data())
        print("❌ Errores del formset:", formset.errors)

        solicitudes_enviadas = SolicitudCodigo.objects.filter(
            solicitante=request.user
        ).order_by('-fecha_creacion')

        messages.error(request, "⚠️ Hay errores en el formulario. Revisa los campos.")
        return render(request, self.template_name, {
            'form': form,
            'formset': formset,
            'solicitudes_enviadas': solicitudes_enviadas,
            'usuario': request.user
        })

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

        # 🔹 Obtener los adjuntos organizados
        documentos = self.object.adjuntos.filter(tipo='documento')
        imagenes = self.object.adjuntos.filter(tipo='imagen')

        context['documentos'] = documentos
        context['imagenes'] = imagenes

        # 🔹 Obtener los productos asociados a esta solicitud
        productos = self.object.detalles.all()

        # 🔹 Calcular PMV y PVP por cada producto
        productos_con_calculo = []
        for p in productos:
            pmv = round(p.costo / Decimal('0.84'), 2) if p.costo and p.costo > 0 else None
            pvp = round(pmv / Decimal('0.6'), 2) if pmv else None

            productos_con_calculo.append({
                'producto': p,
                'pmv': pmv,
                'pvp': pvp
            })

        context['productos'] = productos_con_calculo
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
        area_id = self.request.GET.get('area', '')
        cargo_id = self.request.GET.get('cargo', '')
        filtro_nombre = self.request.GET.get('q', '').strip()  # Nuevo
 
        if area_id:
            qs = qs.filter(area_id=area_id)
        if cargo_id:
            qs = qs.filter(cargo_id=cargo_id)
        if filtro_nombre:
            qs = qs.filter(
                Q(first_name__icontains=filtro_nombre) |
                Q(last_name__icontains=filtro_nombre) |
                Q(username__icontains=filtro_nombre)
            )
        return qs
 
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['areas'] = Area.objects.all()
        context['cargos'] = Cargo.objects.all()
        context['filtro_area'] = self.request.GET.get('area', '')
        context['filtro_cargo'] = self.request.GET.get('cargo', '')
        context['filtro_nombre'] = self.request.GET.get('q', '')  # Nuevo
        return context

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






@login_required
def procesos_view(request):
    print("📌 Entrando a procesos_view")

    form = ArchivoProcesoForm(request.POST or None, request.FILES or None)

    if request.method == 'POST' and form.is_valid():
        archivo = form.cleaned_data['archivo']
        ext = os.path.splitext(archivo.name)[1].lower()

        if ext not in ['.pdf', '.ppt', '.pptx']:
            form.add_error('archivo', 'Solo se permiten archivos PDF o PPT.')
        else:
            try:
                print("📤 Subiendo a Supabase...")
                storage = SupabaseStorage()
                ruta = f"procesos/{archivo.name}"
                storage._save(ruta, archivo)

                ArchivoProceso.objects.create(
                    nombre=archivo.name,
                    archivo=ruta,
                    tipo='pdf' if ext == '.pdf' else 'ppt',
                    subido_por=request.user
                )

                return redirect('procesos')
            except Exception as e:
                print("❌ Error al subir:", e)
                form.add_error(None, f"Error al subir archivo: {e}")

    archivos = ArchivoProceso.objects.order_by('-fecha_subida')
    try:
        storage = SupabaseStorage()
        for a in archivos:
            a.url_publica = storage.get_public_url(a.archivo.name)
    except Exception as e:
        for a in archivos:
            a.url_publica = '#'

    return render(request, 'procesos.html', {
        'form': form,
        'archivos': archivos
    })