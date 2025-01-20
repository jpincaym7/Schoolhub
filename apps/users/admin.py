from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from apps.users.models import User, Module, ModulePermission, UserModuleAccess

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """
    Configuración del panel de administración para el modelo User
    """
    list_display = ('username', 'email', 'user_type', 'is_active', 'is_staff')  # Agregar user_type a la lista
    list_filter = ('user_type', 'is_active', 'is_staff')  # Filtrar por user_type
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)
    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        (_('Información Personal'), {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'address', 'profile_image', 'user_type')  # Agregar user_type aquí
        }),
        (_('Permisos'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Información Importante'), {
            'fields': ('last_login', 'date_joined')
        }),
    )
    readonly_fields = ('last_login', 'date_joined')


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    """
    Configuración del panel de administración para el modelo Module
    """
    list_display = ('name', 'code', 'is_active', 'order', 'parent')
    list_filter = ('is_active',)
    search_fields = ('name', 'code', 'description')
    ordering = ('order', 'name')
    fieldsets = (
        (None, {
            'fields': ('name', 'code', 'description', 'is_active', 'order', 'icon', 'url', 'parent')
        }),
        (_('Fechas'), {
            'fields': ('created_at', 'updated_at'),
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ModulePermission)
class ModulePermissionAdmin(admin.ModelAdmin):
    """
    Configuración del panel de administración para el modelo ModulePermission
    """
    list_display = ('module', 'user_type', 'can_view', 'can_create', 'can_edit', 'can_delete')
    list_filter = ('user_type', 'can_view', 'can_create', 'can_edit', 'can_delete')
    search_fields = ('module__name', 'user_type')
    ordering = ('module', 'user_type')
    fieldsets = (
        (None, {
            'fields': ('module', 'user_type', 'can_view', 'can_create', 'can_edit', 'can_delete')
        }),
        (_('Fechas'), {
            'fields': ('created_at', 'updated_at'),
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


@admin.register(UserModuleAccess)
class UserModuleAccessAdmin(admin.ModelAdmin):
    """
    Configuración del panel de administración para el modelo UserModuleAccess
    """
    list_display = ('user', 'module', 'accessed_at', 'ip_address')
    list_filter = ('accessed_at',)
    search_fields = ('user__username', 'module__name', 'ip_address', 'user_agent')
    ordering = ('-accessed_at',)
    fieldsets = (
        (None, {
            'fields': ('user', 'module', 'ip_address', 'user_agent')
        }),
        (_('Fechas'), {
            'fields': ('accessed_at',),
        }),
    )
    readonly_fields = ('accessed_at',)
