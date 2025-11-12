# apps/usuarios/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Area, Cargo

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'first_name', 'last_name', 'area', 'cargo', 'is_active', 'last_login')
    list_filter = ('is_staff', 'area', 'cargo', 'is_active')

    fieldsets = UserAdmin.fieldsets + (
        ('Datos adicionales', {
            'fields': (
                'area', 'cargo',
                'usuario_ad', 'usuario_office', 'usuario_sap',
                'equipo_a_cargo', 'impresora_a_cargo', 'movil'
            )
        }),
    )

admin.site.register(Area)
admin.site.register(Cargo)
