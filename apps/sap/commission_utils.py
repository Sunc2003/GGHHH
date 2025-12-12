# apps/sap/commission_utils.py
from django.conf import settings
from decimal import Decimal, InvalidOperation
 
def _load_scheme_by_name(name: str):
    schemes = getattr(settings, "COMMISSION_SCHEMES", {})
    return schemes.get(name) or []
 
def get_user_scheme_name(user):
    """
    Devuelve el nombre del esquema asignado al usuario (según settings.COMMISSION_ASSIGNMENT).
    Acepta user object; intenta get_full_name, username y usuario_sap (si existe).
    """
    if not user:
        return getattr(settings, "COMMISSION_DEFAULT_SCHEME", None)
    full = getattr(user, "get_full_name", lambda: "")()
    username = getattr(user, "username", "")
    usuario_sap = getattr(user, "usuario_sap", "") if hasattr(user, "usuario_sap") else ""
 
    mapping = getattr(settings, "COMMISSION_ASSIGNMENT", {})
    candidates = [full, username, usuario_sap]
    for c in candidates:
        if not c:
            continue
        if c in mapping:
            return mapping[c]
    # fallback
    return getattr(settings, "COMMISSION_DEFAULT_SCHEME", None)
 
def get_brackets_for_user(user):
    name = get_user_scheme_name(user)
    return _load_scheme_by_name(name) or []
 
def calc_commission_value_from_pct(pct: float | str, user=None):
    """
    Dado un pct (%) devuelve el 'valor' de comisión según el esquema del user.
    pct puede venir como float o string; se intenta cast a Decimal/float.
    """
    try:
        pct_f = float(pct or 0)
    except (ValueError, TypeError):
        pct_f = 0.0
 
    brackets = get_brackets_for_user(user)
    for b in brackets:
        try:
            desde = float(b.get("desde", 0))
            hasta = float(b.get("hasta", 99999))
            valor = float(b.get("valor", 0))
        except Exception:
            continue
        if pct_f >= desde and pct_f <= hasta:
            return valor
    return 0.0