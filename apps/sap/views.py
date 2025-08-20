# apps/sap/views.py
from django.shortcuts import render
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.conf import settings
from apps.permisos.decorators import permiso_requerido
 
import requests
import time, hmac, hashlib
 
# ---- ENDPOINTS REMOTOS (ajusta si cambias el dominio) ----
NGROK_API_URL = "https://804103bbd425.ngrok-free.app/api/productos"
NGROK_API_SOCIOS = "https://804103bbd425.ngrok-free.app/api/socios"
 
# ---- HEADERS BASE (útiles para ngrok) ----
HEADERS_BASE = {
    "ngrok-skip-browser-warning": "true",
    "User-Agent": "DjangoClient/1.0",
    "accept": "application/json",
}
 
def _hmac_headers():
    """
    Genera los 3 headers requeridos por tu API:
      - X-API-KeyId
      - X-API-Timestamp (epoch en segundos)
      - X-API-Signature (HMAC-SHA256 de "KeyId.Timestamp" con API_KEY_SECRET)
    """
    key_id = getattr(settings, "API_KEY_ID", None)
    key_secret = getattr(settings, "API_KEY_SECRET", None)
    if not key_id or not key_secret:
        # Evita llamadas silenciosas si falta configuración
        raise RuntimeError("API_KEY_ID / API_KEY_SECRET no configurados en settings.py")
 
    ts = str(int(time.time()))
    sig = hmac.new(key_secret.encode(), f"{key_id}.{ts}".encode(), hashlib.sha256).hexdigest()
    return {
        **HEADERS_BASE,
        "X-API-KeyId": key_id,
        "X-API-Timestamp": ts,
        "X-API-Signature": sig,
    }
 
# ---------------------------------------------------------------------
# PRODUCTOS
# ---------------------------------------------------------------------
@login_required
@permiso_requerido('BUSCAR_PRODUCTOS_SAP')
def buscar_productos_remoto(request):
    termino = (request.GET.get("q") or "").strip()
    if termino == "":
        return JsonResponse({"productos": []})
 
    try:
        response = requests.get(
            NGROK_API_URL,
            params={"q": termino},
            headers=_hmac_headers(),
            timeout=int(getattr(settings, "API_TIMEOUT", 5)),
        )
        response.raise_for_status()
        data = response.json()
        return JsonResponse({"productos": data})
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response else 500
        body = e.response.text if e.response else str(e)
        return JsonResponse({"error": str(e), "response_text": body, "status_code": status}, status=status)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
 
@login_required
@permiso_requerido('BUSCAR_PRODUCTOS_SAP')
def buscador_productos_view(request):
    resultados = []
    termino = (request.GET.get("q") or "").strip()
    filtrar_stock = request.GET.get("con_stock", "") == "on"
 
    if termino:
        try:
            r = requests.get(
                NGROK_API_URL,
                params={"q": termino},
                headers=_hmac_headers(),
                timeout=int(getattr(settings, "API_TIMEOUT", 5)),
            )
            r.raise_for_status()
            productos = r.json()
 
            # opcional: calcula Disponible (si lo quieres en tu template)
            for p in productos:
                p.setdefault("StockTotal", p.get("StockTotal", 0) or 0)
                p.setdefault("Comprometido", p.get("Comprometido", 0) or 0)
                p["Disponible"] = (p["StockTotal"] - p["Comprometido"])
 
            resultados = [p for p in productos if p.get("StockTotal", 0) > 0] if filtrar_stock else productos
 
            if not resultados:
                resultados = [{
                    "Codigo": "No encontrado",
                    "Descripcion": "No se encontraron productos con ese término.",
                    "StockTotal": "N/A",
                    "Disponible": "N/A",
                    "Comprometido": "N/A",
                    "Pedido": "N/A",
                    "PrecioMinVta": "N/A"
                }]
 
        except requests.exceptions.RequestException as e:
            resultados = [{
                "Codigo": "Error",
                "Descripcion": str(e),
                "StockTotal": "N/A",
                "Disponible": "N/A",
                "Comprometido": "N/A",
                "Pedido": "N/A",
                "PrecioMinVta": "N/A"
            }]
 
    return render(request, "buscador_productos.html", {
        "termino": termino,
        "filtrar_stock": filtrar_stock,
        "resultados": resultados
    })
 
@login_required
@permiso_requerido('BUSCAR_PRODUCTOS_SAP')
def obtener_detalle_producto(request, itemcode):
    try:
        r = requests.get(
            f"{NGROK_API_URL}/{itemcode}",
            headers=_hmac_headers(),
            timeout=int(getattr(settings, "API_TIMEOUT", 5)),
        )
        r.raise_for_status()
        productos = r.json()
 
        if not productos:
            return JsonResponse({'error': 'Producto no encontrado'}, status=404)
 
        detalles_producto = {}
        for prod in productos:
            codigo = prod["Codigo"]
            if codigo not in detalles_producto:
                detalles_producto[codigo] = {
                    'Codigo': codigo,
                    'Descripcion': prod.get("Descripcion"),
                    'PrecioMinVta': prod.get("PrecioMinVta"),
                    'ProveedorPredeterminado': prod.get("ProveedorPredeterminado", "N/A"),
                    'SKUProveedor': prod.get("SKUProveedor", "N/A"),
                    'NombreProveedor': prod.get("NombreProveedor", "N/A"),
                    'UnidadMedida': prod.get("UnidadMedida", "N/A"),
                    'OrigenArticulo': prod.get("OrigenArticulo", "N/A"),
                    'Almacenes': {}
                }
 
            detalles_producto[codigo]["Almacenes"][prod["Almacen"]] = {
                'NombreAlmacen': prod.get("NombreAlmacen", "N/A"),
                'Stock': prod.get("Stock", 0),
                'Compromiso': prod.get("Compromiso", 0),
                'Pedido': prod.get("Pedido", 0)
            }
 
        producto_detalles = list(detalles_producto.values())[0]
        return render(request, "detalle_producto.html", {'producto': producto_detalles})
 
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response else 500
        return JsonResponse({'error': str(e)}, status=status)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
 
# ---------------------------------------------------------------------
# SOCIOS
# ---------------------------------------------------------------------
@login_required
@permiso_requerido('BUSCAR_SOCIOS')
def socios_lista_view(request):
    q = (request.GET.get("q") or "").strip()
    socios = []
    error = None
 
    if q:
        try:
            r = requests.get(
                NGROK_API_SOCIOS,
                params={"q": q},
                headers=_hmac_headers(),
                timeout=int(getattr(settings, "API_TIMEOUT", 7)),
            )
            r.raise_for_status()
            socios = r.json()
        except requests.exceptions.RequestException as e:
            error = str(e)
 
    return render(request, "socios_lista.html", {
        "q": q,
        "socios": socios,
        "error": error,
    })
 
@login_required
@permiso_requerido('BUSCAR_SOCIOS')
def socio_detalle_view(request, cardcode: str):
    detalle = None
    error = None
    try:
        r = requests.get(
            f"{NGROK_API_SOCIOS}/{cardcode}",
            headers=_hmac_headers(),
            timeout=int(getattr(settings, "API_TIMEOUT", 7)),
        )
        r.raise_for_status()
        detalle = r.json()
    except requests.exceptions.RequestException as e:
        error = str(e)
 
    return render(request, "socio_detalle.html", {
        "cardcode": cardcode,
        "detalle": detalle,
        "error": error,
    })
 