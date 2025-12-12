"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static

# config/urls.py
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('usuarios/', include('apps.usuarios.urls')),
    path('', lambda request: redirect('login', permanent=False)),
    path('permisos/', include('apps.permisos.urls')),
    path('utils/', include('apps.utils.urls')),
    path('sap/' , include('apps.sap.urls')),

     path("", include("apps.usuarios.urls")),
    

    path('', include('apps.sap.urls')),

    # tus otras apps...
    path('tickets/', include('apps.tickets.urls')),  # 👈 aquí montamos tickets
    
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)