from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.students.models import DetalleMatricula, Matricula
from apps.subjects.models.Teacher import Profesor
from apps.subjects.models.grades import AsignacionProfesor
from apps.subjects.models.subject import Materia

class TeacherDashboardView(LoginRequiredMixin, ListView):
    model = AsignacionProfesor
    template_name = 'teacher/dashboard/asignaciones.html'
    context_object_name = 'asignaciones'
    
    def get_queryset(self):
        # Obtén el profesor relacionado con el usuario logueado
        profesor = Profesor.objects.get(usuario=self.request.user)
        
        # Devuelve las asignaciones del profesor
        return AsignacionProfesor.objects.filter(
            profesor=profesor
        ).select_related('materia', 'curso', 'periodo')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtén el profesor actual
        profesor = Profesor.objects.get(usuario=self.request.user)
        
        # Obtener los estudiantes relacionados con las asignaciones del profesor
        asignaciones = AsignacionProfesor.objects.filter(
            profesor=profesor
        )
        estudiantes = Matricula.objects.filter(
            periodo__in=asignaciones.values_list('periodo', flat=True),
            materias__in=asignaciones.values_list('materia', flat=True)
        ).select_related('estudiante__usuario', 'periodo').distinct()
        
        print(estudiantes)
        
        # Agrega los estudiantes al contexto
        context['estudiantes'] = estudiantes
        
        context["total_estudiantes"] = estudiantes.count()
        
        # Calcula el número de materias activas
        context['active_subjects'] = self.get_queryset().filter(
            periodo__activo=True
        ).count()
        
        return context