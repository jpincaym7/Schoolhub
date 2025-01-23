# Generated by Django 5.1 on 2025-01-22 17:23

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0001_initial'),
        ('subjects', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='detallematricula',
            unique_together=set(),
        ),
        migrations.AlterUniqueTogether(
            name='matricula',
            unique_together=set(),
        ),
        migrations.AddField(
            model_name='detallematricula',
            name='materia',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='subjects.materia'),
        ),
        migrations.AddField(
            model_name='estudiante',
            name='curso',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='subjects.curso'),
        ),
        migrations.AddField(
            model_name='matricula',
            name='materias',
            field=models.ManyToManyField(null=True, through='students.DetalleMatricula', to='subjects.materia'),
        ),
        migrations.AddField(
            model_name='matricula',
            name='periodo',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='subjects.periodoacademico'),
        ),
        migrations.AlterUniqueTogether(
            name='detallematricula',
            unique_together={('matricula', 'materia')},
        ),
        migrations.AlterUniqueTogether(
            name='matricula',
            unique_together={('estudiante', 'periodo')},
        ),
    ]
