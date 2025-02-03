from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.db.models import Prefetch
from apps.subjects.models.academic import PeriodoAcademico
from apps.subjects.models.activity import PromedioAnual, PromedioTrimestre
from apps.subjects.serializers.calificaciones import PromedioAnualSerializer, PromedioTrimestreSerializer

class CalificacionesEstudianteViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PromedioAnualSerializer
    
    def get_queryset(self):
        # Obtener el estudiante actual
        estudiante = self.request.user.estudiante
        # Obtener el período académico actual
        periodo_actual = PeriodoAcademico.objects.filter(activo=True).first()
        
        return PromedioAnual.objects.filter(
            detalle_matricula__matricula__estudiante=estudiante,
            detalle_matricula__matricula__periodo=periodo_actual
        ).select_related(
            'detalle_matricula__materia',
            'detalle_matricula__matricula__estudiante'
        )
    
    @action(detail=True, methods=['get'])
    def detalle_trimestres(self, request, pk=None):
        promedio_anual = self.get_object()
        trimestres = PromedioTrimestre.objects.filter(
            detalle_matricula=promedio_anual.detalle_matricula
        ).select_related('trimestre')
        
        serializer = PromedioTrimestreSerializer(trimestres, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def detalle_calificaciones(self, request, pk=None):
        promedio_anual = self.get_object()
        calificaciones = Calificacion.objects.filter(
            detalle_matricula=promedio_anual.detalle_matricula
        ).select_related('parcial')
        
        serializer = CalificacionSerializer(calificaciones, many=True)
        return Response(serializer.data)