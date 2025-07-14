# apps/organizaciones/urls.py
from django.urls import path
from .views import cargos_por_area

urlpatterns = [
    path('api/cargos_por_area/<int:area_id>/', cargos_por_area, name='api_cargos_por_area'),
]