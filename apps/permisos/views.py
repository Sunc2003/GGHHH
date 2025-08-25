from django.views.generic import CreateView, UpdateView
from django.urls import reverse_lazy
from apps.permisos.models import Permiso
from apps.permisos.forms import PermisoForm, AsignarPermisosUsuarioForm
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.permisos.decorators import permiso_requerido
from django.utils.decorators import method_decorator
from apps.usuarios.models import CustomUser
from django.urls import reverse_lazy
from apps.usuarios.forms import PerfilYPermisosUsuarioForm


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



##@method_decorator(permiso_requerido('GESTIONAR_PERMISOS'), name='dispatch')
class AsignarPermisosUsuarioView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    form_class = PerfilYPermisosUsuarioForm   # <-- el form que recalcula username
    template_name = 'asignar_permisos_usuario.html'
    success_url = reverse_lazy('usuarios_ad')
 
    # DEBUG: ¿qué form está usando realmente?
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        print("DEBUG Form en uso:", form.__class__.__name__)
        return form
 
    # (opcional) ver que el save del form se está llamando al enviar:
    def form_valid(self, form):
        print("DEBUG form_valid llamado; username antes de save():", self.get_object().username)
        resp = super().form_valid(form)
        print("DEBUG username después de save():", self.object.username)
        return resp