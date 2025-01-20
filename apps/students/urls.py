from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.students.views.assistance.consult import StudentAttendanceView
from apps.students.views.attention.asistance import AttendanceTemplateView, AttendanceViewSet
from apps.students.views.behavior.api import AcademicPeriodViewSet, BehaviorManagementView, BehaviorSummaryViewSet, BehaviorViewSet
from apps.students.views.students import StudentDashboardView, StudentViewSet

app_name = 'students'

# Initialize the router
router = DefaultRouter()

# Register the viewset with the router
router.register(r'api-students', StudentViewSet)
router.register(r'attendances', AttendanceViewSet)
router.register(r'api-behavior', BehaviorViewSet, basename='behavior')
router.register(r'api-summary', BehaviorSummaryViewSet, basename='summary')
router.register(r'academic-periods', AcademicPeriodViewSet, basename='academicperiod')

urlpatterns = [
    # Include the router's URLs
    path('', include(router.urls)),
    path('dashboard/', StudentDashboardView.as_view(), name='student_management'),
    path('attendance-dashboard/', AttendanceTemplateView.as_view(), name='attendance_dashboard'),
    path('behavior/', BehaviorManagementView.as_view(), name='behavior_management'),
    path('parent-attendance/', StudentAttendanceView.as_view(), name='parent-attendance'),

]
