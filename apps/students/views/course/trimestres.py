from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from decimal import Decimal
from apps.subjects.models.academic import PeriodoAcademico, Trimestre
from apps.subjects.models.activity import PromedioTrimestre, PromedioAnual
from apps.subjects.models.subject import Materia
from apps.subjects.serializers.calificaciones import PromedioTrimestreSerializer
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

class ExamenTrimestralView(LoginRequiredMixin, TemplateView):
    template_name = 'teacher/calificaciones/trimestres.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get active period
        periodo_activo = PeriodoAcademico.objects.filter(activo=True).first()
        
        # Get all periods for the select
        periodos = PeriodoAcademico.objects.all().order_by('-fecha_inicio')
        
        # Get subjects based on user role
        user = self.request.user
        if hasattr(user, 'profesor'):
            # If user is a teacher, get only their subjects
            materias = Materia.objects.filter(profesor=user.profesor)
        else:
            # If user is admin or has other role, get all subjects
            materias = Materia.objects.all()
            
        # Get trimesters
        trimestres = Trimestre.objects.all().order_by('trimestre')
        
        # Add to context
        context.update({
            'periodo_activo': periodo_activo,
            'periodos': periodos,
            'materias': materias,
            'trimestres': trimestres,
            'page_title': 'Exámenes Trimestrales',
            'current_section': 'examenes'
        })
        
        return context



class PromedioTrimestreAPIView(APIView):
    def get(self, request):
        periodo_id = request.query_params.get('periodo')
        materia_id = request.query_params.get('materia')
        trimestre_id = request.query_params.get('trimestre')
        
        if not all([periodo_id, materia_id, trimestre_id]):
            return Response({
                'error': 'Faltan parámetros requeridos'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        promedios = PromedioTrimestre.objects.filter(
            detalle_matricula__matricula__periodo_id=periodo_id,
            detalle_matricula__materia_id=materia_id,
            trimestre_id=trimestre_id
        ).select_related(
            'detalle_matricula__matricula__estudiante__usuario',
            'trimestre'
        )
        
        serializer = PromedioTrimestreSerializer(promedios, many=True)
        return Response(serializer.data)

@method_decorator(csrf_exempt, name='dispatch')
class ExamenTrimestralAPIView(APIView):
    @transaction.atomic
    def post(self, request):
        try:
            examenes_data = request.data
            updated_promedios = []
            
            for examen in examenes_data:
                promedio = PromedioTrimestre.objects.get(id=examen['promedio_id'])
                
                # Actualizar examen trimestral
                if 'examen_trimestral' in examen:
                    promedio.examen_trimestral = Decimal(str(examen['examen_trimestral']))
                
                # Actualizar proyecto trimestral
                if 'proyecto_trimestral' in examen:
                    promedio.proyecto_trimestral = Decimal(str(examen['proyecto_trimestral']))
                
                promedio.save()
                
                # Actualizar promedio anual
                promedio_anual, created = PromedioAnual.objects.get_or_create(
                    detalle_matricula=promedio.detalle_matricula
                )
                
                # Actualizar el promedio del trimestre correspondiente
                trimestre_num = promedio.trimestre.trimestre
                if trimestre_num == '1':
                    promedio_anual.promedio_t1 = promedio.promedio_final
                elif trimestre_num == '2':
                    promedio_anual.promedio_t2 = promedio.promedio_final
                elif trimestre_num == '3':
                    promedio_anual.promedio_t3 = promedio.promedio_final
                
                promedio_anual.save()
                
                updated_promedios.append({
                    'id': promedio.id,
                    'promedio_final': float(promedio.promedio_final),
                    'examen_trimestral': float(promedio.examen_trimestral),
                    'proyecto_trimestral': float(promedio.proyecto_trimestral)
                })
            
            return Response({
                'message': 'Exámenes y proyectos trimestrales actualizados exitosamente',
                'promedios': updated_promedios
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response({
                'error': f'Error en el formato de los números: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)