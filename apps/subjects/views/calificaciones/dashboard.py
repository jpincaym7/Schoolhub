from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from apps.subjects.models.activity import Calificacion, PromedioAnual
from apps.subjects.serializers.calificaciones import CalificacionSerializer, PromedioAnualSerializer

class CalificacionViewSet(viewsets.ModelViewSet):
    serializer_class = CalificacionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['detalle_matricula', 'asignacion_profesor', 'parcial']
    ordering_fields = ['parcial', 'fecha_registro', 'promedio_final']

    def get_queryset(self):
        # If user is a teacher, only show their assigned grades
        if hasattr(self.request.user, 'profesor'):
            return Calificacion.objects.filter(
                asignacion_profesor__profesor=self.request.user.profesor
            )
        return Calificacion.objects.all()

    @action(detail=False, methods=['post'])
    def crear_calificaciones_periodo(self, request):
        periodo_id = request.data.get('periodo_id')
        if not periodo_id:
            return Response(
                {"error": "Debe proporcionar un periodo_id"},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            Calificacion.crear_calificaciones_periodo(periodo_id)
            return Response({"message": "Calificaciones creadas exitosamente"})
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class PromedioAnualViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PromedioAnualSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['detalle_matricula']
    ordering_fields = ['promedio_final']

    def get_queryset(self):
        if hasattr(self.request.user, 'profesor'):
            return PromedioAnual.objects.filter(
                detalle_matricula__materia__in=self.request.user.profesor.materias.all()
            )
        return PromedioAnual.objects.all()
