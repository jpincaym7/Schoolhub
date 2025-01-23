from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from apps.students.models import Estudiante, Matricula
from apps.subjects.models.academic import PeriodoAcademico
from apps.subjects.models.activity import Calificacion, PromedioAnual
import json

class GradesView(LoginRequiredMixin, TemplateView):
    template_name = 'students/student_grades.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get current student and current academic period
        estudiante = Estudiante.objects.get(usuario=self.request.user)
        current_period = PeriodoAcademico.objects.get(activo=True)
        
        # Get student's enrollment for the current period
        matricula = Matricula.objects.get(
            estudiante=estudiante, 
            periodo=current_period
        )
        
        # Prepare grades data
        grades_data = []
        for detalle in matricula.detallematricula_set.all():
            try:
                calificacion = Calificacion.objects.get(
                    detalle_matricula=detalle, 
                    parcial=2  # Use second partial for final representation
                )
                promedio_anual = PromedioAnual.objects.get(
                    detalle_matricula=detalle
                )
                
                grades_data.append({
                    'materia': detalle.materia.nombre,
                    'tarea1': float(calificacion.tarea1),
                    'tarea2': float(calificacion.tarea2),
                    'tarea3': float(calificacion.tarea3),
                    'tarea4': float(calificacion.tarea4),
                    'parcial1': float(promedio_anual.promedio_p1),
                    'parcial2': float(promedio_anual.promedio_p2),
                    'promedio_final': float(promedio_anual.promedio_final)
                })
            except (Calificacion.DoesNotExist, PromedioAnual.DoesNotExist):
                pass
        
        # Prepare periods
        periods = list(PeriodoAcademico.objects.values('id', 'nombre'))
        
        context.update({
            'grades_json': json.dumps(grades_data),
            'periods_json': json.dumps(periods),
            'current_period_id': current_period.id
        })
        
        return context