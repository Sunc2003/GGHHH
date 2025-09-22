# apps/sap/views.py
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from apps.permisos.decorators import permiso_requerido

import requests
import time, hmac, hashlib
from collections import defaultdict

# ---- ENDPOINTS REMOTOS ----
NGROK_API_URL = "https://4391c8832496.ngrok-free.app/api/productos"
NGROK_API_SOCIOS = "https://4391c8832496.ngrok-free.app/api/socios"
NGROK_API_OV_ABIERTAS = "https://4391c8832496.ngrok-free.app/api/ventas/ov_abiertas"
NGROK_API_OV_PENDIENTES = "https://4391c8832496.ngrok-free.app/api/ventas/ov_pendientes_entrega"
NGROK_API_GUIAS_PENDIENTES = "https://4391c8832496.ngrok-free.app/api/ventas/guias_pendientes_facturar"
NGROK_API_FACTURAS_VENCIDAS = "https://4391c8832496.ngrok-free.app/api/ventas/facturas_vencidas"

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
        # Buscar la OV específica en abiertas
        r_ov = requests.get(
            NGROK_API_OV_ABIERTAS,
            params={"cardcode": cardcode},
            headers=_hmac_headers(),
            timeout=int(getattr(settings, "API_TIMEOUT", 7)),
        )
        r_ov.raise_for_status()
        abiertas = r_ov.json()
        detalle_ov = next((ov for ov in abiertas if ov["DocNum"] == docnum), None)

        # Buscar los ítems pendientes de esa OV
        r_pend = requests.get(
            NGROK_API_OV_PENDIENTES,
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
