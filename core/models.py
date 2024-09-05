from asyncio.windows_events import NULL
from distutils.command.upload import upload
from email.policy import default
from pickle import TRUE
from tabnanny import verbose
from tkinter import CASCADE
from django.db import models
from django.forms import IntegerField 
from django.contrib.auth.models import User
from datetime import datetime
import pytz
from django.utils import timezone

# Create your models here.

#Tabla de Ventas.
class Ventas(models.Model):
    id = models.AutoField(primary_key=True, verbose_name="ID Venta")
    idTipoProyecto = models.CharField(max_length=10, blank=False, null=False, verbose_name="Tipo de Proyecto")
    fecha = models.DateTimeField(null=False, blank=False, verbose_name="Fecha")

    def __str__(self):
        return str(self.id) + " - " + str(self.idTipoProyecto) + " - " + str(self.fecha)
    
#Tabla de Perfil horas hombre detalle semanal.
class Perfil_hh_Detalle_Semanal(models.Model):
    id = models.AutoField(primary_key=True, verbose_name="ID Detalle Semanal")
    idTipoProyecto = models.CharField(max_length=10, blank=False, null=False, verbose_name="Tipo de Proyecto")
    numSemana = models.IntegerField(null=False, blank=False, verbose_name="Número de Semana")
    hh = models.DecimalField(max_digits=10, decimal_places=1, null=False, blank=False, verbose_name="Cantidad de horas")

    def __str__(self):
        return str(self.id) + " - " + str(self.idTipoProyecto) + " - " + str(self.numSemana)


class Disponibilidad(models.Model):
    semana = models.IntegerField(primary_key=True, verbose_name="Semana")
    hh = models.DecimalField(max_digits=10, decimal_places=1, verbose_name="Cantidad de horas estimadas")

    def __str__(self):
        return self.semana + " - " + self.hh 
     
class Hh_Estimado_Detalle_Semanal(models.Model):
    id = models.AutoField(primary_key=True, verbose_name="ID Estimado Detalle Semanal")
    fecha = models.DateTimeField(null=False, blank=False, default=datetime.now(), verbose_name="Fecha")
    anio = models.IntegerField(null=False, blank=False, verbose_name="Año")
    semana = models.IntegerField(null=False, blank=False, verbose_name="Semana")
    idVentas = models.ForeignKey(Ventas, on_delete=models.DO_NOTHING)
    idPerfilHhDetalleSemanal = models.ForeignKey(Perfil_hh_Detalle_Semanal, on_delete=models.DO_NOTHING)
    ##CAMBIAR A FLOAT
    hh = models.DecimalField(max_digits=10, decimal_places=1, null=False, blank=False, verbose_name="Cantidad de horas estimadas")

    def __str__(self):
        return str(self.id) + " - " + str(self.anio) + "/" + str(self.semana)

class Graficos(models.Model):
    semana = models.IntegerField(null=False, blank=False, verbose_name="Semana")
    hhRequerido = models.DecimalField(max_digits=10, decimal_places=1, null=False, blank=False, verbose_name="Cantidad de horas estimadas")
    hhDisponible = models.DecimalField(max_digits=10, decimal_places=1, null=False, blank=False, verbose_name="Cantidad de horas estimadas")
    utilizacion =  models.FloatField(null=False, blank=False, verbose_name="Cantidad de horas estimadas")

    def __str__(self):
        return str(self.id) + " - " + str(self.idTipoProyecto)

class PerfilUsuario(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    cargo = models.CharField(max_length=150, null=False, blank=False, verbose_name="Cargo Empleado")
        
    class Meta:
        db_table = 'PERFIL_USUARIO'
    
    def __str__(self):
        return str(self.cargo)
    
    
class historialCambios(models.Model):
    idHist = models.AutoField(primary_key=True, verbose_name="ID Historial")
    fecha = models.DateTimeField(blank=False, null=False, verbose_name="Fecha Acción")
    categoria = models.CharField(max_length=250, blank=False, null=False, default="No Registrado", verbose_name="Categoría")
    subcategoria = models.CharField(max_length=250, blank=False, null=False, default="No Registrado", verbose_name="Sub Categoría")
    prioridad = models.IntegerField(blank=False, null=False, default=0, verbose_name="Prioridad")
    #desc = models.CharField(max_length=300, blank=False, null=False, verbose_name="Descripción")
    #tipoInfo = models.CharField(max_length=50, blank=False, null=False, verbose_name="Tipo de información")
    usuario = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    
    class Meta:
        db_table = 'HISTORIAL_CAMBIOS'
    
    def __str__(self):
        return str(self.idHist) + " - " + str(self.desc) + " - " + str(self.usuario)
    
class proyectosAAgrupar(models.Model):
    id = models.IntegerField(primary_key=True, verbose_name="ID Proyecto")
    proyecto = models.CharField(max_length=12, blank=False, null=False, verbose_name="Proyecto")
    lineaNegocio = models.CharField(max_length=6, blank=False, null=False, verbose_name="Línea de Negocio")
    tipo = models.CharField(max_length=50, blank=False, null=False, verbose_name="Tipo de Proyecto")
    cliente = models.IntegerField(blank=True, null=True, verbose_name="ID Cliente")
    createDate = models.DateTimeField(null=False, blank=False, verbose_name="Fecha de creación")
    cierre = models.DateField(null=False, blank=False, verbose_name="Cierre del proyecto")
    egresosNoHHCLP = models.IntegerField(null=False, blank=False, verbose_name="Egresos no HH CLP")
    montoOfertaCLP = models.IntegerField(null=False, blank=False, verbose_name="Monto Oferta CLP")
    usoAgencia = models.BooleanField(null=False, blank=False, default=0, verbose_name="Apoyo de Agencia")
    ocupacionInicio = models.DecimalField(max_digits=6, decimal_places=2, null=False, blank=False, verbose_name="Porcentaje de uso inicial")
    disponibilidad = models.DecimalField(max_digits=6, decimal_places=2, default=0, null=False, blank=False, verbose_name="Porcentaje de disponibilidad")
    utilizacion = models.DecimalField(max_digits=6, decimal_places=2, default=0, null=False, blank=False, verbose_name="Porcentaje de utilización")

    class Meta:
        db_table = 'PROYECTOS'

    def __str__(self):
        return str(self.proyecto) + " - " + str(self.lineaNegocio) + " - " + str(self.tipo)
    

class Parametro(models.Model):
    nombre_parametro = models.CharField(max_length=255, unique=True)
    valor = models.JSONField()
    
    class Meta:
        db_table = 'PARAMETROS'

    def __str__(self):
        return self.nombre_parametro