from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.students.models import Estudiante, Matricula, Materia

@login_required
def lista_companeros(request):
    # Get the current student
    estudiante_actual = Estudiante.objects.get(usuario=request.user)
    
    # Find students in the same course
    companeros = Estudiante.objects.filter(curso=estudiante_actual.curso).exclude(usuario=request.user)
    
    context = {
        'estudiante_actual': estudiante_actual,
        'companeros': companeros,
        'total_companeros': companeros.count()
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