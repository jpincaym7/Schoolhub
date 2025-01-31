from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from apps.students.models import Estudiante, Matricula
from apps.subjects.models.academic import PeriodoAcademico, Trimestre
from apps.subjects.models.activity import Calificacion, PromedioTrimestre
import json

class GradesView(LoginRequiredMixin, TemplateView):
    template_name = 'students/student_grades.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener el estudiante actual
        estudiante = Estudiante.objects.get(usuario=self.request.user)
        
        # Obtener el período académico seleccionado o el activo por defecto
        period_id = self.request.GET.get('period')
        if period_id:
            current_period = PeriodoAcademico.objects.get(id=period_id)
        else:
            current_period = PeriodoAcademico.objects.get(activo=True)
        
        print(current_period)
        
        # Obtener el trimestre seleccionado
        trimestre_id = self.request.GET.get('trimestre')
        
        # Obtener la materia seleccionada
        materia_id = self.request.GET.get('materia')
        
        try:
            # Obtener la matrícula del estudiante en el período seleccionado
            matricula = Matricula.objects.get(estudiante=estudiante, periodo=current_period)
            
            # Obtener los trimestres disponibles para el período
            trimestres = Trimestre.objects.filter(periodo=current_period)
            
            # Preparar estructura de datos de calificaciones
            grades_data = []
            
            # Filtrar materias si se ha seleccionado una
            detalles_matricula = matricula.detallematricula_set.all()
            if materia_id:
                detalles_matricula = detalles_matricula.filter(materia_id=materia_id)
            
            for detalle in detalles_matricula:
                subject_data = {
                    'materia': detalle.materia.nombre,
                    'trimestres': []
                }
                
                # Filtrar trimestres si se ha seleccionado uno
                trimestres_to_process = trimestres
                if trimestre_id:
                    trimestres_to_process = trimestres.filter(id=trimestre_id)
                
                for trimestre in trimestres_to_process:
                    trimestre_data = {
                        'id': trimestre.id,
                        'trimestre': trimestre.get_trimestre_display(),
                        'parciales': []
                    }
                    
                    # Obtener promedio trimestral
                    try:
                        promedio_trimestre = PromedioTrimestre.objects.get(
                            detalle_matricula=detalle,
                            trimestre=trimestre
                        )
                        trimestre_data['promedio_trimestral'] = float(promedio_trimestre.promedio_final)
                        trimestre_data['examen_trimestral'] = float(promedio_trimestre.examen_trimestral)
                    except PromedioTrimestre.DoesNotExist:
                        trimestre_data['promedio_trimestral'] = 0
                        trimestre_data['examen_trimestral'] = 0
                    
                    # Obtener calificaciones por parciales
                    calificaciones = Calificacion.objects.filter(
                        detalle_matricula=detalle,
                        parcial__trimestre=trimestre
                    ).order_by('parcial__numero')
                    
                    for calificacion in calificaciones:
                        parcial_data = {
                            'numero_parcial': calificacion.parcial.numero,
                            'tarea1': float(calificacion.tarea1),
                            'tarea2': float(calificacion.tarea2),
                            'tarea3': float(calificacion.tarea3),
                            'tarea4': float(calificacion.tarea4),
                            'examen': float(calificacion.examen),
                            'promedio_parcial': float(calificacion.promedio_final)
                        }
                        trimestre_data['parciales'].append(parcial_data)
                    print(trimestre_data)
                    subject_data['trimestres'].append(trimestre_data)
                
                if subject_data['trimestres']:
                    grades_data.append(subject_data)
        
        except Matricula.DoesNotExist:
            grades_data = []
            trimestres = []
        
        # Obtener lista de períodos para el selector
        periods = list(PeriodoAcademico.objects.values('id', 'nombre'))
        
        # Obtener lista de trimestres
        trimestres_data = [
            {
                'id': trimestre.id,
                'nombre': trimestre.get_trimestre_display()
            } 
            for trimestre in trimestres
        ]
        
        # Obtener lista de materias inscritas por el estudiante
        materias = [
            {
                'id': detalle.materia.id,
                'nombre': detalle.materia.nombre
            }
            for detalle in matricula.detallematricula_set.all()
        ]
        print(grades_data)
        context.update({
            'grades_json': json.dumps(grades_data),
            'periods_json': json.dumps(periods),
            'trimestres_json': json.dumps(trimestres_data),
            'materias_json': json.dumps(materias),
            'current_period_id': current_period.id,
            'current_trimestre_id': trimestre_id if trimestre_id else None,
            'current_materia_id': materia_id if materia_id else None
        })
        return context
