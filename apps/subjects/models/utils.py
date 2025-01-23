from django.db.models import Prefetch, Q
from decimal import Decimal

from apps.students.models import DetalleMatricula
from apps.subjects.models.activity import Aporte, CalificacionDeber, NotaFinalMateria, Parcial

def get_student_grades_report(asignacion_profesor):
    """
    Obtiene un reporte completo de calificaciones de estudiantes para una asignación específica,
    incluyendo los que no tienen calificaciones.
    
    Args:
        asignacion_profesor (AsignacionProfesor): La asignación del profesor
        
    Returns:
        dict: Diccionario con las calificaciones y estudiantes sin calificaciones
    """
    # Obtener todos los estudiantes matriculados en la materia
    estudiantes_matriculados = DetalleMatricula.objects.filter(
        matricula__periodo=asignacion_profesor.periodo,
        materia=asignacion_profesor.materia
    ).select_related(
        'matricula__estudiante',
        'matricula__estudiante__usuario'
    )
    
    # Inicializar diccionarios para almacenar resultados
    calificaciones = {
        'estudiantes_con_notas': [],
        'estudiantes_sin_notas': [],
        'resumen': {
            'total_estudiantes': 0,
            'con_notas': 0,
            'sin_notas': 0,
            'aprobados': 0,
            'reprobados': 0
        }
    }
    
    for detalle in estudiantes_matriculados:
        estudiante_info = {
            'nombre': f"{detalle.matricula.estudiante.usuario.first_name} {detalle.matricula.estudiante.usuario.last_name}",
            'id': detalle.matricula.estudiante.id,
            'notas': {}
        }
        
        # Obtener parciales
        parciales = Parcial.objects.filter(asignacion=asignacion_profesor)
        tiene_notas = False
        
        for parcial in parciales:
            nota_final_parcial = parcial.get_nota_final(detalle)
            
            if nota_final_parcial > Decimal('0'):
                tiene_notas = True
                
            estudiante_info['notas'][f'parcial_{parcial.numero_parcial}'] = {
                'nota_final': float(nota_final_parcial),
                'deberes': [],
                'aporte': None
            }
            
            # Obtener calificaciones de deberes
            deberes = CalificacionDeber.objects.filter(
                deber__parcial=parcial,
                detalle_matricula=detalle
            )
            
            for deber in deberes:
                estudiante_info['notas'][f'parcial_{parcial.numero_parcial}']['deberes'].append({
                    'titulo': deber.deber.titulo,
                    'valor': float(deber.valor),
                    'fecha': deber.fecha_calificacion.strftime('%Y-%m-%d')
                })
            
            # Obtener aporte
            aporte = Aporte.objects.filter(
                parcial=parcial,
                detalle_matricula=detalle
            ).first()
            
            if aporte:
                estudiante_info['notas'][f'parcial_{parcial.numero_parcial}']['aporte'] = float(aporte.valor)
        
        # Obtener nota final de la materia
        nota_final = NotaFinalMateria.objects.filter(detalle_matricula=detalle).first()
        if nota_final:
            estudiante_info['nota_final'] = {
                'valor': float(nota_final.nota_final),
                'aprobado': nota_final.aprobado
            }
            
            if nota_final.aprobado:
                calificaciones['resumen']['aprobados'] += 1
            else:
                calificaciones['resumen']['reprobados'] += 1
        
        # Clasificar estudiante según si tiene notas o no
        if tiene_notas or nota_final:
            calificaciones['estudiantes_con_notas'].append(estudiante_info)
            calificaciones['resumen']['con_notas'] += 1
        else:
            calificaciones['estudiantes_sin_notas'].append(estudiante_info)
            calificaciones['resumen']['sin_notas'] += 1
            
    calificaciones['resumen']['total_estudiantes'] = len(estudiantes_matriculados)
    
    return calificaciones

def print_student_grades_report(asignacion_profesor):
    """
    Imprime un reporte formateado de las calificaciones de los estudiantes.
    
    Args:
        asignacion_profesor (AsignacionProfesor): La asignación del profesor
    """
    reporte = get_student_grades_report(asignacion_profesor)
    
    print(f"\nReporte de Calificaciones - {asignacion_profesor}")
    print("=" * 80)
    
    print("\nEstudiantes con calificaciones:")
    print("-" * 40)
    for estudiante in reporte['estudiantes_con_notas']:
        print(f"\nEstudiante: {estudiante['nombre']}")
        for parcial, datos in estudiante['notas'].items():
            print(f"\n  {parcial.replace('_', ' ').title()}:")
            print(f"    Nota final del parcial: {datos['nota_final']:.2f}")
            
            print("    Deberes:")
            for deber in datos['deberes']:
                print(f"      - {deber['titulo']}: {deber['valor']:.2f}")
            
            print(f"    Aporte: {datos['aporte']:.2f if datos['aporte'] else 'No registrado'}")
            
        if 'nota_final' in estudiante:
            print(f"\n  Nota Final: {estudiante['nota_final']['valor']:.2f}")
            print(f"  Estado: {'Aprobado' if estudiante['nota_final']['aprobado'] else 'Reprobado'}")
    
    print("\nEstudiantes sin calificaciones:")
    print("-" * 40)
    for estudiante in reporte['estudiantes_sin_notas']:
        print(f"- {estudiante['nombre']}")
    
    print("\nResumen:")
    print("-" * 40)
    print(f"Total de estudiantes: {reporte['resumen']['total_estudiantes']}")
    print(f"Estudiantes con notas: {reporte['resumen']['con_notas']}")
    print(f"Estudiantes sin notas: {reporte['resumen']['sin_notas']}")
    print(f"Estudiantes aprobados: {reporte['resumen']['aprobados']}")
    print(f"Estudiantes reprobados: {reporte['resumen']['reprobados']}")