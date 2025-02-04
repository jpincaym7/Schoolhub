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
from apps.subjects.models.activity import Calificacion, PromedioAnual, PromedioTrimestre
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
            with transaction.atomic():
                instance = self.get_object()
                detalles = instance.detallematricula_set.all()
                
                # Delete all related grades and averages
                for detalle in detalles:
                    # Delete individual grades (Calificacion)
                    Calificacion.objects.filter(detalle_matricula=detalle).delete()
                    
                    # Delete trimester averages (PromedioTrimestre)
                    PromedioTrimestre.objects.filter(detalle_matricula=detalle).delete()
                    
                    # Delete yearly average (PromedioAnual)
                    PromedioAnual.objects.filter(detalle_matricula=detalle).delete()
                
                # Finally, delete the enrollment and its details
                instance.delete()  # This will also delete DetalleMatricula due to CASCADE
                
                return Response(
                    {
                        'message': 'Matrícula y calificaciones relacionadas eliminadas exitosamente'
                    },
                    status=status.HTTP_200_OK
                )
                
        except Exception as e:
            return Response(
                {
                    'error': f'Error al eliminar la matrícula: {str(e)}'
                },
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
                # Get current subjects
                detalles_actuales = matricula.detallematricula_set.all()
                materias_actuales = set(detalles_actuales.values_list('materia_id', flat=True))
                materias_nuevas = set(materias_ids)
                
                # Find subjects that will be removed
                materias_removidas = materias_actuales - materias_nuevas
                
                # Delete grades for removed subjects
                for detalle in detalles_actuales.filter(materia_id__in=materias_removidas):
                    # Delete individual grades
                    Calificacion.objects.filter(detalle_matricula=detalle).delete()
                    
                    # Delete trimester averages
                    PromedioTrimestre.objects.filter(detalle_matricula=detalle).delete()
                    
                    # Delete yearly average
                    PromedioAnual.objects.filter(detalle_matricula=detalle).delete()
                
                # Remove all existing subjects that are not in the new list
                matricula.detallematricula_set.filter(materia_id__in=materias_removidas).delete()
                
                # Add new subjects
                for materia_id in materias_nuevas - materias_actuales:
                    DetalleMatricula.objects.create(
                        matricula=matricula,
                        materia_id=materia_id
                    )

            return Response(
                {'message': 'Materias y calificaciones actualizadas exitosamente'},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )