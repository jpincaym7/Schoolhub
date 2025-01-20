from rest_framework import viewsets, permissions
from apps.users.models import Module, ModulePermission
from .serializers import ModuleSerializer, ModulePermissionSerializer
from rest_framework.response import Response
from rest_framework.decorators import action
from apps.users.permissions import IsAdminUser, IsAdminUserManagement  # Importar el permiso personalizado

class ModuleViewSet(viewsets.ModelViewSet):
    """
    CRUD para gestionar módulos
    """
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]  # Usar permiso personalizado

    def get_permissions(self):
        """
        Modificar permisos según el tipo de acción que se realice.
        """
        if self.action in ['create', 'update', 'destroy']:
            return [permissions.IsAuthenticated(), IsAdminUser()]  # Solo admin puede crear/actualizar/eliminar
        return super().get_permissions()  # Para acciones GET, puede ser un usuario autenticado

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        module = self.get_object()
        module.is_active = True
        module.save()
        return Response({'status': 'Modulo activado'})

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        module = self.get_object()
        module.is_active = False
        module.save()
        return Response({'status': 'Modulo desactivado'})


class ModulePermissionViewSet(viewsets.ModelViewSet):
    """
    CRUD para gestionar permisos por módulo
    """
    queryset = ModulePermission.objects.all()
    serializer_class = ModulePermissionSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUserManagement]
    pagination_class = None

    def get_permissions(self):
        if self.action in ['create', 'update', 'destroy']:
            return [permissions.IsAuthenticated(), IsAdminUser()]
        return super().get_permissions()

    @action(detail=True, methods=['post'])
    def grant_permission(self, request, pk=None):
        permission = self.get_object()
        user_type = request.data.get('user_type')
        
        if not user_type:
            return Response({"error": "Debe especificar un tipo de usuario"}, status=400)
        
        permission.user_type = user_type
        permission.can_view = True
        permission.save()
        return Response({'status': f'Permiso concedido para el tipo de usuario: {user_type}'})

    @action(detail=True, methods=['post'])
    def revoke_permission(self, request, pk=None):
        permission = self.get_object()
        permission.can_view = False
        permission.save()
        return Response({'status': 'Permiso revocado'})