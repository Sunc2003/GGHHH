from django.http import JsonResponse
from .models import Cargo

def cargos_por_area(request, area_id):
    cargos = Cargo.objects.filter(area_id=area_id).values('id', 'nombre')
    return JsonResponse(list(cargos), safe=False)