from django.shortcuts import render
import requests
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from apps.permisos.decorators import permiso_requerido
 
NGROK_API_URL = "https://804103bbd425.ngrok-free.app/api/productos"
NGROK_API_SOCIOS = "https://804103bbd425.ngrok-free.app/api/socios" 
 
HEADERS_NGROK = {
    "ngrok-skip-browser-warning": "true",
    "User-Agent": "DjangoClient/1.0"
}
 
@login_required
@permiso_requerido('BUSCAR_PRODUCTOS_SAP')
def buscar_productos_remoto(request):
    termino = request.GET.get("q", "")
    headers = {
        "ngrok-skip-browser-warning": "true",
        "User-Agent": "DjangoClient/1.0"
    }
 
    try:
        response = requests.get(NGROK_API_URL, params={"q": termino}, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()
        return JsonResponse({"productos": data})
    except requests.exceptions.HTTPError as e:
        return JsonResponse({
            "error": str(e),
            "response_text": response.text,
            "status_code": response.status_code
        }, status=500)
    except requests.exceptions.RequestException as e:
        return JsonResponse({"error": str(e)}, status=500)
    
@login_required
@permiso_requerido('BUSCAR_PRODUCTOS_SAP')
def buscador_productos_view(request):
    resultados = []
    termino = request.GET.get("q", "")  # Obtén el término de búsqueda de la URL
    filtrar_stock = request.GET.get("con_stock", "") == "on"  # Filtrar por stock disponible

    if termino:
        try:
            # Realizamos la solicitud a la API para obtener productos
            response = requests.get(
                NGROK_API_URL,
                params={"q": termino},  # Pasa el término de búsqueda
                headers={
                    "ngrok-skip-browser-warning": "true",
                    "User-Agent": "DjangoClient/1.0"
                },
                timeout=5  # Tiempo de espera de 5 segundos
            )
            response.raise_for_status()  # Si la respuesta tiene errores, lanzará una excepción

            productos = response.json()  # Convierte la respuesta en un objeto JSON

            # Filtrar por stock si el checkbox 'con_stock' está activado
            if filtrar_stock:
                resultados = [p for p in productos if p.get("StockTotal", 0) > 0]
            else:
                resultados = productos

            # Si no hay productos, mostramos un mensaje de no encontrado
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
            # Si hay un error con la solicitud a la API, mostramos un mensaje de error
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
    

def obtener_detalle_producto(request, itemcode):
    try:
        # Solicitud a la API externa
        response = requests.get(
            f"{NGROK_API_URL}/{itemcode}",
            headers={
                "ngrok-skip-browser-warning": "true",
                "User-Agent": "DjangoClient/1.0"
            },
            timeout=5
        )
        response.raise_for_status()
        productos = response.json()

        if not productos:
            return JsonResponse({'error': 'Producto no encontrado'}, status=404)

        # Diccionario para organizar los almacenes
        detalles_producto = {}
        for producto in productos:
            codigo = producto["Codigo"]
            if codigo not in detalles_producto:
                detalles_producto[codigo] = {
                    'Codigo': codigo,
                    'Descripcion': producto.get("Descripcion"),
                    'PrecioMinVta': producto.get("PrecioMinVta"),
                    'ProveedorPredeterminado': producto.get("ProveedorPredeterminado", "N/A"),
                    'SKUProveedor': producto.get("SKUProveedor", "N/A"),
                    'NombreProveedor': producto.get("NombreProveedor", "N/A"),
                    'UnidadMedida': producto.get("UnidadMedida", "N/A"),
                    'OrigenArticulo': producto.get("OrigenArticulo", "N/A"),
                    'Almacenes': {}  # Diccionario de almacenes
                }

            # Guardamos un diccionario por cada almacén
            detalles_producto[codigo]["Almacenes"][producto["Almacen"]] = {
                'NombreAlmacen': producto.get("NombreAlmacen", "N/A"),
                'Stock': producto.get("Stock", 0),
                'Compromiso': producto.get("Compromiso", 0),
                'Pedido': producto.get("Pedido", 0)
            }

        producto_detalles = list(detalles_producto.values())[0]
        return render(request, "detalle_producto.html", {'producto': producto_detalles})

    except requests.exceptions.RequestException as e:
        return JsonResponse({'error': str(e)}, status=500)

 
@login_required
@permiso_requerido('BUSCAR_SOCIOS')
def socios_lista_view(request):
    q = request.GET.get("q", "").strip()
    socios = []
    error = None
 
    if q:
        try:
            r = requests.get(
                NGROK_API_SOCIOS,
                params={"q": q},
                headers=HEADERS_NGROK,
                timeout=7,
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
            headers=HEADERS_NGROK,
            timeout=7,
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