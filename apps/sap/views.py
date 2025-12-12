# apps/sap/views.py
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from apps.permisos.decorators import permiso_requerido
 
import requests
import time, hmac, hashlib
from collections import defaultdict
 
# apps/sap/views.py
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from apps.permisos.decorators import permiso_requerido
 
import requests
import time, hmac, hashlib
from collections import defaultdict
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
import requests
from .services import SapQuotationsService, SapOrdersService  
from supabase import create_client
from django.utils.text import slugify
from datetime import datetime 

import json
from django.core.serializers.json import DjangoJSONEncoder
from django.views.generic import TemplateView

from .commission_utils import get_brackets_for_user, get_user_scheme_name
 
# ---- ENDPOINTS REMOTOS ----
NGROK_API_URL = "https://36df3f8d4f2e.ngrok-free.app/api/productos"
NGROK_API_SOCIOS = "https://36df3f8d4f2e.ngrok-free.app/api/socios"
NGROK_API_OV_ABIERTAS = "https://36df3f8d4f2e.ngrok-free.app/api/ventas/ov_abiertas"
NGROK_API_OV_PENDIENTES = "https://36df3f8d4f2e.ngrok-free.app/api/ventas/ov_pendientes_entrega"
NGROK_API_GUIAS_PENDIENTES = "https://36df3f8d4f2e.ngrok-free.app/api/ventas/guias_pendientes_facturar"
NGROK_API_FACTURAS_VENCIDAS = "https://36df3f8d4f2e.ngrok-free.app/api/ventas/facturas_vencidas"
NGROK_API_ITEMS = "https://36df3f8d4f2e.ngrok-free.app/api/public/items/inventario"  #
 
 # ========= Supabase: subir OC =========
SUPABASE_URL    = getattr(settings, "SUPABASE_URL", "")
SUPABASE_KEY    = getattr(settings, "SUPABASE_KEY", "")
SUPABASE_BUCKET = getattr(settings, "SUPABASE_BUCKET", "media")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if (SUPABASE_URL and SUPABASE_KEY) else None


def subir_oc_a_supabase(file_obj, cardcode: str) -> str | None:
    """
    Sube el PDF de OC al bucket 'media' (o el que tengas configurado)
    y retorna la URL pública.
    """
    if not supabase:
        return None

    # nombre limpio
    original_name = file_obj.name or "oc.pdf"
    base_name, ext = (original_name.rsplit(".", 1) + ["pdf"])[:2]
    safe_name = f"{slugify(base_name)}.{ext.lower()}"

    # ruta interna en el bucket
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    path = f"ov_oc/{cardcode}/{timestamp}_{safe_name}"

    # leer el archivo en bytes
    data = file_obj.read()

    # subir al bucket
    supabase.storage.from_(SUPABASE_BUCKET).upload(
        path,
        data,
        {
            "content-type": "application/pdf",
            "x-upsert": "true",
        },
    )

    # URL pública
    public_url = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(path)
    return public_url
 
 
# ---- HEADERS BASE ----
HEADERS_BASE = {
    "ngrok-skip-browser-warning": "true",
    "User-Agent": "DjangoClient/1.0",
    "accept": "application/json",
}
 
 
def _hmac_headers():
    """
    Genera los headers requeridos para HMAC:
      - X-API-KeyId
      - X-API-Timestamp
      - X-API-Signature
    """
    key_id = getattr(settings, "API_KEY_ID", None)
    key_secret = getattr(settings, "API_KEY_SECRET", None)
    if not key_id or not key_secret:
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
@permiso_requerido("BUSCAR_PRODUCTOS_SAP")
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
        return JsonResponse(
            {"error": str(e), "response_text": body, "status_code": status}, status=status
        )
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
 
 
@login_required
@permiso_requerido("BUSCAR_PRODUCTOS_SAP")
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
 
            for p in productos:
                p.setdefault("StockTotal", p.get("StockTotal", 0) or 0)
                p.setdefault("Comprometido", p.get("Comprometido", 0) or 0)
                p["Disponible"] = p["StockTotal"] - p["Comprometido"]
 
            resultados = (
                [p for p in productos if p.get("StockTotal", 0) > 0]
                if filtrar_stock
                else productos
            )
 
            if not resultados:
                resultados = [
                    {
                        "Codigo": "No encontrado",
                        "Descripcion": "No se encontraron productos con ese término.",
                        "StockTotal": "N/A",
                        "Disponible": "N/A",
                        "Comprometido": "N/A",
                        "Pedido": "N/A",
                        "PrecioMinVta": "N/A",
                    }
                ]
 
        except requests.exceptions.RequestException as e:
            resultados = [
                {
                    "Codigo": "Error",
                    "Descripcion": str(e),
                    "StockTotal": "N/A",
                    "Disponible": "N/A",
                    "Comprometido": "N/A",
                    "Pedido": "N/A",
                    "PrecioMinVta": "N/A",
                }
            ]
 
    return render(
        request,
        "buscador_productos.html",
        {"termino": termino, "filtrar_stock": filtrar_stock, "resultados": resultados},
    )
 
 
@login_required
@permiso_requerido("BUSCAR_PRODUCTOS_SAP")
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
            return JsonResponse({"error": "Producto no encontrado"}, status=404)
 
        detalles_producto = {}
        for prod in productos:
            codigo = prod["Codigo"]
            if codigo not in detalles_producto:
                detalles_producto[codigo] = {
                    "Codigo": codigo,
                    "Descripcion": prod.get("Descripcion"),
                    "PrecioMinVta": prod.get("PrecioMinVta"),
                    "ProveedorPredeterminado": prod.get("ProveedorPredeterminado", "N/A"),
                    "SKUProveedor": prod.get("SKUProveedor", "N/A"),
                    "NombreProveedor": prod.get("NombreProveedor", "N/A"),
                    "UnidadMedida": prod.get("UnidadMedida", "N/A"),
                    "OrigenArticulo": prod.get("OrigenArticulo", "N/A"),
                    "Almacenes": {},
                }
 
            detalles_producto[codigo]["Almacenes"][prod["Almacen"]] = {
                "NombreAlmacen": prod.get("NombreAlmacen", "N/A"),
                "Stock": prod.get("Stock", 0),
                "Compromiso": prod.get("Compromiso", 0),
                "Pedido": prod.get("Pedido", 0),
            }
 
        producto_detalles = list(detalles_producto.values())[0]
        return render(request, "detalle_producto.html", {"producto": producto_detalles})
 
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response else 500
        return JsonResponse({"error": str(e)}, status=status)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
 
 
# ---------------------------------------------------------------------
# SOCIOS
# ---------------------------------------------------------------------
@login_required
@permiso_requerido("BUSCAR_SOCIOS")
def socios_lista_view(request):
    q = (request.GET.get("q") or "").strip()
    socios, error = [], None
 
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
 
    return render(request, "socios_lista.html", {"q": q, "socios": socios, "error": error})
 
 
@login_required
@permiso_requerido("BUSCAR_SOCIOS")
def socio_detalle_view(request, cardcode: str):
    detalle, ov_abiertas, guias_pendientes, facturas_vencidas, error = None, [], [], [], None
    ov_detalle_dict = defaultdict(list)
 
    try:
        # Detalle del socio
        r = requests.get(
            f"{NGROK_API_SOCIOS}/{cardcode}",
            headers=_hmac_headers(),
            timeout=int(getattr(settings, "API_TIMEOUT", 7)),
        )
        r.raise_for_status()
        detalle = r.json()
 
        # OV Abiertas
        r_ov = requests.get(
            NGROK_API_OV_ABIERTAS,
            params={"cardcode": cardcode},
            headers=_hmac_headers(),
            timeout=int(getattr(settings, "API_TIMEOUT", 7)),
        )
        r_ov.raise_for_status()
        ov_abiertas = r_ov.json()
 
        # OV Pendientes
        r_pend = requests.get(
            NGROK_API_OV_PENDIENTES,
            params={"cardcode": cardcode},
            headers=_hmac_headers(),
            timeout=int(getattr(settings, "API_TIMEOUT", 7)),
        )
        r_pend.raise_for_status()
        ov_pendientes = r_pend.json()
 
        # Agrupar líneas pendientes por DocNum
        for item in ov_pendientes:
            ov_detalle_dict[item["DocNum"]].append(item)
 
        # Guías Pendientes
        r_guias = requests.get(
            NGROK_API_GUIAS_PENDIENTES,
            params={"cardcode": cardcode},
            headers=_hmac_headers(),
            timeout=int(getattr(settings, "API_TIMEOUT", 7)),
        )
        r_guias.raise_for_status()
        guias_pendientes = r_guias.json()
 
        # Facturas Vencidas
        r_fact = requests.get(
            NGROK_API_FACTURAS_VENCIDAS,
            params={"cardcode": cardcode},
            headers=_hmac_headers(),
            timeout=int(getattr(settings, "API_TIMEOUT", 7)),
        )
        r_fact.raise_for_status()
        facturas_vencidas = r_fact.json()
 
    except requests.exceptions.RequestException as e:
        error = str(e)
 
    return render(
        request,
        "socio_detalle.html",
        {
            "cardcode": cardcode,
            "detalle": detalle,
            "ov_abiertas": ov_abiertas,
            "ov_detalle_dict": dict(ov_detalle_dict),  # agrupados listos
            "guias_pendientes": guias_pendientes,
            "facturas_vencidas": facturas_vencidas,
            "error": error,
        },
    )
 
@login_required
@permiso_requerido('BUSCAR_SOCIOS')
def ov_detalle_view(request, cardcode: str, docnum: int):
    detalle_ov, detalle_items, error = None, [], None
 
    try:
        # Buscar la OV específica
        r_ov = requests.get(
            NGROK_API_OV_ABIERTAS,
            params={"cardcode": cardcode},
            headers=_hmac_headers(),
            timeout=int(getattr(settings, "API_TIMEOUT", 7)),
        )
        r_ov.raise_for_status()
        abiertas = r_ov.json()
        detalle_ov = next((ov for ov in abiertas if ov["DocNum"] == docnum), None)
 
        # Buscar los ítems pendientes de esa OV (ya con precios, descuentos, etc.)
        r_pend = requests.get(
            NGROK_API_OV_PENDIENTES,   # este es tu endpoint corregido
            params={"cardcode": cardcode},
            headers=_hmac_headers(),
            timeout=int(getattr(settings, "API_TIMEOUT", 7)),
        )
        r_pend.raise_for_status()
        pendientes = r_pend.json()
        detalle_items = [p for p in pendientes if p["DocNum"] == docnum]
 
    except requests.exceptions.RequestException as e:
        error = str(e)
 
    return render(request, "ov_detalle.html", {
        "cardcode": cardcode,
        "docnum": docnum,
        "ov": detalle_ov,
        "detalle_items": detalle_items,
        "error": error,
    })
 
 
 
 
 
import json
import logging
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.views.generic import TemplateView
 
from .services import SapQuotationsService  # usa el service enfocado a cotizaciones
 
log = logging.getLogger(__name__)
 
class Cotizacion(TemplateView):
    """
    Renderiza el formulario HTML de creación de cotización.
    """
    template_name = "Cotizacion.html"
 
 
@require_POST
@csrf_protect
def crear_cotizacion(request):
    """
    Recibe JSON desde el front (fetch) y crea la cotización en SAP.
    Espera al menos: DocDate, DocDueDate, CardCode y DocumentLines.
    """
    try:
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return HttpResponseBadRequest("Body no es JSON válido.")
 
        # (Opcional) validaciones rápidas de campos clave:
        for k in ("DocDate", "DocDueDate", "CardCode", "DocumentLines"):
            if k not in payload:
                return HttpResponseBadRequest(f"Falta campo requerido: {k}")
 
        svc = SapQuotationsService()
        data = svc.create(payload)  # llama al Service Layer
 
        return JsonResponse({
            "DocEntry": data.get("DocEntry"),
            "DocNum":   data.get("DocNum"),
            "raw":      data,  # útil para debugging; quítalo si no lo necesitas
        }, status=201)
 
    except Exception as e:
        # Log interno y mensaje “bonito” hacia el front
        log.exception("Error creando cotización")
        msg = str(e)
        return JsonResponse(
            {"detail": msg},
            status=400 if "400" in msg or "Falta" in msg else 500
        )
    
 
@login_required
def guias_pendientes_view(request):
    # ── Filtros desde el GET ───────────────────────────────────────────
    vendedor = request.GET.get("vendedor", "")
    estado = request.GET.get("estado", "")  # Packing | En ruta | Entregado
    fecha_desde = request.GET.get("fecha_desde") or ""
    fecha_hasta = request.GET.get("fecha_hasta") or ""

    NGROK_API_GUIAS_PENDIENTES = (
        "https://36df3f8d4f2e.ngrok-free.app/api/guias-pendientes"
    )

    # Lista fija de vendedores
    vendedores = [
        "Rodrigo Gomez", "Alexis Bustamante", "Web", "Asistente - Jacqueline Pizarro",
        "Karen Oporto", "Mariana Cortés", "Asistente - Carolina Herrera", "Carlos Pinto",
        "Grecia Castro", "Daniel Canto", "Andres Rojas Machuca", "Carlos Solis",
        "Alfredo Garretón", "Dorka Molina", "Patricio Toro", "Alfredo Gomez",
        "Asistente - Sebastian Mella", "Israel Vergara", "Paola Rivera", "Silvina Araya",
        "Mercado Libre", "Sebastián Valdivia", "Hernán Ahumada",
    ]

    data, error = [], None

    # Validación estado → debe ser EXACTO a como viene en SAP
    estados_validos = {"Packing", "En ruta", "Entregado"}
    if estado not in estados_validos:
        estado = ""

    # Construcción de parámetros enviados a la API
    params = {}

    if vendedor:
        params["vendedor"] = vendedor

    if estado:
        params["estado_doc"] = estado  # 👈 Nombre correcto según API

    if fecha_desde:
        params["fecha_desde"] = fecha_desde

    if fecha_hasta:
        params["fecha_hasta"] = fecha_hasta

    # ── Consumir API ─────────────────────────────────────────────────────
    try:
        response = requests.get(NGROK_API_GUIAS_PENDIENTES, params=params, timeout=15)

        if response.status_code == 200:
            raw_data = response.json()

            # Normaliza claves con espacios a claves con guion bajo
            def normalize_keys(d: dict):
                return {
                    (k.replace(" ", "_") if isinstance(k, str) else k): v
                    for k, v in d.items()
                }

            data = [normalize_keys(item) for item in raw_data]

        else:
            error = f"Error del servidor: HTTP {response.status_code}"

    except Exception as e:
        error = f"Error de conexión: {e}"

    # ── Renderizar ─────────────────────────────────────────────────────────
    return render(
        request,
        "guias_pendientes.html",
        {
            "data": data,
            "vendedor": vendedor,
            "estado": estado,
            "fecha_desde": fecha_desde,
            "fecha_hasta": fecha_hasta,
            "error": error,
            "vendedores": vendedores,
        },
    )

 
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
import requests
import logging
 
log = logging.getLogger(__name__)
 
@login_required
@require_GET
def buscar_items_inventario(request):
    termino = (request.GET.get("q") or "").strip()
    if not termino:
        return JsonResponse([], safe=False)

    url = f"https://36df3f8d4f2e.ngrok-free.app/api/public/items/inventario?q={termino}"

    try:
        response = requests.get(
            url,
            timeout=10,
            headers={"ngrok-skip-browser-warning": "true", "accept": "application/json"},
        )
        response.raise_for_status()
        data = response.json()

        resultados = []
        for item in data:
            resultados.append({
                "Codigo": item.get("Codigo"),
                "ItemName": item.get("ItemName"),
                "FirmName": item.get("FirmName"),

                # Origen
                "Origen": item.get("U_Origin") or item.get("Origen"),

                "ProveedorCode": item.get("ProveedorCode"),
                "ProveedorName": item.get("ProveedorName"),

                "Stock_A01": item.get("Stock_A01", 0),
                "Stock_A02": item.get("Stock_A02", 0),
                "Stock_A08": item.get("Stock_A08", 0),

                # costos / precios
                "UltimoPrecioCompra": item.get("UltimoPrecioCompra"),
                "UltimaFechaCompra": item.get("UltimaFechaCompra"),

                # Precio mínimo de venta
                "PMV": item.get("PMV") or item.get("U_NX_PrecioMinVta"),
                "U_NX_PrecioMinVta": item.get("U_NX_PrecioMinVta"),

                # Costo promedio (para margen)
                "AcgPrice": item.get("AcgPrice"),
            })

        return JsonResponse(resultados, safe=False)

    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response else 500
        log.error(f"[buscar_items_inventario] Error HTTP {status}: {e}")
        return JsonResponse(
            {"error": f"Error HTTP {status}: {str(e)}"}, status=status
        )

    except requests.exceptions.RequestException as e:
        log.error(f"[buscar_items_inventario] Error de conexión: {e}")
        return JsonResponse(
            {"error": f"Error conectando al API remoto: {str(e)}"},
            status=500
        )

    except Exception as e:
        log.exception("[buscar_items_inventario] Error inesperado")
        return JsonResponse(
            {"error": f"Error procesando la respuesta: {str(e)}"},
            status=500
        )
 
# ============================================================
# 🔹 Detalle de Cotización (para JSON del front)
# ============================================================
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
 
@login_required
def cotizacion_detalle(request, doc_entry: int):
    """
    Devuelve el detalle completo de una cotización desde SAP
    para generar el PDF o mostrar en el front-end.
    """
    try:
        from .services import SapQuotationsService
        svc = SapQuotationsService()
 
        quotation = svc.get(doc_entry)
        if not quotation:
            return JsonResponse({'error': 'Cotización no encontrada'}, status=404)
 
        detalle = {
            "DocNum": quotation.get("DocNum"),
            "DocEntry": quotation.get("DocEntry"),
            "DocDate": quotation.get("DocDate"),
            "DocDueDate": quotation.get("DocDueDate"),
            "CardCode": quotation.get("CardCode"),
            "CardName": quotation.get("CardName"),
            "FederalTaxID": quotation.get("FederalTaxID"),
            "Address": quotation.get("Address"),
            "Phone1": quotation.get("Phone1"),
            "U_ContactoCliente": quotation.get("U_ContactoCliente"),
            "NumAtCard": quotation.get("NumAtCard"),
            "PaymentGroupCode": quotation.get("PaymentGroupCode"),
            "SalesPersonName": quotation.get("SalesPersonName"),
            "DocTotal": quotation.get("DocTotal"),
            "DocumentLines": quotation.get("DocumentLines", []),
        }
        return JsonResponse(detalle, safe=False)
 
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
 
 
from django.shortcuts import render
 
def preview_cotizacion(request):
    from .services import SapQuotationsService
    svc = SapQuotationsService()
    quotation = svc.get(183185)  # usa una cotización real
    return render(request, "cotizacion_pdf.html", {"quotation": quotation, "logo_path": "/static/img/ggh.png"})
 
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from weasyprint import HTML
from io import BytesIO
from .services import SapQuotationsService
from datetime import datetime
 
@login_required
def cotizacion_pdf(request, doc_entry: int):
    try:
        svc = SapQuotationsService()
        quotation = svc.get_full_quotation(doc_entry)
        if not quotation:
            return JsonResponse({"error": "Cotización no encontrada"}, status=404)
 
        def format_date(d):
            if not d:
                return "-"
            try:
                return datetime.strptime(d[:10], "%Y-%m-%d").strftime("%d-%m-%Y")
            except Exception:
                return d
 
        # 🔹 Formatear fechas
        quotation["DocDate_fmt"] = format_date(quotation.get("DocDate"))
        quotation["DocDueDate_fmt"] = format_date(quotation.get("DocDueDate"))
 
        # 🔹 Calcular valores base
        total = quotation.get("DocTotal", 0) or 0
 
        # Si SAP trae IVA explícito, úsalo; si no, aproximamos 19%
        iva_sap = quotation.get("VatSum")
        if iva_sap is None:
            neto_aprox = total / 1.19 if total else 0
            iva_num = round(total - neto_aprox)
        else:
            iva_num = round(iva_sap or 0)
 
        # Neto después de descuentos (base imponible actual)
        neto_num = round(total - iva_num)
 
        # 🔹 Obtener forma de pago desde SAP (nombre real)
        payment_name = quotation.get("PaymentTermsGroupName") or "No informado"
 
        # 🔹 Formatear valores CLP
        def fmt(valor):
            return f"{(valor or 0):,.0f}".replace(",", ".")
 
        # 🔹 Descuentos y totales
        # % de descuento: usar cualquiera disponible
        descuento_percent_val = (
            quotation.get("DiscountPercent")
            or quotation.get("DocDiscountPercent")
            or 0
        )
        try:
            p = float(descuento_percent_val) / 100.0
        except Exception:
            p = 0.0
 
        # Monto de descuento: si SAP lo entrega, usarlo; si no, estimar desde %
        descuento_monto_num = quotation.get("TotalDiscount")
        if descuento_monto_num is None:
            if 0 < p < 1:
                # neto_bruto * (1 - p) = neto_num  => neto_bruto = neto_num / (1 - p)
                neto_bruto_est = neto_num / (1 - p) if (1 - p) != 0 else neto_num
                descuento_monto_num = round(neto_bruto_est - neto_num)
            else:
                descuento_monto_num = 0
        else:
            descuento_monto_num = round(descuento_monto_num or 0)
 
        # Neto bruto (antes de descuento)
        neto_bruto_num = round(neto_num + descuento_monto_num)
 
        # Strings bonitos
        neto_fmt         = fmt(neto_bruto_num)       # Neto (antes de descuento)
        descuento_fmt    = fmt(descuento_monto_num)  # Descuento (monto)
        total_neto_fmt   = fmt(neto_num)             # Neto (después de descuento)
        iva_fmt          = fmt(iva_num)
        total_fmt        = fmt(total)
 
        # % descuento como string (solo para mostrar si > 0)
        try:
            dp = float(descuento_percent_val or 0.0)
        except Exception:
            dp = 0.0
        descuento_percent_str = (f"{dp:.2f}".rstrip("0").rstrip(".") + " %") if dp > 0 else ""
 
        # 🔹 Formatear precios de líneas
        for line in quotation.get("DocumentLines", []):
            if line.get("UnitPrice") is not None:
                line["UnitPrice_fmt"] = fmt(line["UnitPrice"])
            if line.get("LineTotal") is not None:
                line["LineTotal_fmt"] = fmt(line["LineTotal"])
 
        # 🔹 Contexto al template
        context = {
            "quotation": quotation,
            "payment_name": payment_name,
            "logo_path": "/static/img/ggh.png",
 
            # Totales (para el bloque del HTML)
            "neto": neto_fmt,                       # Neto (antes de descuento)
            "descuento": descuento_fmt,             # Monto de descuento
            "total_neto": total_neto_fmt,           # Neto después de descuento
            "iva": iva_fmt,
            "total": total_fmt,
            "descuento_percent": dp,                # número (para if)
            "descuento_percent_str": descuento_percent_str,  # "x %"
        }
 
        # 🔹 Renderizar PDF
        html_string = render(request, "cotizacion_pdf.html", context).content.decode("utf-8")
        pdf_file = BytesIO()
        HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(pdf_file)
 
        response = HttpResponse(pdf_file.getvalue(), content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="Cotizacion_{doc_entry}.pdf"'
        return response
 
    except Exception as e:
        return JsonResponse({"error": f"Ocurrió un error al generar el PDF: {e}"}, status=500)
 
    
    
# ---- Buscar socios por nombre (wrapper a FastAPI público) ----
from django.views.decorators.http import require_GET
from .services import SapBusinessPartnerService

@login_required
@require_GET
def buscar_socios_por_nombre(request):
    q = (request.GET.get("q") or "").strip()
    if not q:
        return JsonResponse([], safe=False)

    svc = SapBusinessPartnerService()
    socios = svc.search_partners(q)
    
    # Formateamos la respuesta para el front
    resultados = []
    for s in socios:
        # Filtramos solo direcciones de envío (bo_ShipTo)
        direcciones = [
            {
                "ID": addr.get("AddressName"), 
                "Calle": addr.get("Street"),
                "Comuna": addr.get("County") or addr.get("City")
            }
            for addr in s.get("BPAddresses", [])
            if addr.get("AddressType") == "bo_ShipTo"
        ]
        
        resultados.append({
            "CardCode": s.get("CardCode"),
            "Nombre": s.get("CardName"),
            "Direcciones": direcciones # Enviamos la lista al front
        })

    return JsonResponse(resultados, safe=False)


class MenuVentasView(TemplateView):
    template_name = "menu_ventas.html" 

from django.contrib.auth.mixins import LoginRequiredMixin
class BuscarCotizacionesView(LoginRequiredMixin, TemplateView):
    template_name = "buscar_cotizaciones.html"


@login_required
@require_GET
def api_cotizaciones(request):
    svc = SapQuotationsService()
    q      = request.GET.get("q") or None
    desde  = request.GET.get("desde") or None
    hasta  = request.GET.get("hasta") or None
    estado = request.GET.get("estado") or None
    slp    = request.GET.get("slp")
    slp    = int(slp) if (slp and slp.isdigit()) else None
    page   = int(request.GET.get("page", "1"))
    size   = int(request.GET.get("size", "20"))
    try:
        return JsonResponse(svc.search(q=q, desde=desde, hasta=hasta, estado=estado, slp=slp, page=page, size=size))
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    

@login_required
@require_POST
def api_cotizacion_action(request, doc_entry: int):
    try:
        payload = json.loads(request.body.decode("utf-8")) if request.body else {}
    except Exception:
        return HttpResponseBadRequest("JSON inválido")

    op = payload.get("op")
    svc = SapQuotationsService()

    try:
        if op == "close":
            out = svc.close(doc_entry)
        elif op == "cancel":
            out = svc.cancel(doc_entry)
        elif op == "patch":
            out = svc.patch(doc_entry, payload.get("data") or {})
        elif op == "to_order":
            out = svc.to_order(doc_entry, warehouse=payload.get("warehouse"), doc_date=payload.get("doc_date"))
        else:
            return HttpResponseBadRequest("Operación no soportada")

        return JsonResponse({"ok": True, "result": out})
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)
    
    
import json
import logging
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

log = logging.getLogger(__name__)

# helpers de ejemplo (reemplaza por tu lógica DB)
def get_all_commission_schemes():
    return [
        {"name": "Comisión 1", "brackets":[
            {"desde":7.00,"hasta":7.99,"valor":0.20},
            {"desde":8.00,"hasta":9.99,"valor":0.40},
            {"desde":10.00,"hasta":11.99,"valor":0.80},
            {"desde":12.00,"hasta":13.99,"valor":1.50},
            {"desde":14.00,"hasta":15.99,"valor":2.00},
            {"desde":16.00,"hasta":99999,"valor":3.00},
        ]},
        {"name":"Comisión 2","brackets":[
            {"desde":0.00,"hasta":9.99,"valor":0.10},
            {"desde":10.00,"hasta":19.99,"valor":0.50},
            {"desde":20.00,"hasta":99999,"valor":100.00},
        ]},
    ]

def get_user_scheme_name(user):
    """
    Devuelve el nombre del esquema de comisión para el usuario.
    Compara tanto user.usuario_sap como user.username (ambos normalizados a lowercase).
    Ajusta el diccionario `mapping` con los identificadores reales de tus usuarios.
    """
    if not user or not user.is_authenticated:
        return None

    username = (getattr(user, "username", "") or "").strip().lower()
    usuario_sap = (getattr(user, "usuario_sap", "") or "").strip().lower()

    # mapping: usa siempre claves en lowercase
    mapping = {
        "Alexssander lopez": "Comisión 1",
        "Gonzalo Neira":     "Comisión 2",
        # mappings por usuario_sap (también en lowercase)
        "alex_sap_user":     "Comisión 1",
        "gneira":            "Comisión 2",   # ejemplo: usuario_sap = 'Gneira' -> 'gneira'
    }

    # intenta por usuario_sap primero (si existe y no está vacío)
    if usuario_sap:
        sch = mapping.get(usuario_sap)
        if sch:
            return sch

    # intenta por username
    if username:
        sch = mapping.get(username)
        if sch:
            return sch

    # fallback: None
    return None


class OrdenVenta(LoginRequiredMixin, TemplateView):
    """
    Renderiza el formulario de Nota de Venta e inyecta la escala
    de comisión correspondiente al usuario logeado.
    """
    template_name = "Nota_Venta.html"
    login_url = "/accounts/login/"   # ajusta si tienes URL distinta

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        schemes = get_all_commission_schemes()
        schemes_map = {s["name"]: s.get("brackets", []) for s in schemes}

        scheme_name = get_user_scheme_name(self.request.user) or ""
        # si no hay esquema asignado, ponemos el primero como default
        if not scheme_name and schemes:
            scheme_name = schemes[0]["name"]

        # inyectar en el contexto (usar DjangoJSONEncoder)
        ctx["commission_schemes_json"]  = json.dumps(schemes, cls=DjangoJSONEncoder)
        ctx["commission_brackets_json"] = json.dumps(schemes_map, cls=DjangoJSONEncoder)
        ctx["commission_scheme_name"]   = scheme_name
        ctx["debug_user"] = {
            "is_authenticated": self.request.user.is_authenticated,
            "username": getattr(self.request.user, "username", None),
            "usuario_sap": getattr(self.request.user, "usuario_sap", None),
        }

        # logging para debug en servidor (temporal)
        log.debug("OrdenVenta.get_context_data user debug: %s", ctx["debug_user"])

        return ctx

import re
import json
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.utils import timezone
import logging
from apps.utils.supabase_storage import SupabaseStorage
log = logging.getLogger(__name__)



def subir_oc_a_supabase(oc_file, cardcode=None):
    """
    Sube el PDF de OC a Supabase usando el mismo backend SupabaseStorage
    que ya usas en procesos_view, y devuelve la URL pública.
    """
    try:
        storage = SupabaseStorage()

        # Nombre “bonito” + timestamp
        now_str   = timezone.now().strftime("%Y%m%d_%H%M%S")
        original  = oc_file.name
        safe_name = re.sub(r'[^\w\-.]', '_', original)

        subfolder = f"ov_oc/{cardcode}" if cardcode else "ov_oc"
        path      = f"{subfolder}/{now_str}_{safe_name}"

        # 👉 Igual que en procesos_view: _save recibe el UploadedFile directo
        storage._save(path, oc_file)

        # 👉 Y usamos el mismo método para obtener la URL pública
        url_publica = storage.get_public_url(path)
        return url_publica

    except Exception as e:
        log.exception(f"Error subiendo OC a Supabase: {e}")
        return None
    
    
@login_required
@csrf_protect
@require_POST
def crear_orden_venta(request):
    """
    Crea una OV (Nota de Venta) en SAP.
    - Recibe JSON dentro de request.POST['payload']
    - Adjunta SIEMPRE un PDF de OC en request.FILES['oc_pdf'] (sube a Supabase)
    """
    try:
        raw_payload = request.POST.get("payload")
        if not raw_payload:
            return HttpResponseBadRequest("Falta payload JSON.")

        try:
            payload = json.loads(raw_payload)
        except json.JSONDecodeError:
            return HttpResponseBadRequest("Payload no es JSON válido.")

        # Campos mínimos
        for k in ("DocDate", "DocDueDate", "CardCode", "DocumentLines"):
            if k not in payload:
                return HttpResponseBadRequest(f"Falta campo requerido: {k}")

        cardcode = payload.get("CardCode")

        # Flag de solicitud de compra (header, por si lo sigues usando)
        con_solicitud = bool(payload.get("ConSolicitudCompra"))

        # ========= PDF OC (OBLIGATORIO) =========
        oc_pdf = request.FILES.get("oc_pdf")
        if not oc_pdf:
            return HttpResponseBadRequest("Debe adjuntar el PDF con la Orden de Compra del cliente.")

        # Subir siempre la OC del cliente a Supabase
        oc_url = subir_oc_a_supabase(oc_pdf, cardcode)

        # ========= Mapear a ORDR =========
        header = {
            "DocDate":    payload.get("DocDate"),
            "TaxDate":    payload.get("TaxDate") or payload.get("DocDate"),
            "DocDueDate": payload.get("DocDueDate"),

            "CardCode":   cardcode,

            # Datos logísticos
            "ShipToCode":         payload.get("ShipToCode") or None,
            "PartSupply":         payload.get("PartSupply") or None,
            "TransportationCode": payload.get("TransportationCode"),
            "Comments":           payload.get("Comments") or None,

            # Campos U_ header
            # 👉 U_GGH_MTVO se usa SOLO para la URL del PDF en Supabase
            "U_GGH_OCCLIE":         oc_url or None,
            "U_NX_TipoOrden":    payload.get("U_NX_TipoOrden") or None,
            "U_INX_FolioRef_1":  payload.get("U_INX_FolioRef_1") or None,
            "U_NX_FechaEntrega": payload.get("U_NX_FechaEntrega") or None,
            "U_INX_FechaRef_1":  payload.get("U_INX_FechaRef_1") or None,
            "U_GGH_TPD":         payload.get("U_GGH_TPD") or None,
            "U_GGH_FPG":         payload.get("U_GGH_FPG") or None,
            "U_GGH_TDS":         payload.get("U_GGH_TDS") or None,
            "U_GGH_FLE":         float(payload.get("U_GGH_FLE") or 0),
        }

        # Si quieres marcar a nivel documento que existe SC:
        header["U_GGH_SCP"] = "SI" if con_solicitud else "NO"

        # Líneas (ya vienen con U_GGH_PROV, U_GGH_CTC, U_GGH_PCS, etc.)
        header["DocumentLines"] = payload["DocumentLines"]

        svc = SapOrdersService()
        data = svc.create(header)

        return JsonResponse(
            {
                "DocEntry": data.get("DocEntry"),
                "DocNum":   data.get("DocNum"),
                "raw":      data,
            },
            status=201
        )

    except Exception as e:
        log.exception("Error creando OV")
        msg = str(e)
        return JsonResponse(
            {"detail": msg},
            status=400 if "400" in msg or "Falta" in msg else 500
        )
        
