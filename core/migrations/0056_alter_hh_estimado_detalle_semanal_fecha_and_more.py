# Generated by Django 4.1.8 on 2024-10-11 00:02

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0055_empleado_remove_asignacion_recurso_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='hh_estimado_detalle_semanal',
            name='fecha',
            field=models.DateTimeField(default=datetime.datetime(2024, 10, 10, 21, 2, 36, 876935), verbose_name='Fecha'),
        ),
        migrations.AlterModelTable(
            name='empleado',
            table='EMPLEADO',
        ),
    ]
