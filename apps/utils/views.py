from django.views import View
from django.http import JsonResponse
from django.core.files.base import ContentFile
from apps.utils.supabase_storage import SupabaseStorage

class TestSupabaseUploadView(View):
    def get(self, request):
        response_data = {}
        supa = SupabaseStorage()  # 👈 usamos directamente

        response_data['SUPABASE_URL'] = supa.url
        response_data['SUPABASE_KEY_exists'] = bool(supa.key)
        response_data['SUPABASE_BUCKET'] = supa.bucket

        try:
            file_name = "uploads/test_render.txt"
            file_content = ContentFile(b"Contenido desde Render")
            supa._save(file_name, file_content)  # 👈 forzamos supabase

            response_data['archivo_subido'] = file_name
            response_data['url_archivo'] = supa.url(file_name)
            response_data['existe_en_supabase'] = supa.exists(file_name)

        except Exception as e:
            response_data['error'] = str(e)

        return JsonResponse(response_data)
    


    # --- QR: contador de solicitudes del usuario ---
from io import BytesIO
import qrcode

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render

from apps.usuarios.models import SolicitudCodigo


@login_required
def qr_png(request):
    """
    Devuelve un PNG con un código QR que apunta a la URL indicada en ?data
    Ej: /utils/qr/?data=/utils/mis-solicitudes/contador/
    """
    data = (request.GET.get("data") or "").strip()
    if not data:
        return HttpResponseBadRequest("Falta el parámetro ?data")

    # Si es path relativo, conviértelo a URL absoluta
    if data.startswith("/"):
        data = request.build_absolute_uri(data)

    img = qrcode.make(data)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return HttpResponse(buf.getvalue(), content_type="image/png")


@login_required
def mis_solicitudes_contador(request):
    """
    Muestra cuántas solicitudes ha enviado el usuario logueado.
    """
    count = SolicitudCodigo.objects.filter(solicitante=request.user).count()
    return render(request, "mis_solicitudes_contador.html", {"count": count})


# apps/utils/views.py
from io import BytesIO
from django.http import HttpResponse, HttpResponseBadRequest
import qrcode

def qr_png(request):
    data = request.GET.get("data", "").strip()
    if not data:
        return HttpResponseBadRequest("Falta parámetro 'data'")
    qr = qrcode.QRCode(version=None, box_size=6, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return HttpResponse(buf.getvalue(), content_type="image/png")
