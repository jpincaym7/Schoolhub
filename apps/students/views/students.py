from django.urls import reverse_lazy
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from apps.users.decorators import module_permission_required
from apps.students.serializer import StudentSerializer
from apps.students.models import Student
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

class StudentDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'students/dashboard.html'
    login_url = reverse_lazy('users:login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['module_code'] = 'Estudiantes'  # Para verificación de permisos en el template
        context['page_title'] = 'Gestión de Estudiantes'
        
        module_permissions = self.request.user.get_module_permissions(module='Estudiantes')
        context['permissions'] = module_permissions
        print(context) 
        return context

class StudentViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar estudiantes con permisos basados en módulos.
    Implementa operaciones CRUD con validaciones de permisos por módulo
    y manejo de transacciones.
    """
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]
    MODULE_CODE = 'STUDENTS#1'  # Código del módulo para permisos
    queryset = Student.objects.all()
    
    
    def get_queryset(self):
        """
        Retorna el queryset base filtrado por estudiantes activos.
        Si el usuario es un padre, solo ve sus estudiantes.
        """
        queryset = Student.objects.filter(is_active=True)
        if self.request.user.user_type == 'teacher':
            return queryset.filter()
        return queryset

    @module_permission_required(MODULE_CODE, 'view')
    def list(self, request, *args, **kwargs):
        """Lista todos los estudiantes según los permisos del usuario."""
        return super().list(request, *args, **kwargs)

    @module_permission_required(MODULE_CODE, 'view')
    def retrieve(self, request, *args, **kwargs):
        """Obtiene un estudiante específico."""
        return super().retrieve(request, *args, **kwargs)

    @module_permission_required(MODULE_CODE, 'create')
    def create(self, request, *args, **kwargs):
        """
        Crea un nuevo estudiante con validaciones de permisos y transacciones.
        """
        with transaction.atomic():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Si es padre, asignar automáticamente como representante
            if request.user.user_type == 'parent':
                serializer.validated_data['parent'] = request.user
            
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(
                serializer.data, 
                status=status.HTTP_201_CREATED, 
                headers=headers
            )

    @module_permission_required(MODULE_CODE, 'edit')
    def update(self, request, *args, **kwargs):
        """
        Actualiza un estudiante existente con validaciones.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Verificar que si es padre, solo pueda editar sus propios estudiantes
        if request.user.user_type == 'parent' and instance.parent != request.user:
            raise PermissionDenied(
                _("No tienes permiso para editar este estudiante.")
            )

        with transaction.atomic():
            serializer = self.get_serializer(
                instance, 
                data=request.data, 
                partial=partial
            )
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

            return Response(serializer.data)

    @module_permission_required(MODULE_CODE, 'edit')
    def partial_update(self, request, *args, **kwargs):
        """Actualización parcial de un estudiante."""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    @module_permission_required(MODULE_CODE, 'delete')
    def destroy(self, request, *args, **kwargs):
        """
        Realiza un borrado suave del estudiante.
        """
        instance = self.get_object()
        
        # Verificar que si es padre, solo pueda eliminar sus propios estudiantes
        if request.user.user_type == 'parent' and instance.parent != request.user:
            raise PermissionDenied(
                _("No tienes permiso para eliminar este estudiante.")
            )

        with transaction.atomic():
            instance.is_active = False
            instance.save()
            return Response(
                {"message": _("Estudiante eliminado correctamente.")},
                status=status.HTTP_200_OK
            )

    def perform_create(self, serializer):
        """
        Método auxiliar para la creación de estudiantes.
        """
        serializer.save()

    def perform_update(self, serializer):
        """
        Método auxiliar para la actualización de estudiantes.
        """
        serializer.save()