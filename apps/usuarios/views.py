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
from .forms import CambiarEstadoForm, PerfilYPermisosUsuarioForm
import os
from apps.utils.supabase_storage import SupabaseStorage
from decimal import Decimal
from django.contrib import messages
from django.views.generic.detail import DetailView
from django.views.generic.base import TemplateResponseMixin
from django.forms import formset_factory
from django.db.models import Q
from django.core.files.storage import default_storage
import re
from urllib.parse import quote
from django.views.decorators.csrf import csrf_exempt
from django.core.files.base import ContentFile
from django.views.generic import ListView
from django.utils.timezone import now
from django import template
from django.db.models import F, Avg, ExpressionWrapper, DurationField
from django.views.generic import CreateView, ListView
from django.urls import reverse_lazy
from apps.permisos.models import Permiso
from apps.permisos.forms import PermisoForm
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test
from django.core.cache import cache
from apps.usuarios.models import CustomUser, SolicitudCodigo
from django.utils.http import url_has_allowed_host_and_scheme
from django.urls import reverse
from urllib.parse import urlparse
from django.urls import resolve, Resolver404 
 
class IniciarSesionView(LoginView):
    template_name = 'login.html'
 
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Usuario'})
        form.fields['password'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Contraseña'})
        return form
 
    def get_success_url(self):
        # 1) Si viene ?next= y es seguro Y EXISTE en tus urls, respétalo
        next_url = self.request.POST.get('next') or self.request.GET.get('next')
        if next_url and url_has_allowed_host_and_scheme(next_url, {self.request.get_host()}):
            path = urlparse(next_url).path
            try:
                resolve(path)   # ¿existe esa ruta?
                return next_url
            except Resolver404:
                pass   # ignoramos next inválido (/usuarios/panel/ por ejemplo)
 
        # 2) Si no hay next válido, SIEMPRE al panel real
        return reverse('panel_admin_usuarios')   
        
@method_decorator(permiso_requerido('CREACION_USUARIO'), name='dispatch')
class RegistroUsuarioView(CreateView):
    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = 'registro.html'
    success_url = reverse_lazy('login')  # Redirige al login después de registrarse
 
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
 
 



##@user_passes_test(es_admin)
def panel_admin_usuarios(request):
    usuarios = CustomUser.objects.all()
 
    # Marcar usuarios en línea desde cache
    for u in usuarios:
        u.en_linea = bool(cache.get(f"online:{u.id}", False))
 
    # 🔹 Solicitudes recibidas por el administrador
    solicitudes_recibidas = SolicitudCodigo.objects.filter(receptor=request.user)
    total_recibidas = solicitudes_recibidas.count()
    pendientes = solicitudes_recibidas.filter(estado='pendiente').count()
    completadas = total_recibidas - pendientes
 
    # 🔹 Tiempo promedio de respuesta
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
 
    # 🔹 KPI para usuarios normales
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


################################################################################################
 
 
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
        
        
@method_decorator(permiso_requerido('VER_SOLICITUDES_RECIBIDAS'), name='dispatch')
class SolicitudesRecibidasView(LoginRequiredMixin, ListView):
    model = SolicitudCodigo
    template_name = 'solicitudes_recibidas.html'
    context_object_name = 'solicitudes_recibidas'
    paginate_by = 25  # opcional

    def get_queryset(self):
        qs = SolicitudCodigo.objects.filter(
            receptor=self.request.user,
            estado='pendiente'
        )

        # --- filtros desde GET ---
        solicitante_id = self.request.GET.get('solicitante', '').strip()
        orden = self.request.GET.get('orden', 'antiguas')  # 'antiguas' (default) o 'recientes'

        # Filtro por solicitante (si viene)
        if solicitante_id:
            qs = qs.filter(solicitante_id=solicitante_id)

        # Orden
        if orden == 'recientes':
            qs = qs.order_by('-fecha_creacion')
        else:
            qs = qs.order_by('fecha_creacion')  # antiguas primero

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Para el select de solicitantes: solo los que te han enviado algo
        solicitantes_ids = (SolicitudCodigo.objects
                            .filter(receptor=self.request.user)
                            .values_list('solicitante_id', flat=True)
                            .distinct())
        solicitantes = CustomUser.objects.filter(id__in=solicitantes_ids).order_by('first_name', 'last_name', 'username')

        context['solicitantes'] = solicitantes
        context['filtro_solicitante'] = self.request.GET.get('solicitante', '')
        context['filtro_orden'] = self.request.GET.get('orden', 'antiguas')
        return context  
        
        
method_decorator(permiso_requerido('VER_SOLICITUDES_RECIBIDA'), name='dispatch')
class SolicitudDetailView(DetailView):
    model = SolicitudCodigo
    template_name = 'solicitud_detalle.html'
 
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
 
        # Adjuntos
        documentos = self.object.adjuntos.filter(tipo='documento')
        imagenes = self.object.adjuntos.filter(tipo='imagen')
 
        context['documentos'] = documentos
        context['imagenes'] = imagenes
 
        # Productos + cálculo
        productos = self.object.detalles.all()
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
 
        # ✅ Agregar el formulario si el usuario es el receptor y está pendiente
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
        solicitud.fecha_respuesta = now()  # ✅ Guardamos fecha de respuesta
        solicitud.comentario_estado = form.cleaned_data.get('comentario_estado')
        solicitud.save()
        return super().form_valid(form)
 
 
    def get_success_url(self):
        return reverse_lazy('detalle_solicitud', kwargs={'pk': self.object.pk})  # <-- CORRECTO
 
 
 
@method_decorator(permiso_requerido('VER_AD'), name='dispatch')
class UsuariosADListView(ListView):
    model = CustomUser
    template_name = 'usuarios_ad.html'
    context_object_name = 'usuarios'
    paginate_by = 10
 
    def get_queryset(self):
        qs = super().get_queryset()
 
        # Filtros desde el formulario
        area_id = self.request.GET.get('area', '')
        cargo_id = self.request.GET.get('cargo', '')
        filtro_nombre = self.request.GET.get('q', '').strip()
        filtro_usuario_ad = self.request.GET.get('usuario_ad', '').strip()
 
        # Aplicar filtros si están presentes
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
    url_archivo = None
    archivos = []
    carpetas = []
 
    # CREAR CARPETA o SUBIR ARCHIVO
    if request.method == "POST":
        # 📁 CREAR NUEVA CARPETA dentro de carpeta_actual
        if "nueva_carpeta" in request.POST:
            nombre_carpeta = request.POST["nueva_carpeta"].strip("/")
            if nombre_carpeta:
                ruta_carpeta = f"{carpeta_actual}/{nombre_carpeta}".strip("/")
                placeholder = ContentFile(b"")
                try:
                    storage._save(f"{ruta_carpeta}/.emptyFolderPlaceholder", placeholder)
                except Exception as e:
                    print("❌ Error al crear carpeta:", e)
 
        # 📤 SUBIR ARCHIVO dentro de carpeta_actual
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
 
    # LISTAR ARCHIVOS EN CARPETA ACTUAL
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
 
    carpetas_full_paths = {
        carpeta: f"{carpeta_actual}/{carpeta}".strip("/")
        for carpeta in carpetas
    }
 
    carpeta_padre = "/".join(carpeta_actual.split("/")[:-1]) if carpeta_actual else ""
 
    return render(request, "procesos.html", {
        "carpeta_actual": carpeta_actual,
        "carpeta_padre": carpeta_padre,
        "url_archivo": url_archivo,
        "archivos": archivos,
        "carpetas": carpetas,
        "carpetas_full_paths": carpetas_full_paths,
    })
 
class EditarPerfilYPermisosUsuarioView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    form_class = PerfilYPermisosUsuarioForm
    template_name = 'asignar_permisos_usuario.html'
    context_object_name = 'usuario'
    success_url = reverse_lazy('usuarios_ad')
 
    def form_valid(self, form):
        response = super().form_valid(form)
        form.instance.permisos_directos.set(form.cleaned_data['permisos_directos'])  # Actualiza los permisos
        return response
    
 
 
 
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
            permisos = permisos.filter(
                Q(codigo__icontains=q) |
                Q(nombre__icontains=q)
            )
        return permisos.order_by('codigo')
 
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['q'] = self.request.GET.get('q', '').strip()
        return ctx
    



@require_GET
@login_required
@permiso_requerido('VER_SOLICITUDES_RECIBIDAS')
def api_contador_solicitudes_pendientes(request):
    """
    Devuelve:
      - count: total pendientes para el receptor actual
      - remitente: nombre del solicitante de la ÚLTIMA solicitud pendiente creada
      - ultimo_id: id de esa última solicitud (para linkear)
      - titulo: título de la última solicitud (opcional)
    """
    qs = (SolicitudCodigo.objects
          .filter(receptor=request.user, estado='pendiente')
          .select_related('solicitante')
          .order_by('-id'))  # más confiable que fecha

    count = qs.count()
    data = {"count": count, "remitente": None, "ultimo_id": None, "titulo": None}

    if count:
        s = qs[0]
        u = s.solicitante
        # nombre “bonito” con varios fallbacks
        nombre = (f"{(u.first_name or '').strip()} {(u.last_name or '').strip()}").strip()
        if not nombre:
            nombre = (u.get_full_name() or "").strip()
        if not nombre:
            nombre = u.username

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
        # deja que el form guarde primero
        response = super().form_valid(form)
 
        # compute y fuerza el username después de guardar (por si algo lo pisó)
        new_first = (form.cleaned_data.get('first_name') or "").strip()
        new_last  = (form.cleaned_data.get('last_name')  or "").strip()
        new_base  = f"{new_first} {new_last}".strip()
 
        # usa el helper del form para garantizar unicidad
        try:
            builder = getattr(form, "_build_unique_username")
        except AttributeError:
            # fallback mínimo
            def builder(base, user_pk=None):
                base = base or (form.cleaned_data.get('email','').split('@')[0] or 'usuario')
                from apps.usuarios.models import CustomUser
                i, username = 1, base
                qs = CustomUser.objects.exclude(pk=self.object.pk) if self.object.pk else CustomUser.objects.all()
                while qs.filter(username=username).exists():
                    username = f"{base} {i}"; i += 1
                return username
 
        forced_username = builder(new_base, user_pk=self.object.pk)
        print("DEBUG vista.force username =>", forced_username)
 
        # Sólo si cambió, persistimos
        if self.object.username != forced_username:
            self.object.username = forced_username
            # si tienes un save() de modelo que lo pisa, usa update() directo como último recurso:
            # type(self.object).objects.filter(pk=self.object.pk).update(username=forced_username)
            self.object.save(update_fields=["username"])
 
        return response 

