from rest_framework import serializers, viewsets, permissions, status
from rest_framework.decorators import action
from apps.students.models import Behavior, BehaviorSummary
from apps.students.views.behavior.serializers import AcademicPeriodSerializer, BehaviorSerializer, BehaviorSummarySerializer
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.subjects.models import (
    AcademicPeriod,
)
from apps.users.decorators import module_permission_required

MODULE_CODE = 'COMP#1'
class BehaviorManagementView(LoginRequiredMixin, TemplateView):
    template_name = 'behavior/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': _('Gestión de Comportamiento'),
            'api_endpoints': {
                'behavior': '/students/api-behavior/',
                'behavior_summary': '/students/api-summary/',
            }
        })
        return context

class BehaviorViewSet(viewsets.ModelViewSet):
    serializer_class = BehaviorSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['student', 'type', 'academic_period', 'partial_number', 'date']
    search_fields = ['description', 'student__first_name', 'student__last_name']
    ordering_fields = ['date', 'type', 'student__last_name']
    ordering = ['-date']

    def get_queryset(self):
        return Behavior.objects.select_related(
            'student', 'reported_by', 'academic_period'
        ).all()
        
    @module_permission_required(MODULE_CODE, 'view')
    @action(detail=False, methods=['get'])
    def student_behavior(self, request):
        """Obtener comportamientos de un estudiante específico"""
        student_id = request.query_params.get('student_id')
        academic_period_id = request.query_params.get('academic_period_id')
        
        if not student_id or not academic_period_id:
            return Response(
                {'error': _('Se requieren student_id y academic_period_id')},
                status=status.HTTP_400_BAD_REQUEST
            )

        behaviors = self.get_queryset().filter(
            student_id=student_id,
            academic_period_id=academic_period_id
        )
        
        serializer = self.get_serializer(behaviors, many=True)
        return Response(serializer.data)

class BehaviorSummaryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = BehaviorSummarySerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['student', 'academic_period']
    ordering_fields = ['updated_at', 'student__last_name']
    ordering = ['-updated_at']

    def get_queryset(self):
        return BehaviorSummary.objects.select_related(
            'student', 'academic_period'
        ).all()

    @module_permission_required(MODULE_CODE, 'edit')
    @action(detail=False, methods=['post'])
    def recalculate(self, request):
        """Recalcular resúmenes para estudiantes específicos"""
        student_ids = request.data.get('student_ids', [])
        academic_period_id = request.data.get('academic_period_id')

        if not student_ids or not academic_period_id:
            return Response(
                {'error': _('Se requieren student_ids y academic_period_id')},
                status=status.HTTP_400_BAD_REQUEST
            )

        for student_id in student_ids:
            BehaviorSummary.update_for_student(
                student_id=student_id,
                academic_period_id=academic_period_id
            )

        return Response({'status': 'Resúmenes actualizados correctamente'})
    
class AcademicPeriodViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar períodos académicos
    """
    queryset = AcademicPeriod.objects.all()
    serializer_class = AcademicPeriodSerializer