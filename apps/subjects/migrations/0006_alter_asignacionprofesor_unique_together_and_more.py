# Generated by Django 5.1 on 2025-01-29 03:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('subjects', '0005_alter_asignacionprofesor_unique_together_and_more'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='asignacionprofesor',
            unique_together={('profesor', 'materia', 'curso', 'periodo')},
        ),
        migrations.RemoveField(
            model_name='asignacionprofesor',
            name='trimestre',
        ),
        migrations.DeleteModel(
            name='Trimestre',
        ),
    ]
