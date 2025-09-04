# apps/tickets/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.db import transaction
from django.core.paginator import Paginator
from django.utils.dateparse import parse_date
from django.http import HttpResponseRedirect, Http404

from apps.utils.supabase_storage import SupabaseStorage
from apps.usuarios.models import CustomUser
from apps.permisos.decorators import permiso_requerido

from .models import Ticket, TicketMensaje, TicketAdjunto
from .forms import TicketForm, TicketMensajeForm

import re


# ===== Helpers =====

def _es_agente(user):
    """Determina si el usuario es de soporte/mesa TI."""
    return (
        user.has_perm('permisos.TICKETS_VER_TODOS') or
        user.has_perm('permisos.TICKETS_RESPONDER') or
        user.has_perm('permisos.TICKETS_GESTIONAR')
    )

def _esta_bloqueado(ticket: Ticket) -> bool:
    """Bloquea respuestas/adjuntos si el ticket está resuelto o cerrado."""
    return ticket.estado in ('resuelto', 'cerrado')

def _safe_filename(name: str) -> str:
    """Nombre de archivo seguro (sin espacios raros/acentos)."""
    name = re.sub(r'[^\w.\-]+', '_', name).strip('._')
    return name or 'archivo'

def _ruta_adjunto_ticket(ticket_id, filename: str) -> str:
    """Ruta lógica en el bucket: tickets/{id}/adjuntos/{filename}."""
    return f"tickets/{ticket_id}/adjuntos/{_safe_filename(filename)}"

def _adjuntos_ctx(adjuntos_queryset):
    """
    Convierte adjuntos a dict, agregando URL pública desde Supabase.
    Mapea 'fecha_subida' desde el campo 'fecha' del modelo.
    """
    storage = SupabaseStorage()  # usa el bucket por defecto (ej. "media")
    ctx = []
    for a in adjuntos_queryset:
        url = None
        try:
            if a.ruta:
                url = storage.get_public_url(a.ruta)
        except Exception:
            url = None
        ctx.append({
            "id": a.id,
            "nombre": getattr(a, "nombre", "") or "Archivo",
            "ruta": getattr(a, "ruta", ""),
            "url": url,
            "subido_por": a.subido_por,
            "fecha_subida": getattr(a, "fecha", None),  # usar 'fecha' del modelo
        })
    return ctx


# ===== LISTA general (mixta; restringe si no es agente) =====

@login_required
def lista_tickets(request):
    user = request.user

    if not (user.has_perm('permisos.TICKETS_VER_TODOS') or user.has_perm('permisos.TICKETS_CREAR')):
        messages.error(request, "No tienes permiso para el módulo de tickets.")
        return redirect('panel_admin_usuarios')

    q = request.GET.get('q', '').strip()
    estado = request.GET.get('estado', '')
    propios = request.GET.get('propios', '')
    asignados = request.GET.get('asignados', '')

    tickets = Ticket.objects.all().order_by('-fecha_actualizacion')

    if not _es_agente(user):
        tickets = tickets.filter(Q(solicitante=user) | Q(asignado_a=user))
    else:
        if propios == '1':
            tickets = tickets.filter(solicitante=user)
        if asignados == '1':
            tickets = tickets.filter(asignado_a=user)

    if q:
        tickets = tickets.filter(Q(titulo__icontains=q) | Q(descripcion__icontains=q))
    if estado:
        tickets = tickets.filter(estado=estado)

    return render(request, 'lista.html', {
        'tickets': tickets,
        'q': q,
        'f_estado': estado,
        'propios': propios,
        'asignados': asignados,
        'es_agente': _es_agente(user),
    })


# ===== SOLICITAR AYUDA (crear + ver mis solicitudes en misma vista) =====
@login_required
def solicitar_ayuda(request):
    """
    - GET ?tab=crear (default): muestra CTA y abre form si ?new=1 o hay errores.
    - POST: crea ticket, sube adjuntos a tickets/{id}/adjuntos/, redirige a ?ok=1
    - GET ?tab=lista: muestra tabla filtrable con paginación.
    """
    tab = request.GET.get('tab', 'crear')

    # --- CREAR (POST)
    if request.method == 'POST':
        form = TicketForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                t = form.save(commit=False)
                t.solicitante = request.user
                t.prioridad = getattr(t, 'prioridad', None) or 'media'
                t.estado = getattr(t, 'estado', None) or 'abierto'
                if hasattr(t, 'asignado_a'):
                    t.asignado_a = None
                t.save()

                # Adjuntos múltiples
                archivos = request.FILES.getlist('archivos')
                if archivos:
                    storage = SupabaseStorage()
                    for f in archivos:
                        ruta = _ruta_adjunto_ticket(t.id, f.name)
                        storage._save(ruta, f)
                        es_img = (f.content_type or "").startswith("image/")
                        TicketAdjunto.objects.create(
                            ticket=t,
                            tipo='imagen' if es_img else 'documento',
                            ruta=ruta,
                            nombre=f.name,
                            subido_por=request.user,
                        )

                # Primer mensaje desde la descripción (opcional)
                desc = (t.descripcion or '').strip()
                if desc:
                    TicketMensaje.objects.create(
                        ticket=t, autor=request.user, mensaje=desc, publico=True
                    )

            return redirect(f"{request.path}?ok=1")
        else:
            messages.error(request, "Revisa los campos del formulario.")
        tab = 'crear'
    else:
        form = TicketForm()

    # --- Mis tickets recientes
    mis_tickets = (
        Ticket.objects.filter(solicitante=request.user)
        .select_related('asignado_a')
        .order_by('-fecha_actualizacion', '-fecha_creacion')[:20]
    )
    for tk in mis_tickets:
        tk.ultimo_mensaje = (
            TicketMensaje.objects
            .filter(ticket=tk, publico=True)
            .select_related('autor')
            .order_by('-fecha')
            .first()
        )

    # --- Pestaña LISTA con filtros/paginación
    q = request.GET.get('q', '').strip()
    estado = request.GET.get('estado', '').strip()
    desde_str = request.GET.get('desde', '').strip()
    hasta_str = request.GET.get('hasta', '').strip()
    desde = parse_date(desde_str) if desde_str else None
    hasta = parse_date(hasta_str) if hasta_str else None

    tickets_qs = (
        Ticket.objects.filter(solicitante=request.user)
        .order_by('-fecha_actualizacion', '-fecha_creacion')
    )
    if q:
        tickets_qs = tickets_qs.filter(Q(titulo__icontains=q) | Q(descripcion__icontains=q))
    if estado:
        tickets_qs = tickets_qs.filter(estado=estado)
    if desde:
        tickets_qs = tickets_qs.filter(fecha_actualizacion__date__gte=desde)
    if hasta:
        tickets_qs = tickets_qs.filter(fecha_actualizacion__date__lte=hasta)

    try:
        per_page = max(1, min(50, int(request.GET.get('pp', 15))))
    except ValueError:
        per_page = 15

    paginator = Paginator(tickets_qs, per_page)
    page_obj = paginator.get_page(request.GET.get('page'))
    elided_range = paginator.get_elided_page_range(
        number=page_obj.number, on_each_side=1, on_ends=1
    )

    for tk in page_obj.object_list:
        tk.ultimo_mensaje = (
            TicketMensaje.objects
            .filter(ticket=tk, publico=True)
            .select_related('autor')
            .order_by('-fecha')
            .first()
        )

    base_qs = request.GET.copy()
    base_qs.pop('page', None)
    base_qs.pop('tab', None)
    base_qs = base_qs.urlencode()

    return render(request, 'solicitar_ayuda.html', {
        'form': form,
        'mis_tickets': mis_tickets,
        'tab': tab,
        'page_obj': page_obj,
        'paginator': paginator,
        'elided_range': elided_range,
        'q': q,
        'f_estado': estado,
        'desde': desde_str,
        'hasta': hasta_str,
        'base_qs': base_qs,
        'estados': Ticket.ESTADOS,
    })


# ===== DETALLE del usuario (propietario) =====
@login_required
def mi_ticket_detalle(request, pk):
    """Detalle para el solicitante: conversación + responder. Sin gestión."""
    ticket = get_object_or_404(Ticket, pk=pk, solicitante=request.user)

    mensajes = (
        TicketMensaje.objects
        .filter(ticket=ticket, publico=True)
        .select_related('autor')
        .order_by('fecha')
    )
    adjuntos_ctx = _adjuntos_ctx(ticket.adjuntos.all())

    if request.method == 'POST':
        # Bloquea respuestas/adjuntos si resuelto o cerrado
        if _esta_bloqueado(ticket):
            messages.error(request, "El ticket está resuelto/cerrado; no se pueden agregar respuestas ni adjuntos.")
            return redirect('mi_ticket_detalle', pk=ticket.pk)

        form_msg = TicketMensajeForm(request.POST, request.FILES)
        if form_msg.is_valid():
            with transaction.atomic():
                msg = form_msg.save(commit=False)
                msg.ticket = ticket
                msg.autor = request.user
                msg.publico = True
                msg.save()

                archivos = request.FILES.getlist('archivos')
                if archivos:
                    storage = SupabaseStorage()
                    for f in archivos:
                        ruta = _ruta_adjunto_ticket(ticket.id, f.name)
                        storage._save(ruta, f)
                        es_img = (f.content_type or "").startswith("image/")
                        TicketAdjunto.objects.create(
                            ticket=ticket,
                            tipo='imagen' if es_img else 'documento',
                            ruta=ruta,
                            nombre=f.name,
                            subido_por=request.user,
                        )

                ticket.save()
            messages.success(request, "Mensaje enviado.")
            return redirect('mi_ticket_detalle', pk=ticket.pk)
        else:
            messages.error(request, "Revisa tu mensaje.")
    else:
        form_msg = TicketMensajeForm()

    return render(request, 'mi_ticket_detalle.html', {
        'ticket': ticket,
        'mensajes': mensajes,
        'adjuntos': adjuntos_ctx,
        'form_msg': form_msg,
        'puede_responder': not _esta_bloqueado(ticket),
    })


# ===== BANDEJA (solo agentes con permiso) =====
@login_required
@permiso_requerido('TICKETS_ACCESO_MENU')
def tickets_bandeja(request):
    """
    Bandeja de tickets para agentes.
    - Requiere el permiso único: tickets.TICKETS_ACCESO_MENU
    """
    q = request.GET.get('q', '').strip()
    estado = request.GET.get('estado', '')
    solo_abiertos = request.GET.get('abiertos', '1')

    tickets = Ticket.objects.all().select_related(
        'solicitante', 'asignado_a'
    ).order_by('-fecha_actualizacion')

    if solo_abiertos == '1':
        tickets = tickets.exclude(estado='cerrado')

    if estado:
        tickets = tickets.filter(estado=estado)

    if q:
        tickets = tickets.filter(Q(titulo__icontains=q) | Q(descripcion__icontains=q))

    return render(request, 'tickets_bandeja.html', {
        'tickets': tickets,
        'q': q,
        'f_estado': estado,
        'solo_abiertos': solo_abiertos,
    })


# ===== DETALLE (agentes) =====
@login_required
def tickets_detalle(request, pk):
    """Detalle interno para TI: puede gestionar y responder."""
    user = request.user
    if not _es_agente(user):
        messages.error(request, "No tienes permiso para ver este ticket.")
        return redirect('tickets_lista')  # nombre existente

    ticket = get_object_or_404(Ticket, pk=pk)

    mensajes = (
        TicketMensaje.objects
        .filter(ticket=ticket)  # agentes ven todos
        .select_related('autor')
        .order_by('fecha')
    )
    adjuntos_ctx = _adjuntos_ctx(ticket.adjuntos.all())

    puede_gestionar = user.has_perm('permisos.TICKETS_GESTIONAR')
    usuarios_asignables = CustomUser.objects.all().order_by('first_name', 'last_name', 'username') if puede_gestionar else []

    if request.method == 'POST' and 'mensaje' in request.POST:
        # Bloquea respuestas/adjuntos si resuelto o cerrado
        if _esta_bloqueado(ticket):
            messages.error(request, "El ticket está resuelto/cerrado; no se pueden agregar respuestas ni adjuntos.")
            return redirect('tickets_detalle', pk=ticket.pk)

        if not (user.has_perm('permisos.TICKETS_RESPONDER') or puede_gestionar):
            messages.error(request, "No tienes permiso para responder.")
            return redirect('tickets_detalle', pk=ticket.pk)

        form_msg = TicketMensajeForm(request.POST, request.FILES)
        if form_msg.is_valid():
            with transaction.atomic():
                msg = form_msg.save(commit=False)
                msg.ticket = ticket
                msg.autor = user
                msg.publico = True
                msg.save()

                archivos = request.FILES.getlist('archivos')
                if archivos:
                    storage = SupabaseStorage()
                    for f in archivos:
                        ruta = _ruta_adjunto_ticket(ticket.id, f.name)
                        storage._save(ruta, f)
                        es_img = (f.content_type or "").startswith("image/")
                        TicketAdjunto.objects.create(
                            ticket=ticket,
                            tipo='imagen' if es_img else 'documento',
                            ruta=ruta,
                            nombre=f.name,
                            subido_por=user
                        )

                ticket.save()
            messages.success(request, "Respuesta enviada.")
            return redirect('tickets_detalle', pk=ticket.pk)
        else:
            messages.error(request, "Revisa el formulario de respuesta.")
    else:
        form_msg = TicketMensajeForm()

    return render(request, 'tickets_detalle.html', {
        'ticket': ticket,
        'mensajes': mensajes,
        'adjuntos': adjuntos_ctx,
        'form_msg': form_msg,
        'puede_gestionar': puede_gestionar,
        'usuarios_asignables': usuarios_asignables,
        'puede_responder': (not _esta_bloqueado(ticket)) and (user.has_perm('permisos.TICKETS_RESPONDER') or puede_gestionar),
    })


# ===== Cambiar estado/asignar (solo gestionar) =====
@login_required
def tickets_cambiar_estado(request, pk):
    user = request.user
    if not user.has_perm('permisos.TICKETS_GESTIONAR'):
        messages.error(request, "No tienes permiso para gestionar tickets.")
        return redirect('tickets_detalle', pk=pk)

    ticket = get_object_or_404(Ticket, pk=pk)
    nuevo_estado = request.POST.get('estado')
    asignado_id = request.POST.get('asignado_a')

    if nuevo_estado and nuevo_estado in dict(Ticket.ESTADOS):
        ticket.estado = nuevo_estado
    if asignado_id:
        ticket.asignado_a = CustomUser.objects.filter(pk=asignado_id).first()
    else:
        ticket.asignado_a = None

    ticket.save()
    messages.success(request, "Ticket actualizado.")
    return redirect('tickets_detalle', pk=ticket.pk)


# ===== Ver adjunto (permisos + redirección a URL pública/firmada) =====
@login_required
def adjunto_ver(request, adjunto_id: int):
    adj = get_object_or_404(TicketAdjunto, pk=adjunto_id)
    ticket = adj.ticket
    user = request.user

    es_autor = (ticket.solicitante_id == user.id)
    es_asignado = (getattr(ticket, "asignado_a_id", None) == user.id)
    es_agente = _es_agente(user)
    if not (es_autor or es_asignado or es_agente):
        messages.error(request, "No tienes permiso para ver este adjunto.")
        return redirect('mi_ticket_detalle', pk=ticket.pk)

    storage = SupabaseStorage()  # usa tu bucket por defecto (p. ej. "media")
    try:
        url = storage.get_public_url(adj.ruta) if adj.ruta else None
        # si tienes método firmado: url = storage.get_signed_url(adj.ruta, 3600)
    except Exception:
        url = None

    if not url:
        raise Http404("Archivo no disponible.")

    return HttpResponseRedirect(url)
