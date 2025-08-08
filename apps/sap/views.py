from django.shortcuts import render
import requests
from django.http import JsonResponse

NGROK_API_URL = "https://4cc96362eae8.ngrok-free.app/api/productos"

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

def buscador_productos_view(request):
    resultados = []
    termino = request.GET.get("q", "")
    filtrar_stock = request.GET.get("con_stock", "") == "on"

    if termino:
        try:
            response = requests.get(
                NGROK_API_URL,
                params={"q": termino},
                headers={
                    "ngrok-skip-browser-warning": "true",
                    "User-Agent": "DjangoClient/1.0"
                },
                timeout=5
            )
            response.raise_for_status()
            productos = response.json()

            if filtrar_stock:
                resultados = [p for p in productos if p.get("Stock", 0) > 0]
            else:
                resultados = productos

        except requests.exceptions.RequestException as e:
            resultados = [{
                "Codigo": "Error",
                "Descripcion": str(e),
                "Stock": "N/A",
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
