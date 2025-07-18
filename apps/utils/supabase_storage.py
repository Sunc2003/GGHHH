import os
from django.core.files.storage import Storage
from django.core.files.base import ContentFile
from supabase import create_client

class SupabaseStorage(Storage):
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")  # Usas esta en Render
        self.bucket = os.getenv("SUPABASE_BUCKET", "media")
        self.client = create_client(self.supabase_url, self.supabase_key)
        self.storage = self.client.storage().from_(self.bucket)

    def _save(self, name, content):
        path = name.replace("\\", "/")
        self.storage.upload(path, content.file, {
            "cacheControl": "3600",
            "upsert": True
        })
        return path

    def exists(self, name):
        path = name.replace("\\", "/")
        try:
            folder = path.rsplit("/", 1)[0] if "/" in path else ""
            files = self.storage.list(folder)
            return any(f["name"] == path.split("/")[-1] for f in files)
        except Exception:
            return False

    def url(self, name):
        path = name.replace("\\", "/")
        return self.storage.get_public_url(path)

    def delete(self, name):
        path = name.replace("\\", "/")
        self.storage.remove([path])

    def open(self, name, mode='rb'):
        path = name.replace("\\", "/")
        file_data = self.storage.download(path)
        return ContentFile(file_data)
