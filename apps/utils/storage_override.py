from django.core.files import storage
from apps.utils.supabase_storage import SupabaseStorage

# Sobrescribe la instancia global default_storage
storage.default_storage = SupabaseStorage()
print("✔️ default_storage forzado a SupabaseStorage")