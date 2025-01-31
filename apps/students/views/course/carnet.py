from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from apps.students.models import Estudiante

@login_required
def student_card_view(request):
    """
    Vista para mostrar el carnet estudiantil del usuario logueado.
    Solo accesible para usuarios de tipo estudiante.
    """
    if request.user.user_type != 'estudiante':
        raise PermissionDenied("Solo los estudiantes pueden acceder a esta página")
    
    estudiante = get_object_or_404(Estudiante, usuario=request.user)
    
    context = {
        'estudiante': estudiante,
    }
    
    return render(request, 'students/student_card.html', context)