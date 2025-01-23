from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.communications.models import Asistencia
from apps.students.models import Estudiante, Matricula
from django.db.models import Count, Case, When, IntegerField, F
from apps.users.models import User

class StudentAttendanceView(LoginRequiredMixin, TemplateView):
    template_name = 'students/student_attendance.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        estudiante = Estudiante.objects.get(usuario=self.request.user)
        # Get current student's matricula
        matricula = Matricula.objects.filter(
            estudiante = estudiante
        ).select_related('periodo').first()
        
        if not matricula:
            context['error'] = "no encontró matricula"
            return context

        # Attendance analysis
        asistencias = Asistencia.objects.filter(matricula=matricula).order_by('-fecha')
        
        # Attendance statistics
        total_clases = asistencias.count()
        presentes = asistencias.filter(asistio=True).count()
        
        # Group by month for visualization
        monthly_attendance = asistencias.annotate(
            month=F('fecha__month'),
            year=F('fecha__year')
        ).values('month', 'year').annotate(
            total_clases=Count('id'),
            presentes=Count(Case(When(asistio=True, then=1), output_field=IntegerField()))
        ).order_by('year', 'month')

        context.update({
            'matricula': matricula,
            'asistencias': asistencias,
            'total_clases': total_clases,
            'presentes': presentes,
            'porcentaje_asistencia': round((presentes / total_clases * 100), 2) if total_clases > 0 else 0,
            'monthly_attendance': list(monthly_attendance)
        })
        
        return context