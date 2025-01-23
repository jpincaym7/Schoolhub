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
    profesor_id = request.GET.get('profesor', '')
    
    horarios = HorarioAtencion.objects.filter(
        profesor__id=profesor_id if profesor_id else None
    )
    
    slots = [{
        'profesor': h.profesor.usuario.get_full_name(),
        'day': h.get_dia_display(),
        'time': f"{h.hora_inicio} - {h.hora_fin}",
        'available': True,
        'especialidad': h.profesor.especialidad.nombre
    } for h in horarios]
    
    return JsonResponse({'slots': slots})