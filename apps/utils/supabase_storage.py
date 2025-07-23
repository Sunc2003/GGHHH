import mimetypes
import os
from django.core.files.storage import Storage
from django.conf import settings
from supabase import create_client

class SupabaseStorage(Storage):
    def __init__(self):
        print("🔄 Inicializando SupabaseStorage")

        self.url = getattr(settings, "SUPABASE_URL", None)
        self.key = getattr(settings, "SUPABASE_KEY", None)
        self.bucket = getattr(settings, "SUPABASE_BUCKET", "media")

        print(f"📦 SUPABASE_URL: {self.url}")
        print(f"🔑 SUPABASE_KEY is set: {'Yes' if self.key else 'No'}")
        print(f"🪣 SUPABASE_BUCKET: {self.bucket}")

        if not all([self.url, self.key]):
            raise Exception("❌ Faltan variables de entorno para Supabase")

        self.client = create_client(self.url, self.key)
    def _save(self, name, content):
       print("🔄 _save() SupabaseStorage ejecutado con nombre:", name)
       content.open()
       data = content.read()
       content.close()
       mime_type = mimetypes.guess_type(name)[0] or 'application/octet-stream'
       response = self.client.storage.from_(self.bucket).upload(name, data, {"content-type": mime_type})
       print("✅ Respuesta de subida Supabase:", response)
       return name

    def url(self, name):
        return f"{settings.SUPABASE_URL}/storage/v1/object/public/{self.bucket}/{name}"

    def exists(self, name):
        try:
            response = self.client.storage.from_(self.bucket).list()
            filenames = [file['name'] for file in response or []]
            return name in filenames
        except Exception as e:
            print("Error en exists:", e)
            return False
