from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from apps.students.models import Estudiante, Matricula
from apps.subjects.models.academic import PeriodoAcademico
from apps.subjects.models.activity import PromedioTrimestre, PromedioAnual
from decimal import Decimal
import json

class FinalGradesView(LoginRequiredMixin, TemplateView):
    template_name = 'students/calificaciones.html'
    
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
            
        try:
            # Obtener la matrícula del estudiante en el período seleccionado
            matricula = Matricula.objects.get(estudiante=estudiante, periodo=current_period)
            
            # Preparar estructura de datos de calificaciones finales
            final_grades_data = []
            
            for detalle in matricula.detallematricula_set.all():
                subject_data = {
                    'materia': detalle.materia.nombre,
                    'promedios': {}
                }
                
                # Obtener promedios trimestrales
                promedios_trimestre = PromedioTrimestre.objects.filter(
                    detalle_matricula=detalle
                ).order_by('trimestre__trimestre')
                
                # Inicializar todos los trimestres con 0
                subject_data['promedios'] = {
                    't1': {'promedio': 0, 'completo': False},
                    't2': {'promedio': 0, 'completo': False},
                    't3': {'promedio': 0, 'completo': False}
                }
                
                # Actualizar con los promedios existentes
                for promedio in promedios_trimestre:
                    trimestre_num = promedio.trimestre.trimestre
                    subject_data['promedios'][f't{trimestre_num}'] = {
                        'promedio': float(promedio.promedio_final),
                        'completo': promedio.is_trimestre_completo()
                    }
                
                # Obtener promedio anual
                try:
                    promedio_anual = PromedioAnual.objects.get(detalle_matricula=detalle)
                    subject_data['promedio_final'] = float(promedio_anual.promedio_final)
                    
                    # Verificar si hay al menos un trimestre con nota
                    trimestres_con_nota = sum(1 for t in subject_data['promedios'].values() 
                                            if t['promedio'] > 0 and t['completo'])
                    trimestres_sin_nota = sum(1 for t in subject_data['promedios'].values() 
                                            if t['promedio'] == 0 or not t['completo'])
                    
                    # Determinar estado
                    if promedio_anual.promedio_final >= Decimal('7.00') and trimestres_sin_nota == 0:
                        subject_data['estado'] = 'Aprobado'
                        subject_data['estado_clase'] = 'text-green-600'
                    elif trimestres_con_nota == 0:
                        subject_data['estado'] = 'En Progreso'
                        subject_data['estado_clase'] = 'text-blue-600'
                    elif trimestres_con_nota > 0 and trimestres_sin_nota > 0:
                        subject_data['estado'] = 'Pendiente'
                        subject_data['estado_clase'] = 'text-purple-600'
                    elif promedio_anual.promedio_final < Decimal('7.00') and trimestres_sin_nota == 0:
                        subject_data['estado'] = 'Reprobado'
                        subject_data['estado_clase'] = 'text-red-600'
                    
                except PromedioAnual.DoesNotExist:
                    subject_data['promedio_final'] = 0
                    subject_data['estado'] = 'En Progreso'
                    subject_data['estado_clase'] = 'text-blue-600'
                
                final_grades_data.append(subject_data)
            
            # Calcular estadísticas generales
            materias_total = len(final_grades_data)
            materias_aprobadas = sum(1 for m in final_grades_data if m['estado'] == 'Aprobado')
            materias_pendientes = sum(1 for m in final_grades_data if m['estado'] == 'Pendiente')
            materias_reprobadas = sum(1 for m in final_grades_data if m['estado'] == 'Reprobado')
            
            # Calcular promedio general solo con materias que tengan notas completas
            promedios_validos = [m['promedio_final'] for m in final_grades_data 
                               if m['promedio_final'] > 0 and m['estado'] != 'Pendiente']
            promedio_general = sum(promedios_validos) / len(promedios_validos) if promedios_validos else 0
            
        except Matricula.DoesNotExist:
            final_grades_data = []
            materias_total = materias_aprobadas = materias_pendientes = materias_reprobadas = 0
            promedio_general = 0
        
        # Obtener lista de períodos para el selector
        periods = list(PeriodoAcademico.objects.values('id', 'nombre'))
        
        context.update({
            'final_grades_json': json.dumps(final_grades_data),
            'periods_json': json.dumps(periods),
            'current_period_id': current_period.id,
            'estadisticas': {
                'total_materias': materias_total,
                'materias_aprobadas': materias_aprobadas,
                'materias_pendientes': materias_pendientes,
                'materias_reprobadas': materias_reprobadas,
                'promedio_general': round(promedio_general, 2)
            }
        })
        
        return context