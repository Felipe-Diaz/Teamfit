from django.core.management.base import BaseCommand
from core.models import TipoProyecto, Recurso, Disponibilidad, Proyecto

class Command(BaseCommand):
    help = 'Carga datos de prueba en la base de datos'

    def handle(self, *args, **kwargs):
        # Crear tipos de proyecto
        tp1 = TipoProyecto.objects.create(nombre="Alta", prioridad=3)
        tp2 = TipoProyecto.objects.create(nombre="Media", prioridad=2)
        tp3 = TipoProyecto.objects.create(nombre="Baja", prioridad=1)

        # Crear recursos
        for i in range(4):
            Recurso.objects.create(nombre=f"Ingeniero {i+1}", rol="Ingeniero de Proyectos", prioridad=3, horas_promedio=8)
        for i in range(4, 8):
            Recurso.objects.create(nombre=f"Ingeniero {i+1}", rol="Ingeniero de Proyectos", prioridad=2, horas_promedio=8)
        for i in range(8, 11 ):
            Recurso.objects.create(nombre=f"Ingeniero {i+1}", rol="Ingeniero de Proyectos", prioridad=3, horas_promedio=8)
        for i in range(1):
            Recurso.objects.create(nombre=f"Jefe de Proyecto {i+1}", rol="Jefe de Proyecto", prioridad=1, horas_promedio=8)
        for i in range(1, 3):
            Recurso.objects.create(nombre=f"Jefe de Proyecto {i+1}", rol="Jefe de Proyecto", prioridad=2, horas_promedio=8)  
        for i in range(3, 4):
            Recurso.objects.create(nombre=f"Jefe de Proyecto {i+1}", rol="Jefe de Proyecto", prioridad=3, horas_promedio=8)          

        # Crear disponibilidad de recursos por semana
        for recurso in Recurso.objects.all():
            for semana in range(1, 53):
                Disponibilidad.objects.create(recurso=recurso, semana=semana, horas_disponibles=40)

        # Crear proyectos
        Proyecto.objects.create(nombre="Desarrollo de Plataforma Web", tipo_proyecto=tp1, horas_demandadas=80, rol_requerido="Ingeniero de Proyectos", semana_inicio=35, duracion_semanas=26)
        Proyecto.objects.create(nombre="Desarrollo de Plataforma Web", tipo_proyecto=tp1, horas_demandadas=20, rol_requerido="Jefe de Proyecto", semana_inicio=35, duracion_semanas=26)
        
        Proyecto.objects.create(nombre="Implementación de ERP", tipo_proyecto=tp2, horas_demandadas=60, rol_requerido="Ingeniero de Proyectos", semana_inicio=38, duracion_semanas=52)
        Proyecto.objects.create(nombre="Implementación de ERP", tipo_proyecto=tp2, horas_demandadas=10, rol_requerido="Jefe de Proyecto", semana_inicio=38, duracion_semanas=52)
        
        Proyecto.objects.create(nombre="Expansión Internacional", tipo_proyecto=tp1, horas_demandadas=100, rol_requerido="Ingeniero de Proyectos", semana_inicio=45, duracion_semanas=16)
        Proyecto.objects.create(nombre="Expansión Internacional", tipo_proyecto=tp1, horas_demandadas=30, rol_requerido="Jefe de Proyecto", semana_inicio=45, duracion_semanas=16)

        self.stdout.write(self.style.SUCCESS('Datos de prueba cargados exitosamente.'))
