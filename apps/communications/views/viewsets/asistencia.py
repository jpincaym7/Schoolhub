from django.db.models import Q, Count, Case, When, IntegerField
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from apps.communications.models import Asistencia
from apps.communications.views.serializers.puntual import AsistenciaCreateUpdateSerializer, AsistenciaSerializer
from apps.students.models import Matricula
from apps.students.serializers.matricula import MatriculaSerializer
from django.utils import timezone
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin


class AsistenciaDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'attendance/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Análisis de asistencia por matrícula (para todos los estudiantes)
        asistencia_analisis = Matricula.objects.annotate(
            total_clases=Count('asistencia'),
            asistencias_confirmadas=Count(Case(
                When(asistencia__asistio=True, then=1),
                output_field=IntegerField()
            ))
        )
        
        print(asistencia_analisis)

        context['asistencia_analisis'] = asistencia_analisis
        return context

class MatriculaViewSet(viewsets.ModelViewSet):
    queryset = Matricula.objects.select_related(
        'estudiante', 'periodo'
    ).prefetch_related('detallematricula_set__materia')
    serializer_class = MatriculaSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['estudiante', 'periodo']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Optional date and attendance filter
        fecha = self.request.query_params.get('fecha')
        sin_asistencia = self.request.query_params.get('sin_asistencia', 'false')
        
        if fecha and sin_asistencia == 'true':
            # Exclude matriculas with attendance already registered for the given date
            matriculas_con_asistencia = Asistencia.objects.filter(
                fecha=fecha
            ).values_list('matricula_id', flat=True)
            
            queryset = queryset.exclude(id__in=matriculas_con_asistencia)
        
        return queryset

class AsistenciaViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = AsistenciaCreateUpdateSerializer
    
    def get_queryset(self):
        # Filtrado inteligente basado en rol de usuario
        user = self.request.user
        if user.is_staff:
            return Asistencia.objects.all()
        elif hasattr(user, 'profesor'):
            # Solo asistencias de materias del profesor
            return Asistencia.objects.filter(
                matricula__detallematricula_set__materia__profesor=user.profesor
            )
        return Asistencia.objects.none()

    @action(detail=False, methods=['GET'])
    def lista(self, request):
        # Listar registros de asistencia agrupados por fecha
        asistencias_por_fecha = Asistencia.objects.values('fecha').annotate(
            total_estudiantes=Count('matricula', distinct=True),
            presentes=Count(Case(When(asistio=True, then=1), output_field=IntegerField()))
        ).order_by('-fecha')
        
        return Response({
            'results': list(asistencias_por_fecha)
        })

    @action(detail=False, methods=['DELETE'])
    def eliminar(self, request):
        fecha = request.data.get('fecha')
        
        if not fecha:
            return Response({
                'error': 'Fecha es requerida'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Delete all attendance records for the specific date
            registros_eliminados, _ = Asistencia.objects.filter(fecha=fecha).delete()
            
            return Response({
                'mensaje': f'Se eliminaron {registros_eliminados} registros de asistencia para la fecha {fecha}',
                'fecha': fecha
            })
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['POST'])
    def registro_masivo(self, request):
        fecha = request.data.get('fecha')
        matriculas_asistencias = request.data.get('matriculas_asistencias', [])

        if not all([fecha, matriculas_asistencias]):
            return Response({
                'error': 'Datos incompletos para registro masivo'
            }, status=status.HTTP_400_BAD_REQUEST)

        registros_exitosos = []
        errores = []

        for item in matriculas_asistencias:
            matricula_id = item.get('matricula')
            asistencias = item.get('asistencias', [])

            try:
                # Delete existing records for this matricula and date first
                Asistencia.objects.filter(
                    matricula_id=matricula_id, 
                    fecha=fecha
                ).delete()

                for asistencia in asistencias:
                    serializer = self.get_serializer(data={
                        'matricula': matricula_id,
                        'fecha': fecha,
                        'asistio': asistencia.get('asistio', True),
                        'justificacion': asistencia.get('justificacion', '')
                    })
                    serializer.is_valid(raise_exception=True)
                    registros_exitosos.append(serializer.save())

            except Exception as e:
                errores.append({
                    'matricula': matricula_id,
                    'error': str(e)
                })

        return Response({
            'mensaje': f'Registros procesados: {len(registros_exitosos)}',
            'registros': self.get_serializer(registros_exitosos, many=True).data,
            'errores': errores
        }, status=status.HTTP_201_CREATED if not errores else status.HTTP_206_PARTIAL_CONTENT)