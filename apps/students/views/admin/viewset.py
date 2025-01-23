from rest_framework import generics
from apps.students.models import Estudiante
from apps.students.serializers.utils import EstudianteSerializer, MateriaSerializer, PeriodoAcademicoSerializer
from apps.subjects.models.academic import PeriodoAcademico
from apps.subjects.models.subject import Materia

class EstudianteListView(generics.ListAPIView):
    queryset = Estudiante.objects.all()
    serializer_class = EstudianteSerializer

class PeriodoAcademicoListView(generics.ListAPIView):
    queryset = PeriodoAcademico.objects.all()
    serializer_class = PeriodoAcademicoSerializer
    
class MatListView(generics.ListAPIView):
    queryset = Materia.objects.all()
    serializer_class = MateriaSerializer
    
class MatDetailView(generics.RetrieveAPIView):
    queryset = Materia.objects.all()
    serializer_class = MateriaSerializer
    lookup_field = 'id'  # O el campo que deseas usar para buscar el detalle, como 'id' o 'slug'
