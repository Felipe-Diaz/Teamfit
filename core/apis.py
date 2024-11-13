import requests
import pytz
from datetime import date, datetime, timedelta
import re
import ast
import json
from .models import Empleado

URL_BASE = 'http://teamfit.openscorp.com/api/'
API_KEY = 'RerPuUkAjjx7b2CDhw4XwDS30n3e5rH8qOh' 

"""
**DESCRIPCIÓN INICIAL**\n
**Parametros**\n
    parametros_necesario (tipo_dato): lore ipsum \n
**Return**\n
    VariableReturn (tipo_dato): lore ipsum
"""

#-para enviar las tareas al Oodo 
def enviar_datos_planning_slots(id, employee_id, allocated_hours, start_datetime, end_datetime, name):
    """
    **Envía los datos a Odoo utilizando la API**\n
    **Parametros**\n
        id (int): ID del recurso \n
        employee_id (int): ID del empleado \n
        allocated_hours (int): Cantidad de horas a asignar \n
        start_datetime (int): Fecha de inicio de la actividad (Día lunes de una semana) \n
        end_datetime (int): Fecha de fin de la actividad (Día viernes de una semana) \n
        name (int): Nombre de la actividad que se verá en Odoo. \n
    **Return**\n
        respuesta (Json): Objeto json que almacena la respuesta de la API. El formato es: \n
            {done:True, object: response.json}. En caso de fallar devolverá False
    """
    endpoint = 'planning_slot?'
    
    fecha_inicio = convertir_fecha_a_gmt(start_datetime)
    fecha_fin = convertir_fecha_a_gmt(end_datetime)
    
    id = f'resource_id={id}'
    employee = f'&employee_id={employee_id}'
    hours = f'&allocated_hours={allocated_hours}'
    start = f'&start_datetime={fecha_inicio}'
    end = f'&end_datetime={fecha_fin}'
    name = f'&name={name}'
    
    url = URL_BASE + endpoint + id + employee + hours + start + end + name
    headers = {
        'api-key' : API_KEY
    }
    
    try:
        upload = requests.post(url, headers=headers)
        if(upload.status_code == 200):
            upload = upload.json()
            respuesta = {
                'done':True,
                'object':upload
            }
            print('Se han enviado los datos')
            return respuesta
        else:
            print(upload.json())
            print('No se han guardado los datos')
            return False
    except Exception as e:
        print(f'Han ocurrido errores: \n{e}')
        return False
   
def obtener_api_recursos(page=1,page_size=80):
    """
    **Obtiene todos los recursos del sistema**\n
    **Parametros**\n
        page (int): Página a buscar \n
        page_size (int): Tamaño de la página a solicitada (Cuantos recursos vienen) \n
    **Return**\n
        recursos (Json): Json de la APi que contiene todos los recursos utilizados.
    """
    endpoint = 'resource'
    page = f'page={page}'
    page_size = f'page_size{page_size}'
    url = URL_BASE + endpoint + '?' + page + '&' + page_size
    headers = {
        'api-key' : API_KEY
    }
    try:
        response = requests.get(url, headers=headers)
        if(response.status_code == 200):
            response = response.json()
        else:
            return False
            
        if(response['total']>0):
            recursos = response['items']
            return recursos
        else:
            return False
            
    except Exception as e:
        print(f'Han ocurrido errores: \n{e}')
        return False
    
def obtener_api_empleados(page=1,page_size=120):
    """
    **Obtiene los empleados de la API**\n
    **Parametros**\n
        page (int): número de página a visualizar en la API. \n
        page_size (int) : Tamaño de la página a visualizar en la API \n
    **Return**\n
        empleados (Json): Json que contiene todos los empleados de Odoo.
    """
    endpoint = 'employees'
    page = f'page={page}'
    page_size = f'page_size{page_size}'
    url = URL_BASE + endpoint
    headers = {
        'api-key' : API_KEY
    }
    try:
        response = requests.get(url, headers=headers)
        if(response.status_code == 200):
            response = response.json()
        else:
            return False
            
        if(response['total']>0):
            empleados = response['items']
            return empleados
        else:
            return False
            
    except Exception as e:
        print(f'Han ocurrido errores: \n{e}')
        return False
    
def obtener_planning_slots(page=1, page_size=80):
    """
    **Obtiene los planning slots existentes en el sistema**\n
    **Parametros**\n
        page (int): número de página a visualizar en la API. \n
        page_size (int) : Tamaño de la página a visualizar en la API \n
    **Return**\n
        slots (json): Json con todos los planing slots obtenidos.
    """
    endpoint = 'planning_slot'
    page = f'page={page}'
    page_size = f'page_size{page_size}'
    url = URL_BASE + endpoint + '?' + page + '&' + page_size
    headers = {
        'api-key' : API_KEY
    }
    try:
        response = requests.get(url, headers=headers)
        if(response.status_code == 200):
            response = response.json()
        else:
            return False
        if(response['total']>0):
            slots = response['items']
            return(slots)
        else:
            return False
    except Exception as eeee:
        print(f'error al obtener planning slots:\n{eeee}')
        return False
    
def obtener_planning_slots_por_semana(page=1, page_size=80, semana=1, anio=2025):
    """
    **Obtiene todos los planing slots relacionados a una semana.**\n
    **Parametros**\n
        page (int): número de página a visualizar en la API. \n
        page_size (int): Tamaño de la página a visualizar en la API \n
        semana (int): Semana en la ue se buscan atividades \n
        anio (int): Año en el que se buscarán las actividades. \n
    **Return**\n
        slots (Json): Json con todos los slots en la semana seleccionada.
    """
    endpoint = 'planning_slot'
    page = f'page={page}'
    page_size = f'page_size{page_size}'
    url = URL_BASE + endpoint + '?' + page + '&' + page_size
    headers = {
        'api-key' : API_KEY
    }
    plan_slots = []
    try:
        response = requests.get(url, headers=headers)
        if(response.status_code == 200):
            response = response.json()
        else:
            return False
        if(response['total']>0):
            slots = response['items']
            
            for slot in slots:
                _, sem_inicio, _ =  datetime.fromisoformat(slot['start_datetime']).isocalendar()
                _, sem_final, _ = datetime.fromisoformat(slot['end_datetime']).isocalendar()
                anio_actividad = datetime.fromisoformat(slot['start_datetime']).year
                if(sem_inicio == semana and anio_actividad == anio):
                    plan_slots.append(slot)
            return(plan_slots)
        else:
            return False
    except Exception as e:
        print(f'error al obtener planning slots:\n{e}')
        return False

def obtener_departamento_empleado(page=1, page_size=80, id=1):
    """
    **Obtiene el departamento de un empleado**\n
    **Parametros**\n
        page (int): número de página a visualizar en la API. \n
        page_size (int) : Tamaño de la página a visualizar en la API \n
        id (int): ID del departamento a buscar
    **Return**\n
        departamento (string): Departamento solicitado.
    """
    endpoint = 'departments'
    page = f'page={page}'
    page_size = f'page_size{page_size}'
    url = URL_BASE + endpoint + '?' + page + '&' + page_size
    headers = {
        'api-key' : API_KEY
    }
    
    try:
        response = requests.get(url, headers=headers)
        if(response.status_code == 200):
            response = response.json()
            departamentos = response['items']
        else:
            return False
        
        for depto in departamentos:
            if(depto['id'] == id):
                departamento = depto['complete_name']
                break
        return departamento

    except Exception as e:
        print(f'Ha ocurrido un error: \n{e}')
        
def obtener_trabajo_empleado(page=1, page_size=80, id=1):
    """
    **DESCRIPCIÓN INICIAL**\n
    COMO FUNCIONA LA FUNCIÓN ALGO MÁS ESPECíFICO \n
    **Parametros**\n
        page (int): número de página a visualizar en la API. \n
        page_size (int): Tamaño de la página a visualizar en la API \n
        id (int): ID del trabajo buscado \n
    **Return**\n
        trabajo (string): Cadena de texto conteniendo el trabajo buscado
    """
    endpoint = 'jobs'
    page = f'page={page}'
    page_size = f'page_size{page_size}'
    url = URL_BASE + endpoint + '?' + page + '&' + page_size
    headers = {
        'api-key' : API_KEY
    }
    
    try:
        response = requests.get(url, headers=headers)
        if(response.status_code == 200):
            response = response.json()
            trabajos = response['items']
        else:
            return False
        
        for trab in trabajos:
            if(trab['id'] == id):
                trabajo = trab['name']
                break
        return trabajo

    except Exception as e:
        print(f'Ha ocurrido un error: \n{e}')
    
#Junily was here
def obtener_resource_calendar(page=1,page_size=80):
    """
    **DESCRIPCIÓN INICIAL**\n
    COMO FUNCIONA LA FUNCIÓN ALGO MÁS ESPECíFICO \n
    **Parametros**\n
        page (int): número de página a visualizar en la API. \n
        page_size (int) : Tamaño de la página a visualizar en la API \n
    **Return**\n
        calendars (Json): Json con todos los calendarios del sistema.
    """

    endpoint = 'resource_calendar'
    page = f'page={page}'
    page_size = f'page_size{page_size}'
    url = URL_BASE + endpoint + '?' + page + '&' + page_size
    headers = {
        'api-key' : API_KEY
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data['total'] > 0:
                calendars = data['items']
                return calendars
            else:
                return False
        else:
            return False

    except Exception as e:
        print(f'Ha ocurrido un error: \n{e}')
        return
#Ty

##Funciones de Útil para el sistema. 
def convertir_fecha_a_gmt(fecha_str):
    """
    **Convierte la fecha al formato UTC 0**\n
    **Parametros**\n
        fecha_str (str): Solicita una fecha en formato String \n
    **Return**\n
        hora_gmt (string): Hora UTC 0 en formato string.
    """
    fecha = datetime.strptime(fecha_str, '%Y-%m-%dT%H:%M:%S')
    chile_tz = pytz.timezone('America/Santiago')
    
    if fecha.tzinfo is None:
        fecha = chile_tz.localize(fecha)
        
    gmt_tz = pytz.timezone('GMT')
    hora_gmt = fecha.astimezone(gmt_tz)
    
    hora_gmt = datetime.strftime(hora_gmt, '%Y-%m-%dT%H:%M:%S')
    
    return hora_gmt


def convertir_fecha_a_chile(fecha_str):
    """
    **Convierte la hora UTC 0 a hora de Chile UTC-3**\n
    **Parametros**\n
        fecha_str (str): String con la fecha a convertir \n
    **Return**\n
        hora_chile (str): String de la fecha en formato Chile.
    """
    fecha = datetime.strptime(fecha_str, '%Y-%m-%dT%H:%M:%S')
    gmt_tz = pytz.timezone('GMT')
    
    if fecha.tzinfo is None:
        fecha = gmt_tz.localize(fecha)

    chile_tz = pytz.timezone('America/Santiago')
    hora_chile = fecha.astimezone(chile_tz)
    hora_chile = datetime.strftime(hora_chile, '%Y-%m-%dT%H:%M:%S')

    return hora_chile

def convertir_fecha_a_string(fecha):
    """
    **Convierte la fecha entregada a String en el formato para Odoo**\n
    **Parametros**\n
        fecha (Datetime): Fecha a convertir en string \n
    **Return**\n
        fecha (string): Fecha transformada en string.
    """
    formato = '%Y-%m-%dT%H:%M:%S'
    fecha = datetime.strftime(fecha, formato)
    return fecha
#
def obtener_empleados_con_horas():
    """
    **Obtiene un empleado con las horas**\n    
    **Parametros**\n
        Ninguno \n
    **Return**\n
        empleados_dict (Dict): Diccionario con los datos de todos los empleados.
    """
    empleados = obtener_api_empleados()
    empleados_dict = {}
    
    if(not empleados):
        return False
    
    for empleado in empleados:
        horas = obtener_horas_recurso(empleado['resource_calendar_id'])
        rol = obtener_trabajo_empleado(id=empleado['job_id'])
        depto = obtener_departamento_empleado(id=empleado['department_id'])
        empleadoJson = {
            'id_empleado' : empleado['id'],
            'id_recurso' : empleado['resource_id'],
            'empleado' : empleado['name'],
            'Rol' : rol,
            'Departamento': depto,
            'horas_semana' : horas
        }
        empleados_dict[str(empleado['id'])] = empleadoJson
    return empleados_dict
#
def cargar_empleados():
    """
    **Carga los empleados a la DB**\n
    **Parametros**\n
        Ninguno \n
    **Return**\n
        Boolean. True si logró realizarlo, False si no fue capaz.
    """
    empleados = obtener_api_empleados()
    roles_necesario = ['Jefe de Proyectos', 'Ingeniero de Proyecto']
    Empleado.objects.all().update(activo=False)
    
    if(not empleados):
        return False
    
    for empleado in empleados:
        horas = obtener_horas_recurso(empleado['resource_calendar_id'])
        rol = obtener_trabajo_empleado(id=empleado['job_id'])
        
        if(not rol):
            continue
        
        if(rol not in roles_necesario):
            continue
        
        Empleado.objects.update_or_create(
            nombre = empleado['name'],
            id_recurso = empleado['resource_id'],
            id_empleado = empleado['id'],
            defaults={
                'rol':rol,
                'horas_totales':horas,
                'activo':True,
            }
        )
    return True
#
def obtener_horas_recurso(id=1):
    """
    **Obtienes las horas de un recurso**\n
    **Parametros**\n
        id (int): ID del horario solicitado \n
    **Return**\n
        horas_semanales (int): Cantidad de horas obtenidas
    """
    calendario = obtener_resource_calendar()
    for horario in calendario:
        if(horario['id'] == id):
            nombre = horario['name']
            match = re.search(r'\d+', nombre)
            if(match):
                horas_semanales = match.group()
            else:
                horas_semanales = 40
            break
    return int(horas_semanales)
#
def convertir_datos_asignacion(semana, año):
    """
    **Convierte el número de semana y año a un rango de fechas con el formato que requiere Odoo.**\n
    **Parametros**\n
        semana (int): Semana a buscar \n
        año (int): Año en que se realizará la búsqueda \n
    **Return**\n
        fecha (Dict): Diccionario con las fechas de inicio de semana, el fin de la semana y el año \n
        formato: {"semana_inicio":SemanaInicio, "semana_fin":SemanaFin, "año":Año}
    """
    primer_dia_del_año = date(año, 1, 1)
    inicio_semana = primer_dia_del_año + timedelta(days=(semana - 1) * 7 - primer_dia_del_año.isoweekday() + 1)
    fin_semana = inicio_semana + timedelta(days=4)
    
    formato_odoo = "%Y-%m-%dT08:30:00"
    
    fecha = {
        "semana_inicio": inicio_semana.strftime(formato_odoo),
        "semana_fin": fin_semana.strftime(formato_odoo),
        "año":año
    }
    #Resultado: Inicio: 2024-10-07T08:30:00 - Fin: 2024-10-13T08:30:00
    return fecha

#Funcion para llamar a la api de odoo y obtener los recursos y empleados, apis.py.
def cal_disponibilidad(semana, anio):
    """
    **Obtiene la disponibilidad en base al Planing Slots**\n
    **Parametros**\n
        semana (int): Semana en que se puede \n
        anio (int): Año en que se busca la disponibilidad \n
    **Return**\n
        utilizacion_empleados (Dict): Diccionario con los empleados y semanas utilizadas en Planing Slots.
    """
    planning = obtener_planning_slots_por_semana(semana=semana, anio=anio)
    recursos = obtener_api_recursos()
    empleados = obtener_api_empleados()
    utilizacion_empleados = {}
    
    #Actualizar lógica para considerar si no hay plannings.
    if empleados and recursos:
        for empleado in empleados:
            id_empleado = empleado['id']
            id_recurso = empleado['resource_calendar_id']
            calendario = obtener_horas_recurso(empleado['resource_calendar_id'])
            cant_horas = 0
            planes = []
            
            if(planning):
                for plan in planning:
                    if(plan['employee_id'] == id_empleado):                    
                        horas_utilizadas = plan['allocated_hours']
                        cant_horas += horas_utilizadas
                        planes.append(plan['id'])
                    
            horas_disponibles = calendario - cant_horas

            utilizacion_empleados[str(id_empleado)] = {
                    'resource_id' : id_recurso,
                    'employee_id' : id_empleado,
                    'employee' : empleado['name'],
                    'role': "N/A",
                    'horas_semanales' : calendario,
                    'horas_utilizadas' : cant_horas,
                    'horas_disponibles' : horas_disponibles,
                }
        return utilizacion_empleados
    
#Funcion para llamar a la api de odoo y obtener los recursos, empleados y semanas, apis.py.
def cal_disponibilidad_varias_semanas(semana_actual, anio_actual, cant_semanas=10):
    """
    **Obtiene la disponibilidad en una semana específica**\n
    **Parametros**\n
        semana_actual (int): Semana en que se buscará la disponibilidad \n
        anio_actual (int): Año en que se buscará la disponibilidad \n
        cant_semana (int): cantidad de semanas a buscar \n
    **Return** \n 
        utilizacion_empleados (Dict): Diccionario con la disponibilidad solicitada
    """
    recursos = obtener_api_recursos()
    empleados = obtener_api_empleados()
    utilizacion_empleados = {}
    
    hoy = date.today()
    semana_actual = 0
    anio, semana_actual, dia_semana = hoy.isocalendar()

    for i in range(cant_semanas + 1):
        semana_key = f"Sem{semana_actual}"

        if semana_key not in utilizacion_empleados:
            utilizacion_empleados[semana_key] = {'sem':semana_actual, 'anio':anio}
            
        
        if empleados and recursos:
            for empleado in empleados:
                id_empleado = empleado['id']
                id_recurso = empleado['resource_calendar_id']
                calendario = obtener_horas_recurso(id_recurso)
                cant_horas = 0
                planes = []
                planning = obtener_planning_slots_por_semana(semana=semana_actual, anio=anio)
                
                if(planning):
                    for plan in planning:
                        if(plan['employee_id'] == id_empleado):                    
                            horas_utilizadas = plan['allocated_hours']
                            cant_horas += horas_utilizadas
                            planes.append(plan['id'])
                    
                horas_disponibles = calendario - cant_horas
                porcentaje_utilizado = round((cant_horas / calendario) * 100, 2) if calendario > 0 else 0

                utilizacion_empleados[semana_key][str(id_empleado)] = {
                        'resource_id' : id_recurso,
                        'employee_id' : id_empleado,
                        'employee' : empleado['name'],
                        'role': "N/A",
                        'horas_semanales' : calendario,
                        'horas_utilizadas' : cant_horas,
                        'horas_disponibles' : horas_disponibles,
                        'porcentaje_utilizado' : porcentaje_utilizado,
                    }
        
        siguiente_semana = hoy + timedelta(weeks= i + 1)
        semana_actual = siguiente_semana.isocalendar()[1]  # Solo el número de semana
        anio_actual = siguiente_semana.isocalendar()[0]    # Año correspondiente
        
    return utilizacion_empleados
    