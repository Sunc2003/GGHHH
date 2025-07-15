# apps.usuarios.decorators.py
from django.core.exceptions import PermissionDenied
from functools import wraps

def cargo_requerido(lista_cargos):
    def decorador(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                raise PermissionDenied("Usuario no autenticado")

            if request.user.cargo and request.user.cargo.nombre in lista_cargos:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied("No tienes permiso para acceder a esta vista")
        return _wrapped_view
    return decorador


def area_requerida(nombre_area):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                raise PermissionDenied("Debes iniciar sesión.")
            if not request.user.area or request.user.area.nombre_area != nombre_area:
                raise PermissionDenied("No tienes permisos para esta acción.")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator