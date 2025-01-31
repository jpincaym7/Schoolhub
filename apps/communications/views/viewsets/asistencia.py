from django.db.models import Q, Count, Case, When, IntegerField
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from apps.communications.models import Asistencia
from apps.communications.views.serializers.puntual import AsistenciaCreateUpdateSerializer, AsistenciaMasivaSerializer, AsistenciaSerializer
from apps.students.models import Matricula
from apps.students.serializers.matricula import MatriculaSerializer
from django.utils import timezone
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from datetime import datetime, timedelta


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
    
    def is_weekend(self, date):
        """Check if a given date is weekend (Saturday or Sunday)."""
        return date.weekday() in [5, 6]  # 5 = Saturday, 6 = Sunday
    
    def get_working_days(self, start_date, end_date):
        """Get list of working days between two dates, excluding weekends."""
        working_days = []
        current_date = start_date
        
        while current_date <= end_date:
            if not self.is_weekend(current_date):
                working_days.append(current_date)
            current_date += timedelta(days=1)
            
        return working_days

    def get_queryset(self):
        user = self.request.user
        base_queryset = Asistencia.objects.all()
        
        if user.is_staff:
            return base_queryset
        elif hasattr(user, 'profesor'):
            return base_queryset.filter(
                matricula__detallematricula_set__materia__profesor=user.profesor
            )
        return Asistencia.objects.none()

    @action(detail=False, methods=['GET'])
    def lista(self, request):
        """List attendance records grouped by date, excluding weekends."""
        asistencias = Asistencia.objects.exclude(
            fecha__week_day__in=[1, 7]  # Exclude Sunday (1) and Saturday (7)
        ).values('fecha').annotate(
            total_estudiantes=Count('matricula', distinct=True),
            presentes=Count(Case(
                When(asistio=True, then=1),
                output_field=IntegerField()
            ))
        ).order_by('-fecha')
        
        return Response({
            'results': list(asistencias)
        })

    @action(detail=False, methods=['DELETE'])
    def eliminar(self, request):
        fecha = request.data.get('fecha')
        
        if not fecha:
            return Response({
                'error': 'Fecha es requerida'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
            
            if self.is_weekend(fecha_obj):
                return Response({
                    'error': 'No se pueden eliminar registros de fines de semana'
                }, status=status.HTTP_400_BAD_REQUEST)
            
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

        try:
            # Aseguramos que la fecha se procese sin ajuste de zona horaria
            fecha_obj = datetime.strptime(fecha, '%Y-%m-%d')
            fecha_obj = timezone.make_aware(fecha_obj)
            fecha_obj = fecha_obj.date()  # Convertimos a solo fecha
            
            print(f"Processing date: {fecha_obj}")  # Para debugging

            # Validar que no sea fin de semana
            if self.is_weekend(fecha_obj):
                return Response({
                    'error': 'No se pueden registrar asistencias en fines de semana'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Validar fecha futura
            if fecha_obj > timezone.now().date():
                return Response({
                    'error': 'No se pueden registrar asistencias para fechas futuras'
                }, status=status.HTTP_400_BAD_REQUEST)

            registros_exitosos = []
            errores = []

            with transaction.atomic():
                for item in matriculas_asistencias:
                    try:
                        self.procesar_asistencia_individual(
                            item, fecha_obj, registros_exitosos, errores
                        )
                    except Exception as e:
                        errores.append({
                            'matricula': item.get('matricula'),
                            'error': str(e)
                        })

            return self.generar_respuesta_registro(registros_exitosos, errores)

        except Exception as e:
            return Response({
                'error': f'Error en el proceso de registro masivo: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['POST'])
    def registro_masivo_rango(self, request):
        serializer = AsistenciaMasivaSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Aseguramos que las fechas se procesen sin ajuste de zona horaria
        fecha_inicio = timezone.make_aware(
            datetime.strptime(request.data['fecha_inicio'], '%Y-%m-%d')
        ).date()
        fecha_fin = timezone.make_aware(
            datetime.strptime(request.data['fecha_fin'], '%Y-%m-%d')
        ).date()
        
        print(f"Processing range: {fecha_inicio} to {fecha_fin}")  # Para debugging
        
        matriculas = serializer.validated_data['matriculas']
        asistencias = serializer.validated_data['asistencias']

        # Obtener días laborables en el rango
        dias_laborables = self.get_working_days(fecha_inicio, fecha_fin)
        
        if not dias_laborables:
            return Response({
                'error': 'No hay días laborables en el rango seleccionado'
            }, status=status.HTTP_400_BAD_REQUEST)

        registros_exitosos = []
        errores = []

        try:
            with transaction.atomic():
                for fecha in dias_laborables:
                    for matricula_id in matriculas:
                        try:
                            # Procesar asistencia para cada día laborable
                            self.procesar_asistencia_rango(
                                matricula_id,
                                fecha,
                                asistencias,
                                registros_exitosos,
                                errores
                            )
                        except Exception as e:
                            errores.append({
                                'matricula': matricula_id,
                                'fecha': fecha,
                                'error': str(e)
                            })

            return self.generar_respuesta_registro(
                registros_exitosos,
                errores,
                mensaje_adicional=f'Procesados {len(dias_laborables)} días laborables'
            )

        except Exception as e:
            return Response({
                'error': f'Error en el proceso de registro masivo: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def procesar_asistencia_individual(self, item, fecha, registros_exitosos, errores):
        """Procesa un registro individual de asistencia."""
        matricula_id = item.get('matricula')
        asistencias = item.get('asistencias', [])

        # Eliminar registros existentes
        Asistencia.objects.filter(
            matricula_id=matricula_id,
            fecha=fecha
        ).delete()

        for asistencia_data in asistencias:
            serializer = self.get_serializer(data={
                'matricula': matricula_id,
                'fecha': fecha,
                'asistio': asistencia_data.get('asistio', True),
                'justificacion': asistencia_data.get('justificacion', '')
            })
            
            if serializer.is_valid():
                registro = serializer.save()
                registros_exitosos.append(registro)
            else:
                errores.append({
                    'matricula': matricula_id,
                    'errores': serializer.errors
                })

    def procesar_asistencia_rango(self, matricula_id, fecha, asistencias, registros_exitosos, errores):
        """Procesa la asistencia para un día específico dentro del rango."""
        try:
            # Eliminar registro existente si existe
            Asistencia.objects.filter(
                matricula_id=matricula_id,
                fecha=fecha
            ).delete()

            # Procesar cada asistencia
            for asistencia_data in asistencias:
                serializer = self.get_serializer(data={
                    'matricula': matricula_id,
                    'fecha': fecha,
                    'asistio': asistencia_data.get('asistio', True),
                    'justificacion': asistencia_data.get('justificacion', '')
                })
                
                if serializer.is_valid():
                    registro = serializer.save()
                    registros_exitosos.append(registro)
                else:
                    errores.append({
                        'matricula': matricula_id,
                        'fecha': fecha,
                        'errores': serializer.errors
                    })
        except Exception as e:
            errores.append({
                'matricula': matricula_id,
                'fecha': fecha,
                'error': str(e)
            })

    def generar_respuesta_registro(self, registros_exitosos, errores, mensaje_adicional=''):
        """Genera una respuesta estandarizada para los registros de asistencia."""
        mensaje = f'Se registraron {len(registros_exitosos)} asistencias correctamente'
        if mensaje_adicional:
            mensaje = f'{mensaje}. {mensaje_adicional}'

        return Response({
            'mensaje': mensaje,
            'registros': self.get_serializer(registros_exitosos, many=True).data,
            'errores': errores
        }, status=status.HTTP_201_CREATED if not errores else status.HTTP_206_PARTIAL_CONTENT)