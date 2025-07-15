# apps/permisos/decorators.py
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def permiso_requerido(codigo_permiso):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, "Debes iniciar sesión.")
                return redirect('login')
            if not request.user.tiene_permiso(codigo_permiso):
                messages.error(request, "No tienes permiso para acceder.")
                return redirect('panel_admin_usuarios')
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
