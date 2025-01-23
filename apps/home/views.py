from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Prefetch
from apps.students.models import DetalleMatricula, Estudiante
from apps.users.models import Module
from apps.subjects.models.grades import AsignacionProfesor
from apps.subjects.models.Curso import Curso
from apps.subjects.models.subject import Materia

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        user_type = user.user_type

        # Get modules with permissions
        modules_with_permission = Module.objects.filter(
            permissions__user_type=user_type,
            permissions__can_view=True
        ).distinct()
        
        context['announcements'] = [
            {'content': 'Inicio del nuevo período académico', 'date': '2025-01-20'},
            {'content': 'Recordatorio: Entrega de calificaciones', 'date': '2025-01-18'},
            {'content': 'Reunión de profesores programada', 'date': '2025-01-15'},
        ]

        # If user is a teacher, get their additional information
        if hasattr(user, 'profesor'):
            profesor = user.profesor
            
            # Get teacher's subject assignments with related data
            asignaciones = AsignacionProfesor.objects.filter(
                profesor=profesor
            ).select_related(
                'materia', 
                'curso', 
                'periodo'
            ).prefetch_related(
                'curso__especialidad'
            )

            # Get students by subject
            estudiantes_por_materia = {}
            for asignacion in asignaciones:
                estudiantes = DetalleMatricula.objects.filter(
                    materia=asignacion.materia,
                ).select_related('matricula')
                estudiantes_por_materia[asignacion.materia] = estudiantes

            # Get unique courses
            cursos_profesor = list(set(asig.curso for asig in asignaciones))

            # Get subject statistics
            estadisticas_materias = {
                'total_materias': asignaciones.values('materia').distinct().count(),
                'total_cursos': len(cursos_profesor),
                'total_estudiantes': sum(len(est) for est in estudiantes_por_materia.values())
            }

            # Add teacher specific context
            context.update({
                'asignaciones': asignaciones,
                'estudiantes_por_materia': estudiantes_por_materia,
                'cursos_profesor': cursos_profesor,
                'estadisticas_materias': estadisticas_materias
            })

        context['modules'] = modules_with_permission
        return context