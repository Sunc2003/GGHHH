import mimetypes
import os
from django.core.files.storage import Storage
from django.conf import settings
from supabase import create_client

class SupabaseStorage(Storage):
    def __init__(self):
        self.client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        self.bucket = settings.SUPABASE_BUCKET

    def _save(self, name, content):
        content.open()
        data = content.read()
        content.close()
        mime_type = mimetypes.guess_type(name)[0] or 'application/octet-stream'
        self.client.storage.from_(self.bucket).upload(name, data, {"content-type": mime_type})
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
