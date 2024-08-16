# Generated by Django 5.1 on 2024-08-16 00:36

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0025_remove_distribuidor_hh_horas_empleado_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='HorasRequeridas',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('id_semana', models.IntegerField(verbose_name='ID Semana')),
                ('horas_requeridas', models.FloatField(verbose_name='Horas Necesarias por semana')),
            ],
        ),
        migrations.AlterField(
            model_name='distribuidor_hh',
            name='horas_dis_empleado',
            field=models.FloatField(verbose_name='Horas del empleado disponible'),
        ),
        migrations.AlterField(
            model_name='hh_estimado_detalle_semanal',
            name='fecha',
            field=models.DateTimeField(default=datetime.datetime(2024, 8, 15, 20, 36, 2, 685608), verbose_name='Fecha'),
        ),
    ]
