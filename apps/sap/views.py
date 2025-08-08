from django.shortcuts import render
import requests
from django.http import JsonResponse

NGROK_API_URL = "https://16cbecaa20f9.ngrok-free.app/api/productos"

def buscar_productos_remoto(request):
    termino = request.GET.get("q", "")

    try:
        response = requests.get(NGROK_API_URL, params={"q": termino}, timeout=5)
        response.raise_for_status()
        data = response.json()
        return JsonResponse({"productos": data})
    except requests.exceptions.RequestException as e:
        return JsonResponse({"error": str(e)}, status=500)

