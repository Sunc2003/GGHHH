# permisos/urls.py
from django.urls import path
from apps.permisos.views import PermisoCreateView, AsignarPermisosUsuarioView

urlpatterns = [
    path('nuevo/', PermisoCreateView.as_view(), name='crear_permiso'),
    path('usuario/<int:pk>/asignar/', AsignarPermisosUsuarioView.as_view(), name='asignar_permisos_usuario'),
]
