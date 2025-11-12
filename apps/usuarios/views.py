from django.urls import reverse_lazy, reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.db.models import Q, F, Avg, ExpressionWrapper, DurationField
from django.utils.timezone import now
from django.utils.http import url_has_allowed_host_and_scheme
from django.urls import resolve, Resolver404
from urllib.parse import urlparse
from decimal import Decimal
import re
from django.db import transaction
from django.views import View
from django.views.generic import (
    CreateView, ListView, DetailView, UpdateView
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from django.utils.decorators import method_decorator
from django import template
 
from apps.usuarios.forms import (
    CustomUserCreationForm, SolicitudCodigoForm,
    DetalleCodigoForm, DetalleCodigoFormSet,
    SolicitudActivacionForm, CambiarEstadoForm,
    PerfilYPermisosUsuarioForm,
    ProduccionDetalleForm,
)
from apps.usuarios.models import CustomUser, SolicitudCodigo, DetalleCodigo, SolicitudAdjunto
from apps.organizaciones.models import Area, Cargo
from apps.permisos.models import Permiso
from apps.permisos.forms import PermisoForm
from apps.permisos.decorators import permiso_requerido
from apps.utils.supabase_storage import SupabaseStorage
 
 



class IniciarSesionView(LoginView):
    template_name = 'login.html'
 
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Usuario'})
        form.fields['password'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Contraseña'})
        return form
 
    def get_success_url(self):
        next_url = self.request.POST.get('next') or self.request.GET.get('next')
        if next_url and url_has_allowed_host_and_scheme(next_url, {self.request.get_host()}):
            path = urlparse(next_url).path
            try:
                resolve(path)
                return next_url
            except Resolver404:
                pass
        return reverse('panel_admin_usuarios')
 
 
@method_decorator(permiso_requerido('CREACION_USUARIO'), name='dispatch')
class RegistroUsuarioView(CreateView):
    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = 'registro.html'
    success_url = reverse_lazy('login')
 
 
class CerrarSesionView(LogoutView):
    next_page = reverse_lazy('login')
 
 
def es_admin(user):
    return user.is_authenticated and user.has_perm('permisos.CREACION_USUARIO')
 
 


register = template.Library()
 
@register.filter
def formatear_tiempo(td):
    if not td:
        return "No disponible"
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{hours}h {minutes}min"
 



def panel_admin_usuarios(request):
    usuarios = CustomUser.objects.all()
    for u in usuarios:
        u.en_linea = bool(cache.get(f"online:{u.id}", False))
 
    solicitudes_recibidas = SolicitudCodigo.objects.filter(receptor=request.user)
    total_recibidas = solicitudes_recibidas.count()
    pendientes = solicitudes_recibidas.filter(estado='pendiente').count()
    completadas = total_recibidas - pendientes
 
    solicitudes_con_respuesta = solicitudes_recibidas.filter(
        estado='creado',
        fecha_creacion__isnull=False
    ).annotate(
        tiempo_respuesta=ExpressionWrapper(
            F('fecha_respuesta') - F('fecha_creacion'),
            output_field=DurationField()
        )
    )
    promedio_respuesta = solicitudes_con_respuesta.aggregate(
        promedio=Avg('tiempo_respuesta')
    )['promedio'] if solicitudes_con_respuesta.exists() else None
 
    solicitudes_enviadas_usuario = SolicitudCodigo.objects.filter(solicitante=request.user)
    total_solicitudes = solicitudes_enviadas_usuario.count()
    solicitudes_respondidas = solicitudes_enviadas_usuario.exclude(estado='pendiente').count()
 
    context = {
        'usuarios': usuarios,
        'solicitudes_recibidas': solicitudes_recibidas,
        'total_recibidas': total_recibidas,
        'pendientes': pendientes,
        'completadas': completadas,
        'promedio_respuesta': promedio_respuesta,
        'total_solicitudes': total_solicitudes,
        'solicitudes_respondidas': solicitudes_respondidas,
    }
    return render(request, 'panel_admin.html', context)
 
 


@method_decorator(permiso_requerido('SOLICITUD_CODIGO'), name='dispatch')
class SolicitudConDetallesCreateView(LoginRequiredMixin, View):
    template_name = 'solicitud_form.html'
    success_url = reverse_lazy('panel_admin_usuarios')
 
    def get(self, request):
        form = SolicitudCodigoForm()
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
        tipo_opcion = request.POST.get("tipo_opcion")
 

        if tipo_opcion in ["activacion", "modificacion"]:
            form = SolicitudActivacionForm(request.POST)
            if form.is_valid():
                solicitud = form.save(commit=False)
                solicitud.solicitante = request.user
                solicitud.tipo_solicitud = tipo_opcion  
                solicitud.save()
                messages.success(
                    request,
                    f"✅ Solicitud de {solicitud.get_tipo_solicitud_display()} registrada con éxito."
                )
                return redirect(self.success_url)
            else:
                messages.error(request, "⚠️ Hay errores en el formulario de Activación/Modificación.")
                return render(request, self.template_name, {
                    'form': SolicitudCodigoForm(), 
                    'formset': DetalleCodigoFormSet(),
                    'solicitudes_enviadas': SolicitudCodigo.objects.filter(
                        solicitante=request.user
                    ).order_by('-fecha_creacion'),
                    'usuario': request.user
                })
 


        form = SolicitudCodigoForm(request.POST, request.FILES)
        formset = DetalleCodigoFormSet(request.POST)
        archivos = request.FILES.getlist('archivos')
        imagenes = request.FILES.getlist('imagenes')
 
        if form.is_valid() and formset.is_valid():
            solicitud = form.save(commit=False)
            solicitud.solicitante = request.user
            solicitud.save()
 
            storage = SupabaseStorage()
            for archivo in archivos:
                ruta = f"solicitudes/{solicitud.id}/documentos/{archivo.name}"
                storage._save(ruta, archivo)
                SolicitudAdjunto.objects.create(solicitud=solicitud, tipo='documento', archivo=ruta)
 
            for imagen in imagenes:
                ruta = f"solicitudes/{solicitud.id}/imagenes/{imagen.name}"
                storage._save(ruta, imagen)
                SolicitudAdjunto.objects.create(solicitud=solicitud, tipo='imagen', archivo=ruta)
 
            productos_guardados = 0
            for f in formset:
                if f.cleaned_data:
                    DetalleCodigo.objects.create(solicitud=solicitud, **f.cleaned_data)
                    productos_guardados += 1
 
            print(f"📦 {productos_guardados} productos guardados.")
            messages.success(request, "✅ Solicitud registrada y subida a Supabase con éxito.")
            return redirect(self.success_url)
 
        # Si hay errores en el formulario grande
        print("❌ Errores del formulario:", form.errors.as_data())
        print("❌ Errores del formset:", formset.errors)
        messages.error(request, "⚠️ Hay errores en el formulario. Revisa los campos.")
        return render(request, self.template_name, {
            'form': form,
            'formset': formset,
            'solicitudes_enviadas': SolicitudCodigo.objects.filter(
                solicitante=request.user
            ).order_by('-fecha_creacion'),
            'usuario': request.user
        })
 
 


@method_decorator(permiso_requerido('VER_SOLICITUDES_RECIBIDAS'), name='dispatch')
class SolicitudesRecibidasView(LoginRequiredMixin, ListView):
    model = SolicitudCodigo
    template_name = 'solicitudes_recibidas.html'
    context_object_name = 'solicitudes_recibidas'
    paginate_by = 25
 
    def get_queryset(self):
        qs = SolicitudCodigo.objects.filter(receptor=self.request.user, estado='pendiente')
        solicitante_id = self.request.GET.get('solicitante', '').strip()
        orden = self.request.GET.get('orden', 'antiguas')
        if solicitante_id:
            qs = qs.filter(solicitante_id=solicitante_id)
        qs = qs.order_by('-fecha_creacion' if orden == 'recientes' else 'fecha_creacion')
        return qs
 
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        solicitantes_ids = (SolicitudCodigo.objects
                            .filter(receptor=self.request.user)
                            .values_list('solicitante_id', flat=True).distinct())
        context['solicitantes'] = CustomUser.objects.filter(id__in=solicitantes_ids).order_by(
            'first_name', 'last_name', 'username'
        )
        context['filtro_solicitante'] = self.request.GET.get('solicitante', '')
        context['filtro_orden'] = self.request.GET.get('orden', 'antiguas')
        return context
 
 

@method_decorator(permiso_requerido('VER_SOLICITUDES_RECIBIDA'), name='dispatch')
class SolicitudDetailView(DetailView):
    model = SolicitudCodigo
    template_name = 'solicitud_detalle.html'
 
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['documentos'] = self.object.adjuntos.filter(tipo='documento')
        context['imagenes'] = self.object.adjuntos.filter(tipo='imagen')
        productos_con_calculo = []
        for p in self.object.detalles.all():
            pmv = round(p.costo / Decimal('0.84'), 2) if p.costo and p.costo > 0 else None
            pvp = round(pmv / Decimal('0.6'), 2) if pmv else None
            productos_con_calculo.append({'producto': p, 'pmv': pmv, 'pvp': pvp})
        context['productos'] = productos_con_calculo
        if self.request.user == self.object.receptor and self.object.estado == 'pendiente':
            context['form'] = CambiarEstadoForm(instance=self.object)
        return context
 


 
class CambiarEstadoView(UpdateView):
    model = SolicitudCodigo
    form_class = CambiarEstadoForm
    template_name = 'cambiar_estado.html'
 
    def form_valid(self, form):
        solicitud = form.save(commit=False)
        solicitud.estado = 'creado'
        solicitud.fecha_respuesta = now()
        solicitud.comentario_estado = form.cleaned_data.get('comentario_estado')
        solicitud.save()
        return super().form_valid(form)
 
    def get_success_url(self):
        return reverse_lazy('detalle_solicitud', kwargs={'pk': self.object.pk})
 
 



@method_decorator(permiso_requerido('VER_AD'), name='dispatch')
class UsuariosADListView(ListView):
    model = CustomUser
    template_name = 'usuarios_ad.html'
    context_object_name = 'usuarios'
    paginate_by = 10
 
    def get_queryset(self):
        qs = super().get_queryset()
        area_id = self.request.GET.get('area', '')
        cargo_id = self.request.GET.get('cargo', '')
        filtro_nombre = self.request.GET.get('q', '').strip()
        filtro_usuario_ad = self.request.GET.get('usuario_ad', '').strip()
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
        if filtro_usuario_ad:
            qs = qs.filter(usuario_ad__icontains=filtro_usuario_ad)
        return qs
 
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['areas'] = Area.objects.all()
        context['cargos'] = Cargo.objects.all()
        context['filtro_area'] = self.request.GET.get('area', '')
        context['filtro_cargo'] = self.request.GET.get('cargo', '')
        context['filtro_nombre'] = self.request.GET.get('q', '')
        context['filtro_usuario_ad'] = self.request.GET.get('usuario_ad', '')
        return context
 
 


def perfil_usuario(request):
    return render(request, 'perfil.html', {'usuario': request.user})
 
 
@login_required
@permiso_requerido('VER_SOLICITUDES')
def solicitudes_enviadas_view(request):
    solicitudes = SolicitudCodigo.objects.filter(solicitante=request.user).order_by('-fecha_creacion')
    return render(request, 'solicitud_enviadas.html', {
        'usuario': request.user,
        'solicitudes_enviadas': solicitudes
    })
 
 

@login_required
@permiso_requerido('PROCESOS')
def procesos_view(request):
    storage = SupabaseStorage()
    carpeta_actual = request.GET.get("path", "").strip("/")
    url_archivo, archivos, carpetas = None, [], []
    if request.method == "POST":
        if "nueva_carpeta" in request.POST:
            nombre_carpeta = request.POST["nueva_carpeta"].strip("/")
            if nombre_carpeta:
                ruta_carpeta = f"{carpeta_actual}/{nombre_carpeta}".strip("/")
                placeholder = ContentFile(b"")
                try:
                    storage._save(f"{ruta_carpeta}/.emptyFolderPlaceholder", placeholder)
                except Exception as e:
                    print("❌ Error al crear carpeta:", e)
        elif request.FILES.get("archivo"):
            archivo = request.FILES["archivo"]
            nombre_original = archivo.name
            nombre = re.sub(r'[^\w\-.]', '_', nombre_original)
            ruta = f"{carpeta_actual}/{nombre}" if carpeta_actual else nombre
            try:
                storage._save(ruta, archivo)
                url_archivo = storage.get_public_url(ruta)
            except Exception as e:
                print("❌ Error al subir archivo:", e)
 
    try:
        lista = storage.client.storage.from_(storage.bucket).list(carpeta_actual or "", {"limit": 9999})
        for item in lista:
            if item.get("metadata"):
                archivos.append({
                    "nombre": item["name"],
                    "url": storage.get_public_url(f"{carpeta_actual}/{item['name']}" if carpeta_actual else item["name"]),
                })
            else:
                if item["name"] != "solicitudes":
                    carpetas.append(item["name"])
    except Exception as e:
        print("❌ Error al listar archivos:", e)
 
    carpetas_full_paths = {carpeta: f"{carpeta_actual}/{carpeta}".strip("/") for carpeta in carpetas}
    carpeta_padre = "/".join(carpeta_actual.split("/")[:-1]) if carpeta_actual else ""
    return render(request, "procesos.html", {
        "carpeta_actual": carpeta_actual,
        "carpeta_padre": carpeta_padre,
        "url_archivo": url_archivo,
        "archivos": archivos,
        "carpetas": carpetas,
        "carpetas_full_paths": carpetas_full_paths,
    })
 
 

@method_decorator(permiso_requerido('GESTIONAR_PERMISOS'), name='dispatch')
class CrearPermisoView(CreateView):
    model = Permiso
    form_class = PermisoForm
    template_name = 'crear_permiso.html'
    success_url = reverse_lazy('lista_permisos')
 
    def form_valid(self, form):
        codigo = form.cleaned_data.get('codigo')
        if Permiso.objects.filter(codigo__iexact=codigo).exists():
            form.add_error('codigo', 'Ya existe un permiso con este código.')
            return self.form_invalid(form)
        messages.success(self.request, "✅ Permiso creado correctamente.")
        return super().form_valid(form)
 
 
class ListaPermisosView(ListView):
    model = Permiso
    template_name = 'lista_permisos.html'
    context_object_name = 'permisos'
 
    def get_queryset(self):
        q = self.request.GET.get('q', '').strip()
        permisos = Permiso.objects.all()
        if q:
            permisos = permisos.filter(Q(codigo__icontains=q) | Q(nombre__icontains=q))
        return permisos.order_by('codigo')
 
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['q'] = self.request.GET.get('q', '').strip()
        return ctx
 
 
@require_GET
@login_required
@permiso_requerido('VER_SOLICITUDES_RECIBIDAS')
def api_contador_solicitudes_pendientes(request):
    qs = (SolicitudCodigo.objects
          .filter(receptor=request.user, estado='pendiente')
          .select_related('solicitante')
          .order_by('-id'))
    count = qs.count()
    data = {"count": count, "remitente": None, "ultimo_id": None, "titulo": None}
    if count:
        s = qs[0]
        u = s.solicitante
        nombre = (f"{(u.first_name or '').strip()} {(u.last_name or '').strip()}").strip() or u.get_full_name() or u.username
        data.update({
            "remitente": nombre,
            "ultimo_id": s.id,
            "titulo": s.titulo or s.get_tipo_solicitud_display(),
        })
    return JsonResponse(data)
 
 
class EditarPerfilYPermisosUsuarioView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    form_class = PerfilYPermisosUsuarioForm
    template_name = 'asignar_permisos_usuario.html'
    success_url = reverse_lazy('usuarios_ad')
 
    def form_valid(self, form):
        response = super().form_valid(form)
        new_first = (form.cleaned_data.get('first_name') or "").strip()
        new_last = (form.cleaned_data.get('last_name') or "").strip()
        new_base = f"{new_first} {new_last}".strip()
        try:
            builder = getattr(form, "_build_unique_username")
        except AttributeError:
            def builder(base, user_pk=None):
                base = base or (form.cleaned_data.get('email','').split('@')[0] or 'usuario')
                i, username = 1, base
                qs = CustomUser.objects.exclude(pk=self.object.pk) if self.object.pk else CustomUser.objects.all()
                while qs.filter(username=username).exists():
                    username = f"{base} {i}"; i += 1
                return username
        forced_username = builder(new_base, user_pk=self.object.pk)
        if self.object.username != forced_username:
            self.object.username = forced_username
            self.object.save(update_fields=["username"])
        return response
 

from django.db import transaction
from apps.sap.models import UDM

 
 

def _get_default_udm():
    """
    Retorna una UDM por defecto.
    Intenta 'UN' y si no existe toma la primera disponible.
    Si no hay ninguna UDM, retorna None.
    """
    return UDM.objects.filter(nombre__iexact="UN").first() or UDM.objects.first()
 
 

from apps.usuarios.forms import ProduccionDetalleForm, ProduccionHeaderForm
 
def _get_default_udm():
    return UDM.objects.filter(nombre__iexact="UN").first() or UDM.objects.first()
 
 
@method_decorator(permiso_requerido('SOLICITUD_CODIGO'), name='dispatch')
class SolicitudProduccionCreateView(LoginRequiredMixin, View):
    """
    Crea una Solicitud de tipo 'produccion' con UN (1) Detalle.
    Usuario elige receptor y empresa. Sin formset ni adjuntos.
    """
    template_name = 'solicitud_produccion_form.html'
    success_url = reverse_lazy('panel_admin_usuarios')
 
    def get(self, request):
        header_form = ProduccionHeaderForm()
        detail_form = ProduccionDetalleForm()
        solicitudes_enviadas = (SolicitudCodigo.objects
                                .filter(solicitante=request.user)
                                .order_by('-fecha_creacion'))
        return render(request, self.template_name, {
            'header_form': header_form,
            'form': detail_form,
            'solicitudes_enviadas': solicitudes_enviadas,
            'usuario': request.user
        })
 
    @transaction.atomic
    def post(self, request):
        header_form = ProduccionHeaderForm(request.POST)
        detail_form = ProduccionDetalleForm(request.POST)
 
        if not (header_form.is_valid() and detail_form.is_valid()):
            messages.error(request, "⚠️ Revisa los campos: faltan datos en la cabecera o el detalle.")
            solicitudes_enviadas = (SolicitudCodigo.objects
                                    .filter(solicitante=request.user)
                                    .order_by('-fecha_creacion'))
            return render(request, self.template_name, {
                'header_form': header_form,
                'form': detail_form,
                'solicitudes_enviadas': solicitudes_enviadas,
                'usuario': request.user
            })
 
        # Validar UDM antes de crear cabecera (tu modelo lo exige)
        udm_default = _get_default_udm()
        if not udm_default:
            messages.error(request, "⚠️ No hay UDM configuradas. Crea al menos una (por ejemplo, 'UN').")
            solicitudes_enviadas = (SolicitudCodigo.objects
                                    .filter(solicitante=request.user)
                                    .order_by('-fecha_creacion'))
            return render(request, self.template_name, {
                'header_form': header_form,
                'form': detail_form,
                'solicitudes_enviadas': solicitudes_enviadas,
                'usuario': request.user
            })
 
        # 1) Cabecera: receptor seleccionado por el usuario + empresa
        solicitud = SolicitudCodigo.objects.create(
            solicitante=request.user,
            receptor=header_form.cleaned_data["receptor"],
            empresa=header_form.cleaned_data["empresa"],
            tipo_solicitud='produccion',
            estado='pendiente',
        )
 
        # 2) Detalle desde el form
        detalle_kwargs = detail_form.build_detalle_kwargs()
        detalle_kwargs["udm"] = udm_default
 

        if detail_form.cleaned_data.get("sin_sku"):
            detalle_kwargs["sku_proveedor"] = ""
        else:
            detalle_kwargs.setdefault("sku_proveedor", "")
        if detail_form.cleaned_data.get("sin_codigo"):
            detalle_kwargs["sku_fabricante"] = ""
        else:
            detalle_kwargs.setdefault("sku_fabricante", "")
 

        tipo_ph = detail_form.cleaned_data.get("tipo_padre_hijo")
        solicitud.mensaje = (solicitud.mensaje or "") + f"\n[Producción] Estructura: {tipo_ph}"
        solicitud.save(update_fields=['mensaje'])
 
        # 3) Crear el ÚNICO detalle
        DetalleCodigo.objects.create(solicitud=solicitud, **detalle_kwargs)
 
        messages.success(request, "✅ Solicitud de Producción creada correctamente.")
        return redirect(self.success_url)