# apps/tickets/templatetags/form_extras.py
from django import template

register = template.Library()

@register.filter
def add_class(field, css):
    """
    Agrega clases CSS al widget conservando las existentes.
    Uso: {{ form.campo|add_class:"form-control is-invalid" }}
    """
    attrs = field.field.widget.attrs.copy()
    current = attrs.get("class", "")
    attrs["class"] = (current + " " + css).strip()
    return field.as_widget(attrs=attrs)
