from rest_framework import serializers, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from apps.students.serializers.matricula import MatriculaSerializer
from apps.subjects.models.academic import PeriodoAcademico
from apps.subjects.models.subject import Materia
from apps.students.models import Estudiante, Matricula, DetalleMatricula
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.users.decorators import module_permission_required
from django.utils.decorators import method_decorator

class MatriculaTemplateView(LoginRequiredMixin, TemplateView):
    template_name = 'admin/matricula/dashboard.html'
    
    @module_permission_required('MATRICULA', 'view')
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['periodo_actual'] = PeriodoAcademico.objects.filter(
            activo=True
        ).first()
        context['periodos'] = PeriodoAcademico.objects.all().order_by('-nombre')
        return context



class MatriculaViewSet(viewsets.ModelViewSet):
    queryset = Matricula.objects.all()
    serializer_class = MatriculaSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        estudiante_id = self.request.query_params.get('estudiante')
        periodo_id = self.request.query_params.get('periodo')
        
        if estudiante_id:
            queryset = queryset.filter(estudiante_id=estudiante_id)
        if periodo_id:
            queryset = queryset.filter(periodo_id=periodo_id)

        return queryset.select_related(
            'estudiante',
            'estudiante__usuario',
            'periodo'
        ).prefetch_related(
            'detallematricula_set',
            'detallematricula_set__materia'
        )

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            # Check if deletion is allowed (you might want to add custom logic here)
            if instance.detallematricula_set.exists():  # Optional: Prevent deletion if has grades
                instance.delete()
                return Response(
                    {'message': 'Matrícula eliminada exitosamente'},
                    status=status.HTTP_200_OK
                )
            return Response(
                {'error': 'No se puede eliminar una matrícula con calificaciones'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['patch'])
    def update_subjects(self, request, pk=None):
        """
        Update the subjects of an existing enrollment
        """
        matricula = self.get_object()
        materias_ids = request.data.get('materias_ids', [])

        try:
            with transaction.atomic():
                # Remove all existing subjects
                matricula.detallematricula_set.all().delete()
                
                # Add new subjects
                for materia_id in materias_ids:
                    DetalleMatricula.objects.create(
                        matricula=matricula,
                        materia_id=materia_id
                    )

            return Response(
                {'message': 'Materias actualizadas exitosamente'},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )