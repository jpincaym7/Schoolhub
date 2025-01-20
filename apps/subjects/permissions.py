from rest_framework import permissions
from apps.users.models import Module, ModulePermission

class ModulePermissionMixin:
    def has_module_permission(self, user, module_code, permission_type):
        # Superadmin siempre tiene acceso completo
        if user.is_superuser:
            return True
        
        try:
            module = Module.objects.get(code=module_code)
            # Solo verificar permisos para usuarios con tipos específicos
            if user.user_type not in ['admin', 'teacher', 'parent']:
                return False
                
            module_permission = ModulePermission.objects.get(
                module=module,
                user_type=user.user_type
            )
            return getattr(module_permission, permission_type)
        except (Module.DoesNotExist, ModulePermission.DoesNotExist):
            return False

class SubjectPermission(permissions.BasePermission, ModulePermissionMixin):
    def has_permission(self, request, view):
        user = request.user
        # Solo admin y profesores pueden acceder al módulo de materias
        if user.user_type not in ['admin', 'teacher']:
            return False
            
        if request.method in permissions.SAFE_METHODS:
            return self.has_module_permission(user, 'subjects', 'can_view')
        elif request.method == 'POST':
            return self.has_module_permission(user, 'subjects', 'can_create')
        return False

    def has_object_permission(self, request, view, obj):
        user = request.user
        
        if request.method in permissions.SAFE_METHODS:
            return self.has_module_permission(user, 'subjects', 'can_view')
        elif request.method in ['PUT', 'PATCH']:
            # Solo el profesor asignado o admin pueden editar
            return (
                self.has_module_permission(user, 'subjects', 'can_edit') and 
                (user.is_superuser or user.user_type == 'admin' or obj.teacher == user)
            )
        elif request.method == 'DELETE':
            # Solo admin puede eliminar
            return user.user_type == 'admin' and self.has_module_permission(user, 'subjects', 'can_delete')
        return False

class GradePermission(permissions.BasePermission, ModulePermissionMixin):
    def has_permission(self, request, view):
        user = request.user
        
        if request.method in permissions.SAFE_METHODS:
            return self.has_module_permission(user, 'grades', 'can_view')
        elif request.method == 'POST':
            # Solo profesores pueden crear calificaciones
            return user.user_type == 'teacher' and self.has_module_permission(user, 'grades', 'can_create')
        return False

    def has_object_permission(self, request, view, obj):
        user = request.user
        
        if request.method in permissions.SAFE_METHODS:
            if user.user_type == 'teacher':
                # Profesores solo ven calificaciones de sus materias
                return obj.subject.teacher == user and self.has_module_permission(user, 'grades', 'can_view')
            elif user.user_type == 'parent':
                # Padres solo ven calificaciones de sus hijos
                return obj.student.parent == user and self.has_module_permission(user, 'grades', 'can_view')
            elif user.user_type == 'admin':
                # Admin puede ver todas
                return self.has_module_permission(user, 'grades', 'can_view')
            return False
        
        elif request.method in ['PUT', 'PATCH']:
            # Solo el profesor de la materia puede modificar calificaciones
            return (
                user.user_type == 'teacher' and
                self.has_module_permission(user, 'grades', 'can_edit') and 
                obj.subject.teacher == user
            )
        
        elif request.method == 'DELETE':
            # Solo admin puede eliminar calificaciones
            return user.user_type == 'admin' and self.has_module_permission(user, 'grades', 'can_delete')
        
        return False