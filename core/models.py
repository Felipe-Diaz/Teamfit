from asyncio.windows_events import NULL
from email.policy import default
from pickle import TRUE
from tabnanny import verbose
from tkinter import CASCADE
from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
from django.utils import timezone
from datetime import date

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
    proyecto = models.CharField(max_length=12, blank=False, null=False, unique=False, verbose_name="Proyecto")
    lineaNegocio = models.CharField(max_length=6, blank=False, null=False, verbose_name="Línea de Negocio")
    tipo = models.CharField(max_length=50, blank=False, null=False, verbose_name="Tipo de Proyecto")
    cliente = models.IntegerField(blank=True, null=True, verbose_name="ID Cliente")
    createDate = models.DateTimeField(null=False, blank=False, verbose_name="Fecha de creación")
    cierre = models.DateField(null=True, blank=True, verbose_name="Cierre del proyecto") #
    fechaInicio = models.DateField(null=True, blank=True, verbose_name="Inicio del proyecto")
    fechaFin = models.DateField(null=True, blank=True, verbose_name="Fin del proyecto") 
    egresosNoHHCLP = models.IntegerField(null=False, blank=False, default=0, verbose_name="Egresos no HH CLP") #
    montoOfertaCLP = models.IntegerField(null=False, blank=False, verbose_name="Monto Oferta CLP")
    usoAgencia = models.BooleanField(null=False, blank=False, default=0, verbose_name="Apoyo de Agencia")
    ocupacionInicio = models.DecimalField(max_digits=6, decimal_places=2, null=False, blank=False, verbose_name="Porcentaje de uso inicial") #
    #disponibilidad = models.DecimalField(max_digits=6, decimal_places=2, default=0, null=False, blank=False, verbose_name="Porcentaje de disponibilidad") #
    #utilizacion = models.DecimalField(max_digits=6, decimal_places=2, default=0, null=False, blank=False, verbose_name="Porcentaje de utilización") #

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
    
    
class HorasPredecidas(models.Model):
    linea_negocio = models.CharField(max_length=10, blank=False, null=False, verbose_name='Linea de Negocio')
    tipo = models.CharField(max_length=255, blank=False, null=False, verbose_name='Tipo')
    rol = models.CharField(max_length=50, blank=False, null=False, verbose_name='Rol')
    hh_max = models.FloatField(null=False, blank=False, default=0, verbose_name='Horas Hombre Max')
    hh_prom = models.FloatField(null=False, blank=False, default=0, verbose_name='Horas Hombre Prom')
    hh_min = models.FloatField(null=False, blank=False, default=0, verbose_name='Horas Hombre Min')
    tipo_semana = models.CharField(max_length=20 ,null=True, blank=True, default='Intermedio', verbose_name='Tipo de Semana')
    cluster = models.IntegerField(null=False, blank=False, default=0, verbose_name='Cluster')
    
    class Meta:
        db_table = 'HORAS_PREDECIDAS'
        
    def __str__(self):
        return self.linea_negocio + ' - ' + self.tipo + ' - ' + self.rol
    
class proyectosSemanas(models.Model):
    proyecto = models.ForeignKey(proyectosAAgrupar, on_delete=models.DO_NOTHING)
    horas = models.ForeignKey(HorasPredecidas, on_delete=models.DO_NOTHING)
    semana = models.IntegerField(null=False, blank=False, default=0, verbose_name='Semana del proyecto')
    tipoSemana = models.CharField(max_length=50, blank=False, null=False, verbose_name='Tipo de Semana')
    
    class Meta:
        db_table = 'SEMANA_PROYECTOS'
    
    def __str__(self):
        return str(self.semana) + ' - ' + str(self.proyecto)
    

### MODELOS GRUPO 2 - ESCRIBIR MODELOS DE ACÁ HACIA ABAJO
    
    
# Modelo TipoProyecto
class TipoProyecto(models.Model):
    nombre = models.CharField(max_length=255)
    prioridad = models.IntegerField()  # Cuanto mayor es el número, mayor es la prioridad

    class Meta:
        db_table = "TipoProyecto"

    def __str__(self):
        return self.nombre

# Modelo Recurso
class Recurso(models.Model):
    nombre = models.CharField(max_length=255)
    rol = models.CharField(max_length=100)  # Por ejemplo, "Ingeniero de Proyectos", "Jefe de Proyecto"
    prioridad = models.IntegerField()  # Cuanto mayor es el número, mayor es la prioridad
    horas_promedio = models.IntegerField(default=40)  # Horas promedio disponibles por semana

    class Meta:
        db_table = "Recurso"

    def __str__(self):
        return f'{self.nombre} - {self.rol}'

# Modelo Disponibilidad
class Disponibilidad(models.Model):
    recurso = models.ForeignKey(Recurso, on_delete=models.CASCADE)
    semana = models.IntegerField()  # De 1 a 52
    horas_disponibles = models.IntegerField(default=40)

    class Meta:
        db_table = "Disponibilidad"

    def __str__(self):
        return f'{self.recurso.nombre} - Semana {self.semana}'

# Modelo Proyecto
class Proyecto(models.Model):
    nombre = models.CharField(max_length=255)
    tipo_proyecto = models.ForeignKey(TipoProyecto, on_delete=models.CASCADE)
    horas_demandadas = models.IntegerField()
    rol_requerido = models.CharField(max_length=100)  # Similarmente, puede ser una ForeignKey si tienes un modelo de Rol
    semana_inicio = models.IntegerField()  # Semana de inicio del proyecto
    duracion_semanas = models.IntegerField()  # Duración del proyecto en semanas

    class Meta:
        db_table = "Proyecto"
    def __str__(self):
        return self.nombre

# Modelo Asignacion
class Asignacion(models.Model):
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE)
    recurso = models.ForeignKey(Recurso, on_delete=models.CASCADE)
    semana = models.IntegerField()
    horas_asignadas = models.IntegerField()
    año = models.IntegerField(default=2024) 

    class Meta:
        db_table = "Asignacion"
    def __str__(self):
        return f'{self.proyecto.nombre} - {self.recurso.nombre} - Semana {self.semana} - {self.horas_asignadas} horas'



class AsignacionControl(models.Model):
    fecha_ultimo_ejecucion = models.DateField(null=True, blank=True)
    ejecuciones_exitosas = models.IntegerField(default=0)  # Agregar este campo

    def puede_ejecutar(self):
        if not self.fecha_ultimo_ejecucion:
            return True
        return self.fecha_ultimo_ejecucion < date.today()

    def registrar_ejecucion(self, exito=True):
        self.fecha_ultimo_ejecucion = date.today()
        if exito:
            self.ejecuciones_exitosas += 1  # Incrementa en caso de éxito
        self.save()