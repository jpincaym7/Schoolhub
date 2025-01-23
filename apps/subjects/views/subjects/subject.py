from django.shortcuts import render
from django.core.exceptions import PermissionDenied
from django.utils.safestring import mark_safe
from apps.subjects.models.Especialidad import Especialidad
from apps.subjects.models.subject import Materia
from apps.subjects.serializers.subject import MateriaSerializer
from apps.users.models import Module, User
from apps.users.decorators import module_permission_required
import json
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter

def materia_list(request):
    try:
        # Obtener el módulo de materias
        module = Module.objects.get(code='MAT#123')
        
        # Verificar permiso básico de visualización
        if not request.user.has_module_permission(module, 'view'):
            raise PermissionDenied("No tienes permiso para ver este módulo.")
        
        # Determinar si el usuario puede editar
        editing = request.user.user_type == 'teacher'
        
        # Obtener permisos
        permissions = {
            'can_view': request.user.has_module_permission(module, 'view'),
            'can_create': request.user.has_module_permission(module, 'create'),
            'can_edit': request.user.has_module_permission(module, 'edit'),
            'can_delete': request.user.has_module_permission(module, 'delete')
        }
        
        Especialidades = Especialidad.objects.all()
        
        print(permissions)

        # Obtener lista de profesores
        teachers = User.objects.filter(user_type='teacher').order_by('first_name', 'last_name')
        teachers_data = [
            {
                'id': teacher.id,
                'first_name': teacher.first_name or '',
                'last_name': teacher.last_name or '',
                'email': teacher.email or ''
            }
            for teacher in teachers
        ]

        # Registrar el acceso al módulo
        request.user.log_module_access(module, request)
        
        context = {
            'teachers': teachers,
            'teachers_json': json.dumps(teachers_data),
            'permissions_json': json.dumps(permissions),
            'editing': editing,
            'especialidades': Especialidades
        }

        return render(request, 'admin/materias/dashboard.html', context)

    except Exception as e:
        print(f"Error: {str(e)}")
        context = {
            'teachers': [],
            'teachers_json': json.dumps([]),
            'permissions_json': json.dumps({
                'can_view': False,
                'can_create': False,
                'can_edit': False,
                'can_delete': False
            })
        }
        return render(request, 'materias/dashboard.html', context)

class MateriaViewSet(viewsets.ModelViewSet):
    queryset = Materia.objects.all()
    serializer_class = MateriaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['especialidad', 'horas_semanales']
    search_fields = ['nombre', 'codigo']
    ordering_fields = ['nombre', 'codigo', 'horas_semanales']
    ordering = ['nombre']

    def get_queryset(self):
        queryset = Materia.objects.all()
        
        # Si el usuario es profesor, solo ver sus materias asignadas
        if self.request.user.user_type == "teacher":
            queryset = queryset.filter(especialidad__teachers=self.request.user)
        # Si es superusuario, ver todas las materias
        elif self.request.user.is_superuser:
            return queryset
            
        return queryset

    @module_permission_required('MAT#123', 'view')
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @module_permission_required('MAT#123', 'view')
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @module_permission_required('MAT#123', 'create')
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @module_permission_required('MAT#123', 'edit')
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @module_permission_required('MAT#123', 'edit')
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @module_permission_required('MAT#123', 'delete')
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
    