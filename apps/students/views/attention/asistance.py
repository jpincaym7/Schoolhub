from rest_framework import serializers, viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.translation import gettext_lazy as _
from datetime import date, datetime
from apps.students.models import Attendance, Student
from apps.students.views.attention.serializers import AttendanceBulkSerializer, AttendanceSerializer
from rest_framework.exceptions import ValidationError
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count
from django.db.models.functions import Cast
from django.db.models import FloatField

class AttendanceTemplateView(LoginRequiredMixin, TemplateView):
    template_name = 'students/dashboard-attendance.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener parámetros de filtro
        start_date = self.request.GET.get('start_date', (timezone.now() - timedelta(days=30)).date())
        end_date = self.request.GET.get('end_date', timezone.now().date())
        selected_status = self.request.GET.get('status', '')
        
        # Query base
        queryset = Attendance.objects.select_related('student')
        
        # Aplicar filtros
        if start_date and end_date:
            queryset = queryset.filter(date__range=[start_date, end_date])
        if selected_status:
            queryset = queryset.filter(status=selected_status)
            
        # Estadísticas generales
        total_records = queryset.count()
        status_distribution = queryset.values('status').annotate(
            count=Count('id'),
            percentage=Cast(Count('id') * 100.0 / total_records, FloatField())
        ).order_by('-count')
        
        # Últimas asistencias registradas
        latest_attendances = queryset.order_by('-date', '-created_at')[:10]
        for latest in latest_attendances:
            print(latest.date)
        
        # Estudiantes con más ausencias
        students_with_absences = queryset.filter(status='absent').values(
            'student__first_name',
            'student__last_name'
        ).annotate(
            total_absences=Count('id')
        ).order_by('-total_absences')[:5]
        
        students = Student.objects.filter(is_active=True)
        
        context.update({
            'start_date': start_date,
            'end_date': end_date,
            'selected_status': selected_status,
            'total_records': total_records,
            'status_distribution': status_distribution,
            'latest_attendances': latest_attendances,
            'students_with_absences': students_with_absences,
            'status_choices': dict(Attendance.status.field.choices),
            'today': datetime.now(),
            'students': students
        })
        
        return context
    

class AttendanceViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar asistencias.
    
    list:
        Retorna una lista paginada de asistencias.
    
    create:
        Crea una nueva asistencia.
        
    retrieve:
        Retorna los detalles de una asistencia específica.
        
    update:
        Actualiza una asistencia existente.
        
    partial_update:
        Actualiza parcialmente una asistencia existente.
        
    destroy:
        Elimina una asistencia existente.
    """
    queryset = Attendance.objects.select_related('student').all()
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['date', 'status', 'student']
    search_fields = ['student__first_name', 'student__last_name', 'comments']
    ordering_fields = ['date', 'created_at', 'updated_at']
    ordering = ['-date']

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtro por rango de fechas
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date and end_date:
            queryset = queryset.filter(date__range=[start_date, end_date])
        
        return queryset

    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """
        Crear múltiples registros de asistencia en una sola petición
        """
        serializer = AttendanceBulkSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            created_attendances = []
            errors = []

            # Si hay estudiantes para procesar (después de las validaciones)
            if data['student_ids']:
                for student_id in data['student_ids']:
                    try:
                        attendance = Attendance(
                            student_id=student_id,
                            date=data['date'],
                            status=data['status'],
                            comments=data.get('comments', '')
                        )
                        attendance.full_clean()
                        attendance.save()
                        created_attendances.append(attendance)
                    except Exception as e:
                        errors.append({
                            'student_id': student_id,
                            'error': str(e)
                        })

            response_data = {
                'created': self.get_serializer(created_attendances, many=True).data,
                'errors': errors
            }
            
            # Si se crearon algunos registros, devolver 201, si no, 400
            status_code = status.HTTP_201_CREATED if created_attendances else status.HTTP_400_BAD_REQUEST
            return Response(response_data, status=status_code)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Obtener estadísticas de asistencia
        """
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        student_id = request.query_params.get('student_id')

        queryset = self.get_queryset()
        if student_id:
            queryset = queryset.filter(student_id=student_id)

        if start_date and end_date:
            queryset = queryset.filter(date__range=[start_date, end_date])

        total_records = queryset.count()
        status_counts = queryset.values('status').annotate(
            count=Count('id'),
            percentage=Cast(Count('id') * 100.0 / total_records, FloatField())
        )

        return Response({
            'total_records': total_records,
            'status_distribution': status_counts
        })

    def perform_create(self, serializer):
        """
        Personalizar la creación de instancias
        """
        serializer.save()

    def handle_exception(self, exc):
        """
        Manejar excepciones de manera personalizada
        """
        if isinstance(exc, ValidationError):
            return Response(
                {'detail': str(exc)},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().handle_exception(exc)