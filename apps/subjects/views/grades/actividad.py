import json
from rest_framework import serializers, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from typing import Dict, Any
from apps.students.models import Student
from apps.subjects.api.activity import ActivitySerializer, ActivityTemplateSerializer, BulkScoreUpdateSerializer
from apps.subjects.models import ActivityTemplate, Activity, AcademicPeriod, Subject
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.db.models import Avg, Count
from django.core.exceptions import ValidationError
from django.contrib import messages
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from rest_framework.decorators import api_view
import logging

#logger
logger = logging.getLogger(__name__)

@api_view(['GET'])
def get_current_academic_period(request):
    """
    Obtiene el período académico actual basado en la fecha
    """
    try:
        # Obtener el año actual
        current_year = timezone.now().year
        
        # Determinar el quimestre actual basado en el mes
        current_month = timezone.now().month
        current_number = 1 if current_month <= 6 else 2
        
        # Formar el año lectivo (ej: "2024-2025")
        school_year = f"{current_year}-{current_year + 1}"
        
        # Obtener o crear el período académico actual
        current_period, created = AcademicPeriod.objects.get_or_create(
            number=current_number,
            school_year=school_year,
        )
        
        return Response({
            'current_period': {
                'id': current_period.id,
                'number': current_period.number,
                'school_year': current_period.school_year
            },
            'message': 'Período académico actual obtenido correctamente'
        })
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

class ActivityTemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar plantillas de actividades y crear actividades en masa
    """
    queryset = ActivityTemplate.objects.all()
    serializer_class = ActivityTemplateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        subject_id = self.request.query_params.get('subject')
        period_id = self.request.query_params.get('academic_period')
        student_id = self.request.query_params.get('student')
        partial = self.request.query_params.get('partial')
        template_id = self.request.query_params.get('template')
        
        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)
        if period_id:
            queryset = queryset.filter(academic_period_id=period_id)
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        if partial:
            queryset = queryset.filter(partial_number=partial)
        if template_id:
            queryset = queryset.filter(template_id=template_id)

        return queryset

    @action(detail=True, methods=['post'])
    def create_activities(self, request, pk=None):
        """
        Crea actividades para múltiples estudiantes basadas en la plantilla
        """
        template = self.get_object()
        student_ids = request.data.get('student_ids', [])

        if not student_ids:
            return Response(
                {'error': _("Debe proporcionar una lista de IDs de estudiantes")},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = BulkActivityCreateSerializer(data={
            'template_id': template.id,
            'student_ids': student_ids
        })

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                activities = serializer.create(serializer.validated_data)
                response_serializer = ActivitySerializer(activities, many=True)
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'])
    def related_activities(self, request, pk=None):
        """
        Obtiene todas las actividades creadas a partir de esta plantilla
        """
        template = self.get_object()
        activities = template.get_all_related_activities()
        serializer = ActivitySerializer(activities, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def students_with_activity(self, request, pk=None):
        """
        Obtiene todos los estudiantes que tienen una actividad creada desde esta plantilla
        """
        template = self.get_object()
        activities = template.get_all_students_with_activity()
        serializer = ActivitySerializer(activities, many=True)
        return Response(serializer.data)

class ActivityViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar actividades individuales y actualizar calificaciones
    """
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'put', 'patch', 'delete'] 
    

    def get_queryset(self):
        queryset = super().get_queryset()
        subject_id = self.request.query_params.get('subject')
        period_id = self.request.query_params.get('academic_period')
        student_id = self.request.query_params.get('student')
        partial = self.request.query_params.get('partial')
        template_id = self.request.query_params.get('template')
        
        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)
        if period_id:
            queryset = queryset.filter(academic_period_id=period_id)
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        if partial:
            queryset = queryset.filter(partial_number=partial)
        if template_id:
            queryset = queryset.filter(template_id=template_id)
        
        return queryset

    def create(self, request, *args, **kwargs):
        """
        Sobrescribe el método create para manejar la creación con plantilla
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            with transaction.atomic():
                instance = serializer.create(serializer.validated_data)
                headers = self.get_success_headers(serializer.data)
                return Response(
                    self.get_serializer(instance).data,
                    status=status.HTTP_201_CREATED,
                    headers=headers
                )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def update(self, request, *args, **kwargs):
        """
        Sobrescribe el método update para permitir solo actualización de calificación
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        if not partial and set(request.data.keys()) - {'score'}:
            return Response(
                {'error': _("Solo se permite actualizar la calificación")},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def bulk_update_scores(self, request):
        """
        Actualiza calificaciones en masa para actividades de una plantilla
        """
        logger.info('Iniciando la actualización en masa de calificaciones')

        template_id = request.data.get('template_id')
        scores_data = request.data.get('scores', [])

        if not template_id or not scores_data:
            logger.warning('Faltan parámetros: template_id o scores')
            return Response(
                {'error': _("Se requiere template_id y scores")},
                status=status.HTTP_400_BAD_REQUEST
            )

        logger.info(f'Template ID recibido: {template_id}')
        template = get_object_or_404(ActivityTemplate, pk=template_id)

        # Añadir template_id a cada item de scores_data
        for score_data in scores_data:
            score_data['template_id'] = template_id
            logger.debug(f'Item actualizado: {score_data}')

        serializer = BulkScoreUpdateSerializer(data=scores_data, many=True)
        if not serializer.is_valid():
            logger.error(f'Errores en la validación del serializador: {serializer.errors}')
            return Response(
                {'error': _("Los datos de las calificaciones no son válidos")},
                status=status.HTTP_400_BAD_REQUEST
            )

        logger.info('Datos de calificaciones validados correctamente')

        try:
            with transaction.atomic():
                updated_activities = Activity.bulk_update_scores(
                    template, 
                    serializer.validated_data
                )
                logger.info(f'Actividades actualizadas: {len(updated_activities)}')

                response_serializer = ActivitySerializer(updated_activities, many=True)
                return Response(response_serializer.data)
        except Exception as e:
            logger.error(f'Error al realizar la actualización en masa: {str(e)}')
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )