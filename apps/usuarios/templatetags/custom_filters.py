from django import template
import os
 
register = template.Library()
 
@register.filter(name='div')
def div(value, arg):
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError, TypeError):
        return ''
 
 
@register.filter
def basename(value, mode=None):
    """Extrae el último segmento de una ruta (carpeta o archivo).
    Si mode='up', devuelve la carpeta padre.
    """
    path = value.strip("/")
 
    if mode == "up":
        parts = path.split("/")
        return "/".join(parts[:-1])
    
    return os.path.basename(path)
 
@register.filter
def dict_get(dictionary, key):
    return dictionary.get(key)