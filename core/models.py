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
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    NUMRUT = models.IntegerField(blank=False, null=False, verbose_name="Numero RUT")
    DVRUN = models.CharField(max_length=1, null=False, blank=False, verbose_name="Digito Verificador")
    fechaNacimiento = models.DateField(null=False, blank=False, verbose_name="Fecha de Nacimiento")
    cargo = models.CharField(max_length=150, null=False, blank=False, verbose_name="Cargo Empleado")
    telefono = models.CharField(max_length=12, null=False, blank=False, verbose_name="Número de contacto")
    
    def __str__(self):
        return str(self.NUMRUT) + " - " + str(self.DVRUN)
    
    
class historialCambios(models.Model):
    idHist = models.AutoField(primary_key=True, verbose_name="ID Historial")
    fecha = models.DateTimeField(blank=False, null=False, verbose_name="Fecha Accion")
    desc = models.CharField(max_length=300, blank=False, null=False, verbose_name="Descripción")
    tipoInfo = models.CharField(max_length=50, blank=False, null=False, verbose_name="Tipo de información")
    usuario = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    
    def __str__(self):
        return str(self.idHist) + " - " + str(self.desc) + " - " + str(self.usuario)
    
class proyectosAAgrupar(models.Model):
    id = models.IntegerField(primary_key=True, verbose_name="ID Proyecto")
    proyecto = models.CharField(max_length=12, blank=False, null=False, verbose_name="Proyecto")
    lineaNegocio = models.CharField(max_length=6, blank=False, null=False, verbose_name="Línea de Negocio")
    tipo = models.CharField(max_length=50, blank=False, null=False, verbose_name="Tipo de Proyecto")
    cliente = models.IntegerField(blank=True, null=True, verbose_name="ID Cliente")
    pm = models.CharField(max_length=60, blank=False, null=False, verbose_name="Correo JP") ##Verificar
    createDate = models.DateTimeField(null=False, blank=False, verbose_name="Fecha de creación")
    cierre = models.DateField(null=False, blank=False, verbose_name="Cierre del proyecto")
    primeraTarea = models.DateField(null=False, blank=False, verbose_name="Primera Tarea Realizada")
    ultimaTarea = models.DateField(null=False, blank=False, verbose_name="Última tarea realizada")
    egresosNoHHCLP = models.IntegerField(null=False, blank=False, verbose_name="Egresos no HH CLP")
    montoOfertaCLP = models.IntegerField(null=False, blank=False, verbose_name="Monto Oferta CLP")
    usoAgencia = models.BooleanField(null=False, blank=False, default=0, verbose_name="Apoyo de Agencia")
    desfaseDias = models.IntegerField(null=False, blank=False, default=0, verbose_name="Desfase de días para el inicio del proyecto")
    ocupacionInicio = models.DecimalField(max_digits=6, decimal_places=2, null=False, blank=False, verbose_name="Porcentaje de uso inicial")

    def __str__(self):
        return str(self.proyecto) + " - " + str(self.lineaNegocio) + " - " + str(self.tipo)


class Distribuidor_HH(models.Model):
    id_empleado = models.IntegerField(blank=False, null=False, verbose_name="ID Empleado")
    nombre_empleado = models.CharField(max_length=100, blank=False, null=False, verbose_name="Nombre del empleado")
    cargo = models.CharField(max_length=100, blank=False, null=False, verbose_name="Nombre del Cargo o Rol del empleado")
    telefono = models.CharField(max_length=20, blank=False, null=False, verbose_name="Número del empleado")
    id_categoria = models.IntegerField(blank=False, null=False, verbose_name="ID De la categoria del empleado")
    id_proyecto = models.IntegerField(blank=False, null=False, verbose_name="ID Del proyecto")
    horas_empleado = models.IntegerField(blank=False, null=False, verbose_name="Horas del empleado")  # Corregido
    horas_dis_empleado = models.IntegerField(blank=False, null=False, verbose_name="Horas del empleado disponible")  # Corregido

    def __str__(self):
        return f"{self.nombre_empleado} - {self.cargo}"