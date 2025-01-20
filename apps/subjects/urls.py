from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.subjects.views.grades.actividad import  ActivityTemplateViewSet, ActivityViewSet, get_current_academic_period 
from apps.subjects.views.grades.dash import ActivityGradesView, SubjectActivitiesView, SubjectListView
from apps.subjects.views.represent.dashboard import ParentDashboardView
from apps.subjects.views.represent.materias import StudentSubjectsView
from apps.subjects.views.grades.subjects import subject_list
from apps.subjects.views.grades.subjects import SubjectViewSet

app_name = 'subjects'

router = DefaultRouter()
router.register(r'api-subjects', SubjectViewSet)
router.register(r'activity-templates', ActivityTemplateViewSet)
router.register(r'activities', ActivityViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard-subject/', subject_list, name='subject_list'),
    path('dashboard-parent/', ParentDashboardView.as_view(), name='grade_parent'),
    path('materias-dashboard/', StudentSubjectsView.as_view(), name='materias-dashboard'),
    path('subject-list/', SubjectListView.as_view(), name='subject_list'),
    path('<int:pk>/api-activities/', 
         SubjectActivitiesView.as_view(), 
         name='subject_activities'),
    path('action-edit/<int:pk>/notas/', 
         ActivityGradesView.as_view(), 
         name='activity_grades'),
    path('academic-periods/current/', get_current_academic_period, name='current-academic-period'),
]