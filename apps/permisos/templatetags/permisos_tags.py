from django import template
 
register = template.Library()
 
@register.filter
def tiene_permiso(user, codigo_permiso):
    if hasattr(user, "tiene_permiso"):
        return user.tiene_permiso(codigo_permiso)
    return False