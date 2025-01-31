from django.contrib import admin
from apps.subjects.models.academic import Parcial

class ParcialAdmin(admin.ModelAdmin):
    list_display = ('trimestre', 'numero', 'get_trimestre_display')  # Muestra el trimestre y número del parcial
    list_filter = ('trimestre',)  # Permite filtrar por trimestre
    search_fields = ('trimestre__periodo__nombre',)  # Permite buscar por nombre del periodo del trimestre
    ordering = ('trimestre', 'numero')  # Ordena por trimestre y número de parcial

    def get_trimestre_display(self, obj):
        return obj.trimestre.get_trimestre_display()  # Muestra el nombre del trimestre
    get_trimestre_display.short_description = 'Trimestre'

admin.site.register(Parcial, ParcialAdmin)