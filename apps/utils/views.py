# apps/utils/views.py
import os
from django.http import JsonResponse
from django.views import View
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from apps.utils.supabase_storage import SupabaseStorage

class TestSupabaseUploadView(View):
    def get(self, request):
        response_data = {}

        # Verificamos las variables de entorno
        response_data['SUPABASE_URL'] = os.getenv('SUPABASE_URL')
        response_data['SUPABASE_KEY_exists'] = bool(os.getenv('SUPABASE_KEY'))
        response_data['SUPABASE_BUCKET'] = os.getenv('SUPABASE_BUCKET')

        # Subimos archivo de prueba
        try:
            file_name = "uploads/test_render.txt"
            file_content = ContentFile(b"Contenido de prueba desde Render")
            path = default_storage.save(file_name, file_content)

            response_data['archivo_subido'] = path
            response_data['url_archivo'] = default_storage.url(path)

            # Validamos si el archivo existe en el bucket
            supa = SupabaseStorage()
            response_data['existe_en_supabase'] = supa.exists(path)

        except Exception as e:
            response_data['error'] = str(e)

        return JsonResponse(response_data)
