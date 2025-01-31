from rest_framework import generics

from apps.subjects.models.academic import Trimestre
from apps.subjects.serializers.calificaciones import TrimestreSerializer

class TrimestreListView(generics.ListAPIView):
    serializer_class = TrimestreSerializer

    def get_queryset(self):
        # Obtén el periodo que se pasa como parámetro en la URL
        periodo_id = self.request.query_params.get('periodo')
        if periodo_id:
            context = Trimestre.objects.filter(periodo_id=periodo_id)
            print(context)
            return Trimestre.objects.filter(periodo_id=periodo_id)
        
        return Trimestre.objects.none()  # Si no se proporciona el periodo, no se retorna nada