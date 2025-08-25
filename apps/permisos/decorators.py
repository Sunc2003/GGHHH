# apps/permisos/decorators.py
from functools import wraps
from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
 
def permiso_requerido(codigo_permiso):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            # 1) No autenticado → login
            if not request.user.is_authenticated:
                return redirect_to_login(
                    request.get_full_path(),
                    login_url=settings.LOGIN_URL
                )
 
            # 2) Superuser (y opcionalmente staff) pasan
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
 
            # 3) Verifica tu método real de permisos
            tiene = getattr(request.user, "tiene_permiso", lambda c: False)(codigo_permiso)
            if tiene:
                return view_func(request, *args, **kwargs)
 
            # 4) Autenticado pero sin permiso → 403, no login
            raise PermissionDenied
        return _wrapped
    return decorator