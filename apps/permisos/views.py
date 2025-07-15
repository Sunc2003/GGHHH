from django.views.generic import CreateView, UpdateView
from django.urls import reverse_lazy
from apps.permisos.models import Permiso
from apps.permisos.forms import PermisoForm, AsignarPermisosUsuarioForm
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.permisos.decorators import permiso_requerido
from django.utils.decorators import method_decorator
from apps.usuarios.models import CustomUser
from django.urls import reverse_lazy



@method_decorator(permiso_requerido('GESTIONAR_PERMISOS'), name='dispatch')
class PermisoCreateView(LoginRequiredMixin, CreateView):
    model = Permiso
    form_class = PermisoForm
    template_name = 'crear_permiso.html'
    success_url = reverse_lazy('crear_permiso')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['permisos'] = Permiso.objects.all().order_by('codigo')
        return context


##@method_decorator(permiso_requerido('GESTIONAR_PERMISOS'), name='dispatch')
class AsignarPermisosUsuarioView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    form_class = AsignarPermisosUsuarioForm
    template_name = 'asignar_permisos_usuario.html'
    success_url = reverse_lazy('usuarios_ad')