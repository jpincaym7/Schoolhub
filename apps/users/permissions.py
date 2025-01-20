from rest_framework.permissions import BasePermission
from rest_framework import permissions

class IsAdminUser(permissions.BasePermission):
    """
    Custom permission to only allow admin users to create teachers and parents.
    """
    def has_permission(self, request, view):
        # Allow read operations for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Only allow admins to create/update/delete users
        return request.user and request.user.is_authenticated and request.user.user_type == 'admin'


class IsAdminUserManagement(permissions.BasePermission):
    """
    Permiso personalizado para asegurar que solo los administradores puedan crear, 
    actualizar o eliminar módulos y permisos.
    """
    def has_permission(self, request, view):
        # Solo los administradores pueden realizar operaciones de creación, actualización y eliminación
        if request.method in permissions.SAFE_METHODS:
            return True  # GET, HEAD, OPTIONS son seguros y accesibles para todos
        return request.user and request.user.is_staff