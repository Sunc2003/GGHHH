# apps/utils/urls.py
from django.urls import path
from .views import TestSupabaseUploadView
from .views import qr_png, mis_solicitudes_contador   # ⬅️ añade esto
from . import views # ⬅️ añade esto para qr_png
urlpatterns = [
    path('test-upload/', TestSupabaseUploadView.as_view(), name='test_upload'),
    path("qr/", qr_png, name="qr_png"),
    path("mis-solicitudes/contador/", mis_solicitudes_contador, name="mis_solicitudes_contador"),
    path("qr.png", views.qr_png, name="qr_png"),
]


