# # myapp/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
from .views import eliminar_historial_automatico  # Asegúrate de importar tu tarea
from .models import Parametro

def start_scheduler():
    scheduler = BackgroundScheduler()
    #Código Min Hor * * *
    hora, minuto = obtener_tiempo_eliminacion()
    scheduler.add_job(eliminar_historial_automatico, 'cron', hour=hora ,minute=minuto, id='perro')
    print(f"Tarea programada para eliminar logs a las {hora}:{minuto}")
    scheduler.start()
    
    
def obtener_tiempo_eliminacion():
    parametro = Parametro.objects.filter(nombre_parametro='historial.mantener').first()
    if parametro:
        tiempo_realizar = parametro.valor.get('tiempo', [])
        print(tiempo_realizar)
    hora = tiempo_realizar['hora']
    minuto = tiempo_realizar['minutos']
    print(str(hora) + ' - ' + str(minuto))
    return int(hora), int(minuto)

