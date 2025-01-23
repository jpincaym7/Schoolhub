from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg, Count
from apps.subjects.models.Teacher import Profesor
from apps.subjects.models.activity import Calificacion, PromedioAnual
from django.shortcuts import get_object_or_404
from apps.students.models import DetalleMatricula
from apps.subjects.models.grades import AsignacionProfesor
from apps.subjects.views.asignacion import profesor

class CalificacionesView(LoginRequiredMixin, TemplateView):
    template_name = 'teacher/calificaciones/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        estudiante_id = self.kwargs.get('estudiante_id')
        periodo_id = self.kwargs.get('periodo_id')
        
        # Obtener detalles de matrícula
        detalles_matricula = DetalleMatricula.objects.filter(
            matricula__estudiante_id=estudiante_id,
            matricula__periodo_id=periodo_id
        ).select_related(
            'materia',
            'matricula__estudiante',
            'matricula__periodo'
        ).prefetch_related(
            'calificacion_set'
        )
        
        materias_info = []
        
        for detalle in detalles_matricula:
            calificaciones = detalle.calificacion_set.all()
            
            tareas_por_parcial = {}
            for cal in calificaciones:
                tareas_por_parcial[cal.parcial] = {
                    'tarea1': cal.tarea1,
                    'tarea2': cal.tarea2,
                    'tarea3': cal.tarea3,
                    'tarea4': cal.tarea4,
                    'examen': cal.examen,
                    'promedio_final': cal.promedio_final,
                }
            
            # Obtener promedios por parcial
            promedios = {cal.parcial: cal.promedio_final for cal in calificaciones}
            
            materias_info.append({
                'materia': detalle.materia.nombre,  # Usar el nombre de la materia
                'promedio_p1': promedios.get(1, 0),
                'promedio_p2': promedios.get(2, 0),
                'promedio_final': sum(promedios.values()) / len(promedios) if promedios else 0,
                'tareas_por_parcial': tareas_por_parcial,  # Notas por parcial
            })
        
        context.update({
            'materias_info': materias_info,
            'estudiante': detalles_matricula[0].matricula.estudiante if detalles_matricula else None,
            'periodo': detalles_matricula[0].matricula.periodo if detalles_matricula else None,
        })
        return context