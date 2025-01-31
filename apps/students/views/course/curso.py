from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from apps.students.models import Estudiante, Matricula, Materia

@login_required
def lista_companeros(request):
    estudiante_actual = get_object_or_404(Estudiante, usuario=request.user)
    
    # Get classmates from the same course, fixing the select_related
    companeros = (Estudiante.objects
                 .filter(curso=estudiante_actual.curso)
                 .exclude(usuario=request.user)
                 .select_related('usuario', 'curso', 'curso__especialidad')  # Fixed this line
                 .order_by('usuario__last_name', 'usuario__first_name'))
    
    # Get some statistics
    total_companeros = companeros.count()
    especialidad = estudiante_actual.curso.especialidad
    periodo_actual = estudiante_actual.curso.periodo
    
    # Group students by their initial letter for the directory
    companeros_por_letra = {}
    for companero in companeros:
        inicial = companero.usuario.last_name[0].upper()
        if inicial not in companeros_por_letra:
            companeros_por_letra[inicial] = []
        companeros_por_letra[inicial].append(companero)
    
    context = {
        'estudiante_actual': estudiante_actual,
        'companeros': companeros,
        'companeros_por_letra': dict(sorted(companeros_por_letra.items())),
        'total_companeros': total_companeros,
        'especialidad': especialidad,
        'periodo_actual': periodo_actual,
        'curso_actual': estudiante_actual.curso,
    }
    
    return render(request, 'students/lista_companeros.html', context)

@login_required
def course_dashboard(request):
    # Get the current student
    estudiante_actual = Estudiante.objects.get(usuario=request.user)
    
    # Get the current student's course
    curso = estudiante_actual.curso
    
    # Find students in the same course
    total_companeros = Estudiante.objects.filter(curso=curso).count() - 1
    
    # Get the student's subjects for the current course
    matricula = Matricula.objects.get(estudiante=estudiante_actual, periodo=curso.periodo)
    materias = matricula.materias.all()
    
    context = {
        'curso': curso,
        'estudiante_actual': estudiante_actual,
        'total_companeros': total_companeros,
        'materias': materias
    }
    
    return render(request, 'students/course_dashboard.html', context)