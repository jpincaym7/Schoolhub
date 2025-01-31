from decimal import Decimal
from django.views.generic import ListView
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Prefetch, Avg, F
from apps.students.models import Estudiante, Matricula, DetalleMatricula
from apps.subjects.models.activity import Calificacion, PromedioAnual, PromedioTrimestre
from apps.subjects.models.grades import AsignacionProfesor
from apps.subjects.models.academic import PeriodoAcademico
from django.db.models import Q
from django.contrib import messages

class ListaEstudiantesView(LoginRequiredMixin, ListView):
    template_name = 'teacher/calificaciones/students_list.html'
    context_object_name = 'estudiantes'
    
    def get_queryset(self):
        # Get the teacher's assignment
        self.asignacion = get_object_or_404(
            AsignacionProfesor,
            id=self.kwargs['asignacion_id'],
            profesor__usuario=self.request.user
        )
        
        # Get selected trimester and partial from GET parameters
        self.trimestre_id = self.request.GET.get('trimestre')
        self.parcial_numero = self.request.GET.get('parcial')
        
        # Get students with their enrollments
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
            estudiante.calificaciones_data = self.get_calificaciones_estudiante(estudiante)

        return estudiantes
    
    def get_calificaciones_estudiante(self, estudiante):
        """Get student grades based on selected filters"""
        data = {
            'promedio_parcial': Decimal('0.0'),
            'calificaciones': None,
            'promedio_trimestre': None,
            'matricula': None
        }
        
        if hasattr(estudiante, 'matriculas') and estudiante.matriculas:
            matricula = estudiante.matriculas[0]
            data['matricula'] = matricula
            
            detalle = DetalleMatricula.objects.filter(
                matricula=matricula,
                materia=self.asignacion.materia
            ).first()
            
            if detalle:
                # Build query for grades
                calificaciones_query = Calificacion.objects.filter(
                    detalle_matricula=detalle,
                    asignacion_profesor=self.asignacion
                )
                
                # Apply trimester filter if specified
                if self.trimestre_id:
                    calificaciones_query = calificaciones_query.filter(
                        parcial__trimestre_id=self.trimestre_id
                    )
                    
                    # Get trimester average
                    promedio_trimestre = PromedioTrimestre.objects.filter(
                        detalle_matricula=detalle,
                        trimestre_id=self.trimestre_id
                    ).first()
                    
                    if promedio_trimestre:
                        data['promedio_trimestre'] = {
                            'promedio_p1': promedio_trimestre.promedio_p1,
                            'promedio_p2': promedio_trimestre.promedio_p2,
                            'examen_trimestral': promedio_trimestre.examen_trimestral,
                        }
                
                # Apply partial filter if specified
                if self.parcial_numero:
                    calificaciones_query = calificaciones_query.filter(
                        parcial__numero=self.parcial_numero
                    )
                
                # Get filtered grades
                calificacion = calificaciones_query.select_related('parcial__trimestre').first()
                
                if calificacion:
                    data['calificaciones'] = {
                        'parcial': calificacion.parcial.get_numero_display(),
                        'trimestre': calificacion.parcial.trimestre.get_trimestre_display(),
                        'tareas': [
                            calificacion.tarea1,
                            calificacion.tarea2,
                            calificacion.tarea3,
                            calificacion.tarea4
                        ],
                        'promedio_tareas': sum([
                            calificacion.tarea1,
                            calificacion.tarea2,
                            calificacion.tarea3,
                            calificacion.tarea4
                        ]) / 4,
                        'examen': calificacion.examen,
                        'promedio_final': calificacion.promedio_final
                    }
                    data['promedio_parcial'] = calificacion.promedio_final
        
        return data
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['asignacion'] = self.asignacion
        
        # Add filter options to context
        context['trimestres'] = self.asignacion.trimestres.all().order_by('trimestre')
        context['parciales'] = [
            {'numero': 1, 'nombre': 'Primer Parcial'},
            {'numero': 2, 'nombre': 'Segundo Parcial'}
        ]
        
        # Add selected filters to context
        context['trimestre_seleccionado'] = self.trimestre_id
        context['parcial_seleccionado'] = self.parcial_numero
        
        # Calculate statistics based on filtered data
        estudiantes = context['estudiantes']
        total_estudiantes = len(estudiantes)
        
        if total_estudiantes > 0:
            promedios = [
                est.calificaciones_data['promedio_parcial'] 
                for est in estudiantes 
                if est.calificaciones_data['promedio_parcial'] > 0
            ]
            
            if promedios:
                context.update({
                    'promedio_general': round(sum(promedios) / len(promedios), 2),
                    'mejor_promedio': round(max(promedios), 2),
                    'peor_promedio': round(min(promedios), 2),
                    'total_estudiantes': total_estudiantes,
                    'estudiantes_aprobados': sum(1 for p in promedios if p >= 7.0),
                    'estudiantes_reprobados': sum(1 for p in promedios if p < 7.0),
                    'porcentaje_aprobacion': round(
                        (sum(1 for p in promedios if p >= 7.0) / total_estudiantes) * 100, 
                        2
                    )
                })
        
        return context

    def dispatch(self, request, *args, **kwargs):
        if not AsignacionProfesor.objects.filter(
            id=self.kwargs['asignacion_id'],
            profesor__usuario=request.user
        ).exists():
            messages.error(request, "No tienes permiso para ver esta información.")
            return redirect('subjects:dashboard')
        return super().dispatch(request, *args, **kwargs)
