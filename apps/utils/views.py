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
    


    



from django.contrib.auth.decorators import login_required

from django.shortcuts import render

from apps.usuarios.models import SolicitudCodigo




@login_required
def mis_solicitudes_contador(request):
    """
    Muestra cuántas solicitudes ha enviado el usuario logueado.
    """
    count = SolicitudCodigo.objects.filter(solicitante=request.user).count()
    return render(request, "mis_solicitudes_contador.html", {"count": count})


