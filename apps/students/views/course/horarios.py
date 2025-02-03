from django.http import JsonResponse
from django.shortcuts import render
from apps.subjects.models.Teacher import Profesor
from apps.subjects.models.Horario import HorarioAtencion

def office_hours_view(request):
    profesores = Profesor.objects.all()
    return render(request, 'students/office_hours.html', {
        'profesores': profesores,
        'dias': ['Lun', 'Mar', 'Mie', 'Jue', 'Vie']
    })
    
def get_office_hours(request):
    profesor_id = request.GET.get('profesor')
    
    # Inicializar el queryset base
    horarios = HorarioAtencion.objects.all()
    
    # Aplicar filtro solo si se selecciona un profesor específico
    if profesor_id and profesor_id.strip():  # Verificar si hay un ID y no está vacío
        horarios = horarios.filter(profesor_id=profesor_id)
    
    # Ordenar los resultados
    horarios = horarios.order_by('dia', 'hora_inicio').select_related(
        'profesor__usuario', 
        'profesor__especialidad'
    )
    
    slots = []
    for h in horarios:
        slots.append({
            'profesor': h.profesor.usuario.get_full_name(),
            'day': h.get_dia_display(),
            'time': f"{h.hora_inicio.strftime('%H:%M')} - {h.hora_fin.strftime('%H:%M')}",
            'available': True,
            'especialidad': h.profesor.especialidad.nombre
        })
    
    return JsonResponse({'slots': slots})