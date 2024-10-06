# # myapp/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
from .views import eliminar_historial_automatico  # Asegúrate de importar tu tarea
from .models import Parametro
from .forms import PROGRAMACION_MAPPING

scheduler = BackgroundScheduler()

def start_scheduler():
    #Código Min Hor * * *
    frecuencia = obtener_frecuencia()
    if frecuencia == 'A1':
        hora, minuto = obtener_tiempo_eliminacion()
        scheduler.add_job(eliminar_historial_automatico, 'cron', id='borrar_historial', hour=hora ,minute=minuto, replace_existing=True)
        print(f"Tarea programada para eliminar logs a las {hora}:{minuto}")
        scheduler.start()
    elif frecuencia == 'A2':
        hora, minuto = obtener_tiempo_eliminacion()
        dias_semana, nombres_dias_semana = obtener_dias()
        dias_semana_str = ','.join(map(str, dias_semana))
        print(f'VALOR DE DIAS SEMANAS {dias_semana}')
        scheduler.add_job(eliminar_historial_automatico, 'cron', id='borrar_historial', hour=hora ,minute=minuto, day_of_week=dias_semana_str, replace_existing=True)
        print(f"Tarea programada para eliminar logs a las {hora}:{minuto} todos los {nombres_dias_semana}")
    # elif frecuencia == 'A3':
    #     print('Mensual aún no agregado, se crea el diario (El Mercurio) equisde')
    #     hora, minuto = obtener_tiempo_eliminacion()
    #     scheduler.add_job(eliminar_historial_automatico, 'cron', id='borrar_historial', hour=hora ,minute=minuto, replace_existing=True)
    #     print(f"Tarea programada para eliminar logs a las {hora}:{minuto}")
    #     scheduler.start()
    
    
def obtener_tiempo_eliminacion():
    parametro = Parametro.objects.filter(nombre_parametro='historial.mantener').first()
    if parametro:
        tiempo_realizar = parametro.valor.get('tiempo', [])
        print(tiempo_realizar)
    hora = tiempo_realizar['hora']
    minuto = tiempo_realizar['minutos']
    print(str(hora) + ' - ' + str(minuto))
    return int(hora), int(minuto)

def obtener_frecuencia():
    parametro = Parametro.objects.filter(nombre_parametro='historial.mantener').first()
    if parametro:
        frecuencias = parametro.valor.get('valores_programacion', [])
        opciones = ['A1', 'A2', 'A3']
        for opcion in opciones:
            if opcion in frecuencias:
                frecuencia = opcion
                break
        print(frecuencia)
    return frecuencia

def obtener_dias():
    parametro = Parametro.objects.filter(nombre_parametro='historial.mantener').first()
    if parametro:
        dias_semana = parametro.valor.get('valores_programacion', [])
        opciones = ['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7']
        dias_seleccionados = [opcion for opcion in opciones if opcion in dias_semana]
        nombres_dias = [PROGRAMACION_MAPPING[dia] for dia in dias_seleccionados]
        dias_cron = [int(dia[1]) - 1 for dia in dias_seleccionados]
        print(nombres_dias)
        print(dias_seleccionados)
        print(dias_cron)
    return dias_cron, nombres_dias