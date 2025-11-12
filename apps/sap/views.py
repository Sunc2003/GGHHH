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


# ---- ENDPOINTS REMOTOS ----
NGROK_API_URL = "https://82f86d348566.ngrok-free.app/api/productos"
NGROK_API_SOCIOS = "https://82f86d348566.ngrok-free.app/api/socios"
NGROK_API_OV_ABIERTAS = "https://82f86d348566.ngrok-free.app/api/ventas/ov_abiertas"
NGROK_API_OV_PENDIENTES = "https://82f86d348566.ngrok-free.app/api/ventas/ov_pendientes_entrega"
NGROK_API_GUIAS_PENDIENTES = "https://82f86d348566.ngrok-free.app/api/ventas/guias_pendientes_facturar"
NGROK_API_FACTURAS_VENCIDAS = "https://82f86d348566.ngrok-free.app/api/ventas/facturas_vencidas"
NGROK_API_ITEMS = "https://82f86d348566.ngrok-free.app/api/public/items/inventario"  # 




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
    vendedor = request.GET.get("vendedor", "")
    solo_no_recepcionadas = request.GET.get("solo_no_recepcionadas", "false")

    NGROK_API_GUIAS_PENDIENTES = "https://82f86d348566.ngrok-free.app/api/guias-pendientes"

    
    vendedores = [
        "Rodrigo Gomez",
        "Alexis Bustamante",
        "Web",
        "Asistente - Jacqueline Pizarro",
        "Karen Oporto",
        "Mariana Cortés",
        "Asistente - Carolina Herrera",
        "Carlos Pinto",
        "Grecia Castro",
        "Daniel Canto",
        "Andres Rojas Machuca",
        "Carlos Solis",
        "Alfredo Garretón",
        "Dorka Molina",
        "Patricio Toro",
        "Alfredo Gomez",
        "Asistente - Sebastian Mella",
        "Israel Vergara",
        "Paola Rivera",
        "Silvina Araya",
        "Mercado Libre",
        "Sebastián Valdivia",
        "Hernán Ahumada",
    ]

    data = []
    error = None

    try:
        params = {
            "vendedor": vendedor,
            "solo_no_recepcionadas": solo_no_recepcionadas.lower() == "true"
        }

        response = requests.get(NGROK_API_GUIAS_PENDIENTES, params=params, timeout=15)
        if response.status_code == 200:
            raw_data = response.json()

            # 🔹 Normaliza nombres de campos con espacios
            def normalize_keys(d):
                return {k.replace(" ", "_"): v for k, v in d.items()}

            data = [normalize_keys(item) for item in raw_data]
        else:
            error = f"Error al obtener datos del servidor (HTTP {response.status_code})"
    except Exception as e:
        error = f"Error de conexión: {e}"

    return render(
        request,
        "guias_pendientes.html",
        {
            "data": data,
            "vendedor": vendedor,
            "solo_no_recepcionadas": solo_no_recepcionadas,
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
    """
    Consulta la API FastAPI pública (SAP HANA / Inventario) para buscar productos.
    Endpoint actualizado: /api/public/items/inventario
    Retorna los campos principales requeridos por el buscador de cotizaciones.
    """
    termino = (request.GET.get("q") or "").strip()
    if not termino:
        return JsonResponse([], safe=False)

    # 🔹 Nueva ruta corregida (endpoint público)
    url = f"https://82f86d348566.ngrok-free.app/api/public/items/inventario?q={termino}"

    try:
        response = requests.get(
            url,
            timeout=10,
            headers={"ngrok-skip-browser-warning": "true", "accept": "application/json"},
        )
        response.raise_for_status()
        data = response.json()

        # 🔹 Normalización de campos
        resultados = []
        for item in data:
            resultados.append({
                "Codigo": item.get("Codigo"),
                "ItemName": item.get("ItemName"),
                "FirmName": item.get("FirmName"),
                "Origen": item.get("Origen"),
                "ProveedorCode": item.get("ProveedorCode"),
                "ProveedorName": item.get("ProveedorName"),
                "Stock_A01": item.get("Stock_A01", 0),
                "Stock_A02": item.get("Stock_A02", 0),
                "Stock_A08": item.get("Stock_A08", 0),
                "UltimoPrecioCompra": item.get("UltimoPrecioCompra"),
                "UltimaFechaCompra": item.get("UltimaFechaCompra"),
                "PMV": item.get("PMV"),
                
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
        neto = round(total / 1.19)
        iva = round(total - neto)

        # 🔹 Obtener forma de pago desde SAP (nombre real)
        payment_name = quotation.get("PaymentTermsGroupName") or "No informado"

        # 🔹 Formatear valores CLP
        def fmt(valor):
            return f"{valor:,.0f}".replace(",", ".")

        neto_fmt = fmt(neto)
        iva_fmt = fmt(iva)
        total_fmt = fmt(total)

        # 🔹 Formatear precios de líneas
        for line in quotation.get("DocumentLines", []):
            if line.get("UnitPrice"):
                line["UnitPrice_fmt"] = fmt(line["UnitPrice"])
            if line.get("LineTotal"):
                line["LineTotal_fmt"] = fmt(line["LineTotal"])

        # 🔹 Contexto al template
        context = {
            "quotation": quotation,
            "neto": neto_fmt,
            "iva": iva_fmt,
            "total": total_fmt,
            "payment_name": payment_name,
            "logo_path": "/static/img/ggh.png",
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
    
    
