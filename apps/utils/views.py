# apps/utils/views.py
from django.views import View
from django.http import HttpResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

class TestSupabaseUploadView(View):
    def get(self, request):
        name = 'test_render.txt'
        content = ContentFile(b'Subido desde Render!')
        try:
            path = default_storage.save(name, content)
            return HttpResponse(f'Subido correctamente: <a href="{default_storage.url(path)}">{path}</a>')
        except Exception as e:
            return HttpResponse(f'Error al subir: {e}')
