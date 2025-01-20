from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _

class AcademicPeriod(models.Model):
    """Manages academic periods (quimesters)"""
    number = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(2)],
        verbose_name=_('Número de Quimestre')
    )
    school_year = models.CharField(
        max_length=9,
        verbose_name=_('Año Lectivo')
    )

    class Meta:
        verbose_name = _('Período Académico')
        verbose_name_plural = _('Períodos Académicos')
        unique_together = ['number', 'school_year']
        ordering = ['school_year', 'number']

    def __str__(self):
        return f"Quimestre {self.number} - {self.school_year}"