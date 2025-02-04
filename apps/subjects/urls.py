from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.students.views.course.horarios import get_office_hours, office_hours_view
from apps.subjects.views.asignacion.profesor import AsignacionProfesorListView, AsignacionProfesorViewSet
from apps.subjects.views.calificaciones.dashboard import CalificacionViewSet, PromedioAnualViewSet
from apps.subjects.views.calificaciones.deber import CalificacionesView
from apps.subjects.views.calificaciones.manage import CalManageView, CalificacionesAPIView, CalificacionesBulkAPIView, CalificacionesExcelAPIView
from apps.subjects.views.curso.curso import CursoManagementView, CursoViewSet
from apps.subjects.views.dashboards.asignaciones import TeacherDashboardView
from apps.subjects.views.dashboards.students import ListaEstudiantesView
from apps.subjects.views.horario.dashboard import HorarioAtencionViewSet, HorariosAtencionView
from apps.subjects.views.subjects.subject import MateriaViewSet, materia_list

router = DefaultRouter()
router.register(r'api-subjects', MateriaViewSet)
router.register(r'api-cursos', CursoViewSet)
router.register(r'api-asignaciones', AsignacionProfesorViewSet)
router.register(r'horarios-atencion', HorarioAtencionViewSet, basename='horario-atencion')
router.register(r'api-calificaciones', CalificacionViewSet, basename='calificacion')
router.register(r'promedios-anuales', PromedioAnualViewSet, basename='promedio-anual')

app_name = 'subjects'

urlpatterns = [
    path('', include(router.urls)),
    path('subject-list/', materia_list, name='subject_list'),
    path('cursos-list/', CursoManagementView.as_view(), name='cursos-list'),
    path('asignaciones/', AsignacionProfesorListView.as_view(), name='list-asignaciones'),
    path('dashboard-horarios/', HorariosAtencionView.as_view(), name='api-horarios'),
    path('profesor/dashboard/', TeacherDashboardView.as_view(), name='teacher_dashboard'),
    path('estudiante/<int:estudiante_id>/periodo/<int:periodo_id>/calificaciones/',
     CalificacionesView.as_view(), 
     name='calificaciones_estudiante'),
    path('dashboard-calificaciones/', CalManageView.as_view(), name='dashboard-calificaciones'),
    path('request/calificaciones/', CalificacionesAPIView.as_view(), name='calificaciones_api'),
    path('request/calificaciones/bulk/', CalificacionesBulkAPIView.as_view(), name='calificaciones_bulk_api'),
    path('request/calificaciones/excel/', CalificacionesExcelAPIView.as_view(), name='calificaciones_excel_api'),
    path('asignacion/<int:asignacion_id>/estudiantes/', 
         ListaEstudiantesView.as_view(), 
         name='lista_estudiantes'),
    path('consult-office/', get_office_hours, name='office_hours_view'),
    path('dashboard-office/', office_hours_view, name='office_hours_view'),
]