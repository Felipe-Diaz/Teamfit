from asyncio.windows_events import NULL
from distutils.command.upload import upload
from email.policy import default
from pickle import TRUE
from sre_parse import Verbose
from tabnanny import verbose
from tkinter import CASCADE
from django.db import models
from django.forms import IntegerField 
from django.contrib.auth.models import User
from datetime import datetime

# Create your models here.

#Tabla de Ventas.
class Ventas(models.Model):
    id = models.AutoField(primary_key=True, verbose_name="ID Venta")
    idTipoProyecto = models.CharField(max_length=10, blank=False, null=False, verbose_name="Tipo de Proyecto")
    fecha = models.DateTimeField(null=False, blank=False, verbose_name="Fecha")

    def __str__(self):
        return self.id + " - " + self.idTipoProyecto + " - " + str(self.fecha)
    
#Tabla de Perfil horas hombre detalle semanal.
class Perfil_hh_Detalle_Semanal(models.Model):
    id = models.AutoField(primary_key=True, verbose_name="ID Detalle Semanal")
    idTipoProyecto = models.CharField(max_length=10, blank=False, null=False, verbose_name="Tipo de Proyecto")
    numSemana = models.IntegerField(null=False, blank=False, verbose_name="Número de Semana")
    hh = models.IntegerField(null=False, blank=False, verbose_name="Cantidad de horas")

    def __str__(self):
        return str(self.id) + " - " + str(self.idTipoProyecto)


class Disponibilidad(models.Model):
    semana = models.IntegerField(primary_key=True, verbose_name="Semana")
    hh = models.IntegerField(verbose_name="Cantidad de horas estimadas")

    def __str__(self):
        return self.semana + " - " + self.hh 
     
class Hh_Estimado_Detalle_Semanal(models.Model):
    id = models.AutoField(primary_key=True, verbose_name="ID Estimado Detalle Semanal")
    fecha = models.DateTimeField(null=False, blank=False, default=datetime.now(), verbose_name="Fecha")
    anio = models.IntegerField(null=False, blank=False, verbose_name="Año")
    semana = models.IntegerField(null=False, blank=False, verbose_name="Semana")
    idVentas = models.ForeignKey(Ventas, on_delete=models.DO_NOTHING)
    idPerfilHhDetalleSemanal = models.ForeignKey(Perfil_hh_Detalle_Semanal, on_delete=models.DO_NOTHING)
    hh = models.IntegerField(null=False, blank=False, verbose_name="Cantidad de horas estimadas")

    def __str__(self):
        return str(self.id) + " - " + str(self.anio) + "/" + str(self.semana)

class Graficos(models.Model):
    semana = models.IntegerField(null=False, blank=False, verbose_name="Semana")
    hhRequerido = models.IntegerField(null=False, blank=False, verbose_name="Cantidad de horas estimadas")
    hhDisponible = models.IntegerField(null=False, blank=False, verbose_name="Cantidad de horas estimadas")
    utilización =  models.FloatField(null=False, blank=False, verbose_name="Cantidad de horas estimadas")

    def __str__(self):
        return self.id + " - " + self.idTipoProyecto
