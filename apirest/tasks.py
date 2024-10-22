from celery import shared_task
from .models import historialCambios
from datetime import datetime, timedelta
from views import eliminar_historial_automatico

@shared_task
def ejecutar_eliminacion_historial():
    # Obtener los parametros
    parametro = obtener_parametros()

    if parametro:
        config = #parametro.valor
        activar = #config.get('activar', False)
        dias_ejecucion = #config.get('dias_ejecucion', [])
        semanas_frecuencia = #config.get('semanas_frecuencia', 1)
        
        # Verificar si la eliminacion esta activada
        if activar:
            # Verificar si hoy es uno de los dias configurados
            hoy = datetime.now().date()
            dia_semana = hoy.weekday()  # Lunes es 0, Domingo es 6

            if dia_semana in dias_ejecucion:
                # Verificar si estamos en la semana correcta (cada X semanas)
                semanas_desde_inicio = (hoy - parametro.fecha_creacion).days // 7
                if semanas_desde_inicio % semanas_frecuencia == 0:
                    # Ejecutar el codigo de eliminacion
                    eliminar_historial_automatico()
    else:
        print("Parámetro no encontrado.")