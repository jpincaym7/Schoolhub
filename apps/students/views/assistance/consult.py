# views.py
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Case, When, FloatField, Q
from django.db.models.functions import Cast
from django.utils.translation import gettext as _
from django.http import HttpResponseForbidden
from apps.students.models import Student, Attendance
from typing import Dict, Any
from collections import defaultdict

class StudentAttendanceView(LoginRequiredMixin, ListView):
    template_name = 'attendance/student_attendance.html'
    context_object_name = 'students_attendance'
    
    def get_queryset(self):
        """
        Obtiene los estudiantes del representante y calcula sus estadísticas de asistencia
        """
        if self.request.user.user_type != 'parent':
            return Student.objects.none()
            
        # Obtener estudiantes activos del representante
        students = Student.objects.filter(
            parent=self.request.user,
            is_active=True
        ).prefetch_related('attendance')
        
        attendance_stats = []
        
        for student in students:
            # Calcular el total de días con registro de asistencia
            total_days = student.attendance.count()
            
            if total_days == 0:
                continue
                
            # Calcular porcentajes por tipo de asistencia
            attendance_counts = student.attendance.aggregate(
                present_count=Count(Case(
                    When(status='present', then=1),
                    output_field=FloatField(),
                )),
                absent_count=Count(Case(
                    When(status='absent', then=1),
                    output_field=FloatField(),
                )),
                late_count=Count(Case(
                    When(status='late', then=1),
                    output_field=FloatField(),
                )),
                justified_count=Count(Case(
                    When(status='justified', then=1),
                    output_field=FloatField(),
                ))
            )
            
            # Calcular porcentajes
            stats = {
                'student': student,
                'total_days': total_days,
                'percentages': {
                    'present': (attendance_counts['present_count'] / total_days) * 100,
                    'absent': (attendance_counts['absent_count'] / total_days) * 100,
                    'late': (attendance_counts['late_count'] / total_days) * 100,
                    'justified': (attendance_counts['justified_count'] / total_days) * 100
                },
                'counts': attendance_counts,
                # Calcular asistencia total (presente + atraso)
                'total_attendance': (
                    (attendance_counts['present_count'] + attendance_counts['late_count']) 
                    / total_days * 100
                )
            }
            attendance_stats.append(stats)
            
        return attendance_stats
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['status_labels'] = {
            'present': _('Presente'),
            'absent': _('Ausente'),
            'late': _('Atrasado'),
            'justified': _('Justificado')
        }
        return context

    def handle_no_permission(self):
        return HttpResponseForbidden(_('No tiene permiso para ver esta página.'))