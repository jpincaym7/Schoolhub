from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from functools import wraps
from apps.users.models import Module

def module_permission_required(module_code, permission_type):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(self, *args, **kwargs):
            # Verificar que el objeto request tiene un atributo 'user'
            request = self.request  # Accede al objeto request desde el ViewSet
            if not hasattr(request, "user"):
                raise AttributeError("El objeto request no tiene un atributo 'user'.")

            # Obtener el módulo por código
            module = get_object_or_404(Module, code=module_code)

            # Verificar si el usuario tiene permiso para el módulo
            if not request.user.has_module_permission(module, permission_type):
                raise PermissionDenied("No tienes permiso para realizar esta acción.")

            # Registrar acceso al módulo
            request.user.log_module_access(module, request)

            # Llamar a la vista original
            return view_func(self, *args, **kwargs)
        return wrapper
    return decorator
