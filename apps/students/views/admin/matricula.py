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

    def destroy(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                instance = self.get_object()
                
                # Check if any subjects have grades
                detalles_con_calificaciones = instance.detallematricula_set.filter(
                    calificacion__isnull=False
                ).distinct().values_list('materia__nombre', flat=True)
                
                if detalles_con_calificaciones.exists():
                    return Response(
                        {
                            'error': f"No se puede eliminar la matrícula porque las siguientes materias tienen calificaciones registradas: {', '.join(detalles_con_calificaciones)}"
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                instance.delete()
                return Response(
                    {
                        'message': 'Matrícula eliminada exitosamente'
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
                
                if materias_removidas:
                    # Check if any of the subjects to be removed have grades
                    materias_con_calificaciones = detalles_actuales.filter(
                        materia_id__in=materias_removidas,
                        calificacion__isnull=False
                    ).distinct().values_list('materia__nombre', flat=True)
                    
                    if materias_con_calificaciones:
                        return Response(
                            {
                                'error': f"No se pueden eliminar las siguientes materias porque tienen calificaciones registradas: {', '.join(materias_con_calificaciones)}"
                            },
                            status=status.HTTP_400_BAD_REQUEST
                        )
                
                # Remove subjects that are not in the new list
                matricula.detallematricula_set.filter(materia_id__in=materias_removidas).delete()
                
                # Add new subjects
                for materia_id in materias_nuevas - materias_actuales:
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