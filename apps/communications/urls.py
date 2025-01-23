from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.communications.views.dashboard import StudentAttendanceView
from apps.communications.views.viewsets.asistencia import AsistenciaDashboardView, AsistenciaViewSet, MatriculaViewSet

app_name = 'communications'

router = DefaultRouter()
router.register(r'api-consult', MatriculaViewSet, basename='consult')
router.register(r'asistencias', AsistenciaViewSet, basename='asistencias')

urlpatterns = [
    path('dashboard/asistencias/', AsistenciaDashboardView.as_view(), name='asistencia_dashboard'),
    path('mi-asistencia/', StudentAttendanceView.as_view(), name='student_attendance'),
    # Rutas para los endpoints de la API
    path('', include(router.urls)),
]