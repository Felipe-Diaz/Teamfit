import unicodedata
from .models import Asignacion, Empleado, historialCambios, Parametro, proyectosAAgrupar
from django.contrib.auth.models import User
from django.db.models import Sum, Subquery, Count, Q
from decimal import Decimal
from django.utils import timezone
from .forms import CATEGORIAS_MAPPING, PROGRAMACION_MAPPING, ESCENARIOS_MAPPING
from .forms import CategoriasForm, ProgramacionForm, EscenariosForm
import pandas as pd
##Funciones relacionadas con la asignación
def obtener_empleado(proyecto_id, rol, semana, anio, cant_horas):
    """
    **Obtiene un empleado que esté disponible.**\n
    Primero intenta utilizar al empleado asignado anteriormente, en caso de no tener asignado a un empleado 
    anteriormente o que este no esté disponible, buscará un empleado disponible dentro de la DB. \n
    **Parametros**\n
      proyecto_id (int): ID del proyecto que se busca asignar \n
      rol (string): Rol necesario para asignar \n
      semana (int): Número de semana a asignar \n
      anio (int): Año en que se realizará la asignación \n
      cant_horas (int): La cantida de horas que se asignarán \n
    **Return**\n
      empleado (Empleado): Un objeto de tipo Empleado
    """
    asignaciones = Asignacion.objects.select_related('empleado').filter(proyecto=proyecto_id,empleado__rol=rol)
    asignado = False
    if(asignaciones):
        asignacion = asignaciones.first()
        empleado = asignacion.empleado
        disponible = verificar_disponibilidad(empleado, semana, anio, cant_horas)
        if(disponible):
            asignado = True
            return empleado
        
    if(not asignado):
        empleados = Empleado.objects.filter(rol=rol, activo=True)\
            .annotate(cantidad_proyectos=Count(
                'asignacion__proyecto', 
                filter=Q(asignacion__semana=semana, asignacion__anio=anio),
                distinct=True
            ))\
            .order_by('cantidad_proyectos')
        print(empleados)
        print('-------------------------------')
        for idx, empleado in enumerate(empleados):
            disponible = verificar_disponibilidad(empleado, semana, anio, cant_horas)
            if(disponible):
                asignado = True
                return empleado
    return None

def verificar_disponibilidad(id_emp, semana, anio, cant_horas):
    """
    **Verifica la disponibilidad de un empleado**\n
    Verifica la disponibilidad comparando su horario con la cantidad de horas que tendría si se le asignasen las solicitadas  \n
    **Parametros**\n
      id_emp (int): ID del empleado que debe validarse  \n
      semana (int): Número de semana a asignar \n
      anio (int): Año en que se realizará la asignación \n
      cant_horas (int): cantidad de horas que serán asignadas \n
    **Return**\n
      VariableReturn: lore ipsum
    """
    asignaciones = Asignacion.objects.filter(empleado=id_emp, semana=semana, anio=anio).values('semana','anio').annotate(
        total_horas=Sum('horas_asignadas')
    ).order_by('semana')
    if(asignaciones):
        horas = asignaciones.first()['total_horas']
        horas_maximas = id_emp.horas_totales
        horas_totales_utilizadas = Decimal(horas) + Decimal(cant_horas)
        if(horas_totales_utilizadas <= horas_maximas):
            return True
        else:
            return False
    else:
        return True

def obtener_proyectos_sin_asignar():
    """
    **Devuelve los proyectos que no hayan sido asignados**\n
    **Parametros**\n
        Parametros: Ninguno\n
    **Return**\n
        proyectos_no_asignados(list(proyectosAAgrupar)): Una lista de proyectos sin asignar. \n
        En caso de no haber proyectos retornará None.
    """

    proyectos = proyectosAAgrupar.objects.filter(fechaFin__gt=timezone.now()).order_by('fechaInicio')
    proyectos_asignados = Asignacion.objects.values('proyecto')
    proyectos_no_asignados = proyectos.exclude(id__in=Subquery(proyectos_asignados))
    return proyectos_no_asignados

##Funciones relacionadas con obtener la creación del historial
def obtener_subcategorias():
    """
    **Obtiene las disintas subcategorías**\n
    **Parametros**\n
        No utiliza \n
    **Return**\n
        categorias (Json): Json de subcategorías disponibles  
    """
    categorias = {
    "A1": "Login",
    "A2": "Logout",
    "B1": "Cambio de parametros",
    "B2": "Cambio de configuraciones en la base de datos",
    "C1": "Limpieza de datos",
    "D1": "Errores",
    "E1": "Agregó Proyectos",
    "E2": "Agregó usuario",
    "E3": "Desactivo usuario",
    "E4": "Activo usuario",
    "F1": "Cambio un cargo",
    "F2": "Actualizó permisos",
    "G1": "Realizó la clusterización",
    "G2": "Asignó los recursos",
    "G3": "Subió datos a Odoo"
    }
    return categorias

def obtener_categorias():
    """
    **Obtiene las disintas categorías**\n
    **Parametros**\n
        No utiliza \n
    **Return**\n
        categorias (Json): Json de categorías disponibles
    """
    categorias = {
    'A': "Autentificación",
    'B': "Configuración",
    'C': "Mantenimiento",
    'D': "Error",
    'E': "Auditoría",
    'F': "Seguridad",
    'G': "Modelo"
    }
    return categorias

def obtener_prioridades():
    """
    **Obtiene las disintas prioridades en base a la subcategoría**\n
    **Parametros**\n
        No utiliza \n
    **Return**\n
        categorias (Json): Json de prioridades disponibles  
    """
    prioridades = {
        "A1": "1",
        "A2": "1",
        "A3": "1",
        "A4": "1",
        "B1": "4",
        "B2": "3",
        "C1": "3",
        "C2": "3",
        "C3": "3",
        "D1": "2",
        "E1": "2",
        "E2": "3",
        "E3": "3",
        "E4": "3",
        "F1": "3",
        "F2": "3",
        "F3": "2",
        "G1": "3",
        "G2": "3",
        "G3": "3"
    }
    return prioridades

def verificar_usuario_hist(user):
    """
    **Verifica si el usuario existe, si no, entrega el primer usuario.**\n 
    **NO DEBERÍA ACTIVARSE SI HAY UN USUARIO ACTIVO**\n
    **Parametros**\n
        user (User): Usuario u objeto usuario para validar \n
    **Return**\n
        usuario (User): Usuario para almacenar el historial
    """
    if(user is None):
        usuario = User.objects.all().first()
    else:
        usuario = user
    return usuario

#Almacena el historial solicitando desc, tipoInfo y usuario
def almacenarHistorial(categoria={'Cat':"A",'Sub':'1'}, usuario=None):
    """**Almacena el historial.**

        **Parametros:**\n 
        categoria (Json): Diccionario con la categoria y la subcategoría.\n
                Formato categoría {"cat":"A","sub":"1"}
        
        **Return:**\n
        histCambios (historialCambios): Objeto de tipo HistorialCambios.
    """
    fecha = timezone.now()
    
    categorias = obtener_categorias()
    subcategorias = obtener_subcategorias()
    prioridades = obtener_prioridades()
    
    subcategoria_clave = categoria['Cat'] + categoria['Sub']
    
    categoria_texto = categorias.get(categoria['Cat'], "Categoría desconocida")
    subcategoria_texto = subcategorias.get(subcategoria_clave, "Subcategoría desconocida")
    prioridad = prioridades.get(subcategoria_clave, "Prioridad desconocida")
    usuario = verificar_usuario_hist(usuario)
    
    histCambios = historialCambios.objects.create(fecha=fecha, categoria=categoria_texto, subcategoria=subcategoria_texto, 
                                    prioridad=prioridad, usuario=usuario)
    return histCambios

##Funciones relacionadas con la eliminación automática del historial
def eliminar_historial_automatico():
    # Obtener el parámetro con la clave "historial.mantener"
    parametro = Parametro.objects.filter(nombre_parametro='historial.mantener').first()
    
    if parametro:
        valores_a_mantener = parametro.valor.get('valores_a_mantener', [])
        subcategorias = obtener_subcategorias()
        nombres_subs = []

        for idx, val in enumerate(valores_a_mantener):
            nombres_subs.append(subcategorias.get(val, "Subcategoría desconocida"))

        if valores_a_mantener:
            count, _ = historialCambios.objects.exclude(subcategoria__in=nombres_subs).delete()
            print(f'{count} registros eliminados exitosamente.')
        else:
            print('La lista de valores a mantener está vacía. No se eliminaron datos.')
    else:
        print('Parámetro no encontrado.')
        
def cambiar_scheduler(hora, minutos, id):
    from .scheduler import scheduler
    try:
        job = scheduler.get_job(id)
        scheduler.reschedule_job(id, trigger='cron', hour= hora, minute= minutos)
        print(f"Tarea actualizada a las {hora}:{minutos}.")
        return(True)
    except Exception as e:
        print(f'Ha ocurrido un error: \n {e}')
        return False
        
##Funciones relacionadas con los parámetros del sistema
def obtener_campos_secundarios(form,tipo):
    """
    **Obtiene los campos secundarios de un formulario**\n
    **Parametros**\n
        form (Form): Formulario de parámetros \n
    **Return**\n
        to_keep (list): Lista con las categorías a marcar en el formulario
    """
    if(tipo == 'Cat'):
        sub_cats = obtener_subcategorias()
    elif(tipo == 'Cron'):
        sub_cats = PROGRAMACION_MAPPING
    elif(tipo == 'Esce'):
        sub_cats = ESCENARIOS_MAPPING
    to_keep = []
    try:
        for val in sub_cats:
            field = form.get_field_by_code(val)
            field_name = field.name
            if(form.cleaned_data.get(field_name)):
                to_keep.append(val)
        return to_keep
    except Exception as e:
        print('Error al obtener los campos secundarios: ' + str(e))
        return []
###Formulario de parámetros
def obtener_valores_formulario_parametro(form):
    """
    Obtiene los valores de los parámetros almacenados, para luego cargarlos en el formulario
    
    Parametros: Solicita el formulario de parámetros
    
    Return: Entrega el formulario con los datos cargados
    """
    try:
        parametro = Parametro.objects.get(nombre_parametro='historial.mantener')
        valor_parametro = parametro.valor
        valores_a_mantener = valor_parametro.get('valores_a_mantener', [])
    except:
        valores_a_mantener = []
    
    initial_data = {field_name: False for field_name in CATEGORIAS_MAPPING.values()}
    
    for val in valores_a_mantener:
        field = CATEGORIAS_MAPPING.get(val)
        if field:
            initial_data[field] = True          
    initial_data = marcar_categorias_principales_parametros(initial_data=initial_data)

    form_categorias = CategoriasForm(initial=initial_data, prefix='categorias')
    return form_categorias

def marcar_categorias_principales_parametros(initial_data):
    """
    Devuelve el formulario con las categorías principales marcadas
    
    Parametros: initial_data es el valor del formulario con los campos marcados
    
    Return: Retorna el formulario con los campos principales marcados
    """
    categorias_principales = set(key for key in CATEGORIAS_MAPPING.keys() if len(key) == 1)
    for categoria in categorias_principales:
        sub_categorias = [sub_key for sub_key in CATEGORIAS_MAPPING.keys() if sub_key.startswith(categoria) and len(sub_key) > 1]
        
        if all(initial_data[CATEGORIAS_MAPPING[sub_key]] for sub_key in sub_categorias):
            initial_data[CATEGORIAS_MAPPING[categoria]] = True
    return initial_data
###Formulario de Programación
def obtener_valores_formulario_parametro_programacion(form):
    """
    Obtiene los valores de los parámetros de programación almacenados, para luego cargarlos en el formulario
    
    Parametros: Solicita el formulario de parámetros
    
    Return: Entrega el formulario con los datos cargados
    """
    try:
        parametro = Parametro.objects.get(nombre_parametro='historial.mantener')
        valor_parametro = parametro.valor
        valores_programacion = valor_parametro.get('valores_programacion', [])
    except:
        valores_programacion = []
    
    initial_data = {field_name: False for field_name in PROGRAMACION_MAPPING.values()}
    
    for val in valores_programacion:
        if isinstance(val, dict):
            initial_data['hora'] = val.get('hora', 0)
            initial_data['minutos'] = val.get('minutos', 0)
        else:
            field = PROGRAMACION_MAPPING.get(val)
            if field:
                initial_data[field] = True        
    initial_data = marcar_programacion_principal_parametros(initial_data=initial_data)

    form = ProgramacionForm(initial=initial_data, prefix='programacion')
    return form

def marcar_programacion_principal_parametros(initial_data):
    """
    Devuelve el formulario de programación con las categorías principales marcadas
    
    Parametros: initial_data es el valor del formulario con los campos marcados
    
    Return: Retorna el formulario con los campos principales marcados
    """
    programaciones_principales  = set(key for key in PROGRAMACION_MAPPING.keys() if len(key) == 1)
    for programacion  in programaciones_principales :
        sub_programaciones   = [sub_key for sub_key in PROGRAMACION_MAPPING.keys() if sub_key.startswith(programacion) and len(sub_key) > 1]
        
        if all(initial_data[PROGRAMACION_MAPPING[sub_key]] for sub_key in sub_programaciones):
            initial_data[PROGRAMACION_MAPPING[programacion]] = True
    return initial_data
###Formulario de escenarios
def obtener_valores_formulario_parametro_escenarios(form):
    """
    Devuelve el formulario con las categorías principales marcadas. Específico para el formulario de escenarios
    
    Parametros: initial_data es el valor del formulario con los campos marcados
    
    Return: Retorna el formulario con los campos principales marcados
    """
    try:
        parametro = Parametro.objects.get(nombre_parametro='asignacion.tipo')
        valor_parametro = parametro.valor
        valores_escenarios = valor_parametro.get('valores_escenarios', [])
    except:
        valores_escenarios = []
    
    initial_data = {field_name: False for field_name in ESCENARIOS_MAPPING.values()}
    
    for val in valores_escenarios:
        field = ESCENARIOS_MAPPING.get(val)
        if field:
            initial_data[field] = True          
    initial_data = marcar_escenarios_principal_parametros(initial_data=initial_data)

    form_escenarios = EscenariosForm(initial=initial_data, prefix='escenarios')
    return form_escenarios

def marcar_escenarios_principal_parametros(initial_data):
    """
    Devuelve el formulario de escenarios con las categorías principales marcadas
    
    Parametros: initial_data es el valor del formulario con los campos marcados
    
    Return: Retorna el formulario con los campos principales marcados
    """
    escenarios_principales  = set(key for key in ESCENARIOS_MAPPING.keys() if len(key) == 1)
    for escenarios  in escenarios_principales :
        sub_escenarios   = [sub_key for sub_key in ESCENARIOS_MAPPING.keys() if sub_key.startswith(escenarios) and len(sub_key) > 1]
        
        if all(initial_data[ESCENARIOS_MAPPING[sub_key]] for sub_key in sub_escenarios):
            initial_data[ESCENARIOS_MAPPING[escenarios]] = True
    return initial_data

#Funciones relacionadas con validar los proyectos:

def entregar_mensaje_df_valido():
    """
    **Entrega un Json para entregar una respuesta válida**\n
    **Parametros**\n
        Ninguno \n
    **Return**\n
        respuesta (Dict): Diccionario con datos de respuesta válido y un mensaje.
            formato: {'mesg':string,'valido':boolean}.
    """
    mesg = 'No se han encontrado datos que puedan provocar conflictos.'
    respuesta = {'mesg':mesg,'valido':True}
    return respuesta

def validar_linea_tipo_df(row, tipos_proy):
    """
    **valida la linea de negocio y el tipo de una fila en un dataframe**\n
    **Parametros**\n
        row (row Dataframe): Fila en la que se aplicará la función \n
        tipos_proy (Dict): Valores necesarios para la linea de negocio y tipo de proyecto \n
    **Return**\n
        Boolean: True si hay problemas, False si no hay
    """
    linea = row['lineaNegocio']
    tipo = row['tipo']
    tipos = tipos_proy.get(linea, [])
    
    if tipo not in tipos:
        return True
    else:
        return False

def validar_agencia(df):
    """
    **Valida que la agencia no tenga valores ilegales.**\n
    **Parametros**\n
        df (Dataframe): Un objeto de tipo dataframe \n
    **Return**\n
        respuesta (dict): Diccionario con el boolean y mensaje
            formato: {'mesg':string,'valido':boolean}.
    """
    if not isinstance(df, pd.DataFrame):
        mesg = "El archivo entregado no puede ser leido correctamente, intentelo de nuevo más tarde."
        respuesta =  {'mesg':mesg, 'valido':False}
        return respuesta
    try:
        valores_validos = {'si', 'no', None, '0', '1'}
        df['C/Agencia_normalizada'] = df['usoAgencia'].apply(normalizar_cadena)
        valores_no_validos = df[~df['C/Agencia_normalizada'].isin(valores_validos)]
        if not valores_no_validos.empty:
            mesg = "La columna 'C/Agencia' contiene valores no válidos. Solo se aceptan 'sí', 'no' o nulos."
            respuesta = {'mesg': mesg, 'valido': False}
            return respuesta
        
        respuesta = entregar_mensaje_df_valido()
        return respuesta
    except Exception as e:
        print(f'Ha ocurrido un error: \n{e}')
        mesg = "La columna 'C/Agencia' contiene valores no válidos. Solo se aceptan 'sí', 'no' o nulos."
        respuesta = {'mesg':mesg,'valido':False}
        return respuesta

def normalizar_cadena(cadena):
    if pd.isnull(cadena):
        return cadena
    return unicodedata.normalize('NFKD', cadena).encode('ascii', 'ignore').decode('utf-8').lower()
    
def validar_columnas_nulas_df(df):
    """
    **Valida que las columnas importantes no sean nulas**\n
    **Parametros**\n
        df (Dataframe): Un objeto de tipo dataframe \n
    **Return**\n
        respuesta (dict): Diccionario con el boolean y mensaje
            formato: {'mesg':string,'valido':boolean}.
    """
    if not isinstance(df, pd.DataFrame):
        mesg = "El archivo entregado no puede ser leido correctamente, intentelo de nuevo más tarde."
        respuesta =  {'mesg':mesg, 'valido':False}
        return respuesta
    
    columns_to_check = ['id', 'proyecto', 'lineaNegocio', 'tipo', 'cliente', 'createDate', 'montoOfertaCLP', 'egresosNoHHCLP', 'ocupacionInicio']
    if df[columns_to_check].isnull().values.any():
        ids_nulos = df.loc[df[columns_to_check].isnull().any(axis=1), 'id'].tolist()
        ids_nulos = sorted(ids_nulos)
        if(len(ids_nulos) > 0):
            mesg = ("Valores nulos en los siguientes registros: <br> <strong>" + str(ids_nulos[:5]) + "</strong> entre otros. <br>"
                    "Por favor, verifique los registros indicados. <br>"
                    '<i class="fa fa-info-circle" data-toggle="tooltip" data-html="true" title="<div>'
                    '<p>Los datos presentan problemas. Por favor, verifique lo siguiente:</p>'
                    '<ul>'
                        "<li>Las Columnas 'id', 'proyecto', 'Línea de Negocio', 'tipo', 'cliente', 'create_date',<br>"
                        "'Monto Oferta CLP', 'Ocupación Al Iniciar' (%), 'ocupacionInicio', 'InicioProyecto' y 'FinPlanificado' <br>"
                        '<strong>NO PUEDEN CONTENER DATOS NULOS O VACÍOS</strong></li>'
                        '<li>Las columnas deben tener exactamente <strong> el mismo nombre que se solicita</strong></li>'
                    '</ul>'
                    '</div>"></i>'
                    )
            respuesta = {'mesg':mesg,'valido':False}
            return respuesta
    else:
        respuesta = entregar_mensaje_df_valido()
        return respuesta

def validar_numeros_negativos(df):
    """
    **Valida los números negativos de las distintas columnas**\n
    **Parametros**\n
        df (Dataframe): Un objeto de tipo dataframe \n
    **Return**\n
        respuesta (dict): Diccionario con el boolean y mensaje
            formato: {'mesg':string,'valido':boolean}.
    """
    if not isinstance(df, pd.DataFrame):
        mesg = "El archivo entregado no puede ser leido correctamente, intentelo de nuevo más tarde."
        respuesta =  {'mesg':mesg, 'valido':False}
        return respuesta
    try:
        if (df['egresosNoHHCLP'] < 0).any() or (df['montoOfertaCLP'] < 0).any() or (df['ocupacionInicio'] < 0).any() or (df['cliente'] < 0).any() or (df['id'] < 0).any():
            mesg = "Los valores de 'id', 'Egresos No HH CLP', 'Monto Oferta CLP' y/o ocupacion Inicio deben ser un número no negativo"
            respuesta = {'mesg': mesg, 'valido': False}
            return respuesta
        else:
            respuesta = entregar_mensaje_df_valido()
            return respuesta
    except:
        mesg = "Algunos valores de 'id', 'Egresos No HH CLP', 'Ocupación Inicio', 'Monto Oferta CLP' o 'cliente' son nulas o no son válidas."
        respuesta = {'mesg': mesg, 'valido': False}
        return respuesta

def validar_fechas_df(df):
    """
    **Valida las fechas del dataframe**\n
    **Parametros**\n
        df (Dataframe): Un objeto de tipo dataframe \n
    **Return**\n
        respuesta (dict): Diccionario con el boolean y mensaje
            formato: {'mesg':string,'valido':boolean}.
    """
    if not isinstance(df, pd.DataFrame):
        mesg = "El archivo entregado no puede ser leido correctamente, intentelo de nuevo más tarde."
        respuesta =  {'mesg':mesg, 'valido':False}
        return respuesta
    
    try:
        df['createDate'] = pd.to_datetime(df['createDate']).dt.strftime('%Y-%m-%d')
        df['Cierre'] = pd.to_datetime(df['cierre']).dt.strftime('%Y-%m-%d')
        df['InicioProyecto'] = pd.to_datetime(df['InicioProyecto']).dt.strftime('%Y-%m-%d')
        df['FinPlanificado'] = pd.to_datetime(df['FinPlanificado']).dt.strftime('%Y-%m-%d')

        if df['createDate'].isnull().any() or df['cierre'].isnull().any():
            mesg = "Algunas fechas en 'create_date' o 'Cierre' son nulas o no son válidas."
            respuesta = {'mesg': mesg, 'valido': False}
            return respuesta
        
        if df['InicioProyecto'].isnull().any() or df['FinPlanificado'].isnull().any():
            mesg = "Algunas fechas en 'Inicio Proyecto' o 'Fin Planificado' son nulas o no son válidas."
            respuesta = {'mesg': mesg, 'valido': False}
            return respuesta
        
        if (df['FinPlanificado'] < df['InicioProyecto']).any():
            mesg = "La fecha de 'Fin Planificado' no puede ser anterior a 'Inicio Proyecto'."
            respuesta = {'mesg': mesg, 'valido': False}
            return respuesta
        
        respuesta = entregar_mensaje_df_valido()
        return respuesta
        
    except Exception as e:
        print(f'Ha ocurrido un error: \n{e}')
        mesg = "Algunas fechas en 'create_date', 'Cierre', 'Inicio Proyecto' o 'Fin Planificado' son nulas o no son válidas."
        respuesta = {'mesg': mesg, 'valido': False}
        return respuesta
    
def validar_linea_negocio_tipos(df):
    """
    **Valida la línea de negocio y el tipo de todo el dataframe**\n
    **Parametros**\n
        df (Dataframe): Un objeto de tipo dataframe \n
    **Return**\n
        respuesta (dict): Diccionario con el boolean y mensaje
            formato: {'mesg':string,'valido':boolean}.
    """
    tipo_proy = Parametro.objects.get(nombre_parametro='proyectos.tipo').valor
    try:
        df['problema'] = df.apply(lambda row: validar_linea_tipo_df(row, tipo_proy), axis=1)
        columnas_a_buscar = ['id', 'proyecto']
        ids_problemas = df[df['problema'] == True][columnas_a_buscar]
        if(not ids_problemas.empty):
            mesg = 'Se han encontrado problemas en el tipo y línea de negocio en las siguientes filas: <br> <ul>'
            problemas_str = ' '.join([f"<li> ID: {row['id']}, Proyecto: {row['proyecto']} </li>" for _, row in ids_problemas.head(5).iterrows()])
            mesg = mesg + problemas_str + '</ul> Entre otros. Por favor, verifique los datos.'
            respuesta = {'mesg':mesg, 'valido':False}
            return respuesta    
        else:
            respuesta = entregar_mensaje_df_valido()
            return respuesta
    except Exception as e:
        mesg = 'Han ocurrido problemas con el procesamiento de los datos. Intentelo de nuevo más tarde'
        respuesta = {'mesg':mesg,'valido':False}
        return respuesta
    
def verificarDf(df):
    """
    **Verifica que el df esté funcionando correctamente**\n
    **Parametros**\n
        df (Dataframe): Un objeto de tipo dataframe \n
    **Return**\n
        respuesta (dict): Diccionario con el boolean y mensaje
            formato: {'mesg':string,'valido':boolean}.
    """
    if not isinstance(df, pd.DataFrame):
        mesg = "El archivo entregado no puede ser leido correctamente, intentelo de nuevo más tarde."
        respuesta =  {'mesg':mesg, 'valido':False}
        return respuesta
    
    validaciones = [
        validar_columnas_nulas_df,
        validar_numeros_negativos,
        validar_fechas_df,
        validar_linea_negocio_tipos,
        validar_agencia
    ]
    
    for validacion in validaciones:
        print(validacion)
        respuesta = validacion(df=df)
        if not respuesta.get('valido', True):
            return respuesta
        
    mesg = 'No se han encontrado datos que puedan provocar conflictos.'
    respuesta = {'mesg':mesg, 'valido':True}
    return respuesta