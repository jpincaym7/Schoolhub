from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.students.views.course.calificaciones import GradesView
from apps.students.views.course.carnet import student_card_view
from apps.students.views.course.curso import course_dashboard, lista_companeros
from apps.students.views.admin.matricula import MatriculaTemplateView, MatriculaViewSet
from apps.students.views.admin.viewset import EstudianteListView, MatDetailView, MatListView, PeriodoAcademicoListView
from apps.students.views.course.trimestre import TrimestreListView
from apps.students.views.course.trimestres import ExamenTrimestralAPIView, ExamenTrimestralView, PromedioTrimestreAPIView

app_name = 'students'

router = DefaultRouter()
router.register(r'matriculas', MatriculaViewSet)

urlpatterns = [

    path('admin/matricula/', MatriculaTemplateView.as_view(), name='matricula_dashboard'),
    path('query-periods/', PeriodoAcademicoListView.as_view(), name='query_periods'),
    path('query-mat/', MatListView.as_view(), name='materia-list'),
    path('query-detail/', MatDetailView.as_view(), name='query-detail'),
    path('query-students/', EstudianteListView.as_view(), name='query_students'),
    path('companeros/', lista_companeros, name='lista_companeros'),
    path('dashboard-course/', course_dashboard, name='course_dashboard'),
    path('dashboard-student/', GradesView.as_view(), name='dashboard-student'),
    path('api/trimestres/', TrimestreListView.as_view(), name='trimestres-list'),
    path('examenes-trimestrales/view/', ExamenTrimestralView.as_view(), name='examenes-view'),
    path('promedios-trimestre/', PromedioTrimestreAPIView.as_view(), name='promedios-trimestre'),
    path('examenes-trimestrales/', ExamenTrimestralAPIView.as_view(), name='examenes-trimestrales'),
    path('view/card/', student_card_view, name='student_card'),
    path('', include(router.urls)),
]
