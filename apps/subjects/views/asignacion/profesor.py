import json
from rest_framework import serializers, viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from apps.subjects.models.Curso import Curso
from apps.subjects.models.Teacher import Profesor
from apps.subjects.models.academic import PeriodoAcademico
from apps.subjects.models.grades import AsignacionProfesor
from apps.subjects.models.subject import Materia
from apps.subjects.serializers.asignacion import AsignacionProfesorSerializer
from apps.users.decorators import module_permission_required
from django.views.generic import ListView
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.db.models import Value
from django.db.models import Q, CharField
from django.db.models.functions import Concat
from apps.users.models import Module

class AsignacionProfesorListView(ListView):
    model = AsignacionProfesor
    template_name = 'admin/asignaciones/teacher.html'
    context_object_name = 'asignaciones'
    paginate_by = 10

    @module_permission_required('ASIG_PROF', 'view')
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        # Consulta base con todas las relaciones necesarias
        queryset = AsignacionProfesor.objects.select_related(
            'profesor', 
            'profesor__usuario',
            'materia', 
            'curso', 
            'periodo'
        ).order_by('profesor__usuario__first_name')

        # Obtener y procesar término de búsqueda
        search = self.request.GET.get('search', '').strip()
        if search:
            # Dividir el término de búsqueda en palabras para búsqueda más precisa
            search_terms = search.split()
            
            # Crear consultas Q para cada término
            query = Q()
            for term in search_terms:
                term_query = (
                    Q(profesor__usuario__first_name__icontains=term) |
                    Q(profesor__usuario__last_name__icontains=term) |
                    Q(materia__nombre__icontains=term) |
                    Q(curso__nombre__icontains=term) |
                    Q(periodo__nombre__icontains=term)
                )
                query &= term_query  # Usar AND para múltiples términos
            
            queryset = queryset.filter(query).distinct()

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Verificar permisos
        module = get_object_or_404(Module, code='ASIG_PROF')
        context.update({
            'can_create': self.request.user.has_module_permission(module, 'create'),
            'can_edit': self.request.user.has_module_permission(module, 'edit'),
            'can_delete': self.request.user.has_module_permission(module, 'delete'),
        })

        # Optimizar consultas para los datos JSON
        profesores_data = list(Profesor.objects.select_related('usuario').annotate(
            nombre_completo=Concat(
                'usuario__first_name', 
                Value(' '), 
                'usuario__last_name',
                output_field=CharField()
            )
        ).values('id', 'nombre_completo'))

        # Convertir anotación a formato requerido
        for profesor in profesores_data:
            profesor['nombre'] = profesor.pop('nombre_completo').strip()
        
        # Obtener datos para los demás modelos
        materias_data = list(Materia.objects.values('id', 'nombre'))
        cursos_data = list(Curso.objects.values('id', 'nombre'))
        periodos_data = list(PeriodoAcademico.objects.values('id', 'nombre'))

        # Agregar datos JSON al contexto
        context.update({
            'profesores_json': json.dumps(profesores_data),
            'materias_json': json.dumps(materias_data),
            'cursos_json': json.dumps(cursos_data),
            'periodos_json': json.dumps(periodos_data),
            'search': self.request.GET.get('search', ''),
        })

        return context

class AsignacionProfesorViewSet(viewsets.ModelViewSet):
    queryset = AsignacionProfesor.objects.all()
    serializer_class = AsignacionProfesorSerializer
    filterset_fields = ['profesor', 'materia', 'curso', 'periodo']
    search_fields = [
        'profesor__nombre', 
        'materia__nombre', 
        'curso__nombre', 
        'periodo__nombre'
    ]
    ordering_fields = ['profesor__nombre', 'materia__nombre', 'curso__nombre']
    ordering = ['profesor__nombre']

    def get_queryset(self):
        """
        Optionally restricts the returned assignments,
        by filtering against query parameters in the URL.
        """
        queryset = AsignacionProfesor.objects.select_related(
            'profesor', 
            'materia', 
            'curso', 
            'periodo'
        )
        
        # Add any custom filtering here if needed
        return queryset

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except IntegrityError:
            return Response(
                {"detail": _("Esta asignación ya existe.")},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def by_profesor(self, request):
        """
        Get all assignments for a specific professor
        """
        profesor_id = request.query_params.get('profesor_id')
        if not profesor_id:
            return Response(
                {"detail": _("Se requiere el ID del profesor.")},
                status=status.HTTP_400_BAD_REQUEST
            )

        queryset = self.get_queryset().filter(profesor_id=profesor_id)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_periodo(self, request):
        """
        Get all assignments for a specific academic period
        """
        periodo_id = request.query_params.get('periodo_id')
        if not periodo_id:
            return Response(
                {"detail": _("Se requiere el ID del período.")},
                status=status.HTTP_400_BAD_REQUEST
            )

        queryset = self.get_queryset().filter(periodo_id=periodo_id)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)