import mimetypes
from django.core.files.storage import Storage
from django.conf import settings
from django.core.files.base import ContentFile
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
        content.open()
        data = content.read()

        mime_type = mimetypes.guess_type(name)[0] or 'application/octet-stream'
        print(f"📤 Subiendo {name} a bucket {self.bucket} (sobrescribiendo si existe)...")

        try:
            # 🔄 Usamos 'update' para sobrescribir si ya existe
            self.client.storage.from_(self.bucket).update(
                path=name,
                file=data,
                file_options={"content-type": mime_type}
            )
        except Exception as e:
            print("❌ Error al subir a Supabase:", e)
            raise e

        return name

    def _open(self, name, mode='rb'):
        print(f"📥 Descargando {name} desde SupabaseStorage (modo: {mode})")
        try:
            response = self.client.storage.from_(self.bucket).download(name)
            return ContentFile(response)
        except Exception as e:
            print("❌ Error al descargar desde Supabase:", e)
            raise e

    def exists(self, name):
        try:
            response = self.client.storage.from_(self.bucket).list()
            filenames = [file['name'] for file in response or []]
            return name in filenames
        except Exception as e:
            print("❌ Error en exists:", e)
            return False

    def url(self, name):
        return f"{self.url}/storage/v1/object/public/{self.bucket}/{name}"

    def get_public_url(self, path):
        """Devuelve la URL pública completa del archivo en Supabase"""
        return f"{self.url}/storage/v1/object/public/{self.bucket}/{path}"
