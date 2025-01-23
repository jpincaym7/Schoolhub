from django.views.generic import ListView
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Prefetch, Avg, F
from apps.students.models import Estudiante, Matricula, DetalleMatricula
from apps.subjects.models.activity import Calificacion, PromedioAnual
from apps.subjects.models.grades import AsignacionProfesor
from apps.subjects.models.academic import PeriodoAcademico
from django.db.models import Q
from django.contrib import messages

class ListaEstudiantesView(LoginRequiredMixin, ListView):
    template_name = 'teacher/calificaciones/students_list.html'
    context_object_name = 'estudiantes'
    
    def get_queryset(self):
        # Obtener la asignación del profesor
        self.asignacion = get_object_or_404(
            AsignacionProfesor,
            id=self.kwargs['asignacion_id'],
            profesor__usuario=self.request.user
        )
        
        # Obtener los estudiantes del curso con sus matrículas
        estudiantes = Estudiante.objects.filter(
            curso=self.asignacion.curso
        ).select_related(
            'usuario',
            'curso'
        ).prefetch_related(
            Prefetch(
                'matricula_set',
                queryset=Matricula.objects.filter(
                    periodo=self.asignacion.periodo
                ),
                to_attr='matriculas'
            )
        )

        for estudiante in estudiantes:
            # Inicializar atributos dinámicos para las calificaciones
            estudiante.promedio_p1 = 0
            estudiante.promedio_p2 = 0
            estudiante.promedio_final = 0
            estudiante.matricula = None

            if hasattr(estudiante, 'matriculas') and estudiante.matriculas:
                matricula = estudiante.matriculas[0]
                estudiante.matricula = matricula
                
                # Obtener detalle de matrícula para la materia específica
                detalle = DetalleMatricula.objects.filter(
                    matricula=matricula,
                    materia=self.asignacion.materia
                ).first()
                
                if detalle:
                    # Obtener calificaciones
                    calificaciones = Calificacion.objects.filter(
                        detalle_matricula=detalle,
                        asignacion_profesor=self.asignacion
                    ).order_by('parcial')
                    
                    # Obtener los promedios del estudiante
                    prom = PromedioAnual.objects.filter(
                        detalle_matricula=detalle
                    ).first()
                    
                    if prom:
                        estudiante.promedio_p1 = prom.promedio_p1
                        estudiante.promedio_p2 = prom.promedio_p2
                        estudiante.promedio_final = prom.promedio_final

                    print(estudiantes)
        return estudiantes
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['asignacion'] = self.asignacion
        
        # Agregar estadísticas generales
        estudiantes = context['estudiantes']
        total_estudiantes = len(estudiantes)
        
        if total_estudiantes > 0:
            # Calcular promedios finales de todos los estudiantes
            promedios = [est.promedio_final for est in estudiantes if est.promedio_final > 0]
            if promedios:
                context['promedio_general'] = round(sum(promedios) / len(promedios), 2)
                context['mejor_promedio'] = round(max(promedios), 2)
                context['peor_promedio'] = round(min(promedios), 2)
                
                # Calcular estadísticas de aprobación
                aprobados = sum(1 for p in promedios if p >= 7.0)
                context['porcentaje_aprobacion'] = round((aprobados / total_estudiantes) * 100, 2)
                context['total_estudiantes'] = total_estudiantes
                context['estudiantes_aprobados'] = aprobados
                context['estudiantes_reprobados'] = total_estudiantes - aprobados
        
        return context

    def dispatch(self, request, *args, **kwargs):
        # Verificar que el profesor tenga acceso a esta asignación
        if not AsignacionProfesor.objects.filter(
            id=self.kwargs['asignacion_id'],
            profesor__usuario=request.user
        ).exists():
            messages.error(request, "No tienes permiso para ver esta información.")
            return redirect('subjects:dashboard')
        return super().dispatch(request, *args, **kwargs)
