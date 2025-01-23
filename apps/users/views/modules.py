from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from apps.users.models import Module, ModulePermission, UserModuleAccess
from apps.users.views.assingment import ModuleSerializer, ModulePermissionSerializer

class ModuleViewSet(viewsets.ModelViewSet):
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter modules based on user permissions"""
        user = self.request.user
        accessible_modules = []
        
        for module in super().get_queryset():
            permissions = user.get_module_permissions(module)
            if permissions['can_view']:
                accessible_modules.append(module.id)
        
        return super().get_queryset().filter(id__in=accessible_modules)

    @action(detail=False, methods=['get'])
    def user_permissions(self, request):
        """Get all permissions for the current user"""
        user = request.user
        modules = self.get_queryset()
        permissions = {}
        
        for module in modules:
            permissions[module.id] = user.get_module_permissions(module)
        
        return Response(permissions)

    @action(detail=True, methods=['post'])
    def log_access(self, request, pk=None):
        """Log user access to a module"""
        module = self.get_object()
        user = request.user
        
        user.log_module_access(module, request)
        return Response({'status': 'access logged'})