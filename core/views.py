from django.shortcuts import redirect, render, get_object_or_404, redirect
from .models import Ventas, Perfil_hh_Detalle_Semanal, Disponibilidad, Hh_Estimado_Detalle_Semanal
from .models import Graficos, historialCambios, proyectosAAgrupar, PerfilUsuario, Parametro, User 
from .models import Disponibilidad, Asignacion, AsignacionControl, HorasPredecidas 
from .models import proyectosSemanas, Empleado
from .forms import VentasForm, DispForm, UploadFileForm, LoginForm, CrearUsuarioAdmin
from .forms import proyectosForm, CategoriasForm , UsuarioForm, ProgramacionForm, EscenariosForm
from .forms import CATEGORIAS_MAPPING, PROGRAMACION_MAPPING, ESCENARIOS_MAPPING
import locale
from django.core.paginator import Paginator
import requests
from django.db.models import Sum
from django.contrib import messages
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.utils import timezone
# importacion de dashboard x4
import locale
from datetime import timedelta, datetime, date
from django.db.models import Count
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from .clusters_data import realizar_clusterizacion
import logging
from apscheduler.schedulers.background import BackgroundScheduler

from apscheduler.triggers.cron import CronTrigger
from django.db import DatabaseError, IntegrityError, OperationalError
import json
from django.core.mail import send_mail, BadHeaderError
# import plotly.express as px
# import plotly.graph_objects as go
# from django.contrib.auth import authenticate, login, logout
# from django.contrib.auth.models import User
from django.db.models import Sum, Q, Count
from django.db import transaction
from django.db.models import F
from decimal import Decimal
from django.core.paginator import Paginator
from io import BytesIO
from .apis import obtener_api_empleados, obtener_planning_slots, obtener_resource_calendar, enviar_datos_planning_slots
from .apis import obtener_api_recursos, convertir_fecha_a_chile, convertir_fecha_a_gmt, convertir_fecha_a_string
from .apis import obtener_empleados_con_horas, convertir_datos_asignacion, obtener_horas_recurso, cal_disponibilidad
from .apis import obtener_planning_slots_por_semana, obtener_departamento_empleado, cal_disponibilidad_varias_semanas
from .apis import cargar_empleados
#import collections defaultdict, itertools import islice para disponibilidad x2
from collections import defaultdict
from itertools import islice
from decimal import Decimal


# Create your views here.

def subirProyectos(request, upload='Sh'):
    if not request.user.is_authenticated:
        return redirect(iniciar_sesion)
    
    data = {'form':UploadFileForm()}
    showTable = False
    messages = []
    merror = []
    
    if(upload=="Can"):
        try:
            request.session.pop('df_proyectos')
        except:
            pass
        return redirect (subirProyectos)
        
    if(upload=="Up"):
        df = cambiarFormatoAlmacenarDb(request.session['df_proyectos'])
        cont = 0
        for _, row in df.iterrows():
            proyecto = proyectosAAgrupar(
                id=row['id'],
                proyecto=row['proyecto'],
                lineaNegocio=row['lineaNegocio'],
                tipo=row['tipo'],
                cliente=row['cliente'],
                createDate=row['createDate'],
                cierre=row['cierre'],
                egresosNoHHCLP=row['egresosNoHHCLP'],
                montoOfertaCLP=row['montoOfertaCLP'],
                usoAgencia=row['usoAgencia'],
                ocupacionInicio=row['ocupacionInicio'],
                fechaInicio = row['InicioProyecto'],
                fechaFin = row['FinPlanificado']
            )
            cont += 1
            proyecto.save()
        request.session.pop('df_proyectos')
        cat = {'Cat':'E','Sub':'1'}
        almacenado = almacenarHistorial(cat, request.user)
        clusterizacion = realizar_clusterizacion()
        return redirect(ver_proyectos)
    
    if request.method == 'POST' and 'file' in request.FILES:
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            if not file.name.endswith(('.csv', '.xlsx')):
                data['mesg'] = 'Archivo no compatible. Por favor, selecciona un archivo CSV o XLSX.'
            else:
                df = pd.read_excel(file) if file.name.endswith('.xlsx') else pd.read_csv(file)
                required_columns = ['id', 'Proyecto', 'Línea de Negocio', 'tipo', 'cliente', 'create_date', 
                                    'Cierre', 'Egresos No HH CLP', 'Monto Oferta CLP',
                                    'C/Agencia', 'Ocupación Al Iniciar (%)', 'Inicio Proyecto', 'Fin Planificado']
                if not all(col in df.columns for col in required_columns):
                    mesg = ('<div style="container col-md-6"> El archivo <strong>no contiene</strong> las columnas requeridas:'
                                    '<ul> <li>id</li> <li>Proyecto</li> <li>Línea de Negocio</li> <li>tipo</li>'
                                    '<li>cliente</li> <li>create_date</li> <li>Cierre</li> <li>Egresos No HH CLP</li>'
                                    '<li>Monto Oferta CLP</li> <li>C/Agencia</li> <li>Ocupación Al Iniciar (%)</li>' 
                                    '<li>Inicio Proyecto</li> <li>Fin Planificado</li> </ul>'
                                    '<br> Por favor, suba un archivo con estas columnas.</div>')
                    merror.append(mesg)
                    
                else:
                    extra_columns = [col for col in df.columns if col not in required_columns and col]
                    if extra_columns:
                        extra_columns_html = ''.join(f'<li>{col}</li>' for col in extra_columns if col)
                        mesg = ('<div style="container col-md-6"> El archivo <strong>contiene</strong> columnas innecesarias:'
                                    f'<ul><li>{extra_columns_html}</li> </ul> <br> Se necesitan unicamente las siguientes columnas'
                                    '<ul> <li>id</li> <li>Proyecto</li> <li>Línea de Negocio</li> <li>tipo</li>'
                                    '<li>cliente</li> <li>create_date</li> <li>Cierre</li> <li>Egresos No HH CLP</li>'
                                    '<li>Monto Oferta CLP</li> <li>C/Agencia</li> <li>Ocupación Al Iniciar (%)</li> </ul>'
                                    '<li>Inicio Proyecto</li> <li>Fin Planificado</li>'
                                    '<br> Por favor, suba un archivo solo con estas columnas.</div>')
                        merror.append(mesg)
                    else:
                        df = cambiarFormatoAlmacenarDf(df)
                        validado = verificarDf(df)
                        df_validado = validado['valido']
                        
                        datosDfDict = df.to_dict(orient='records')
                        data["proyectos"] = datosDfDict
                        data['validado'] = df_validado
                        showTable = True
                        
                        if(not df_validado):
                            merror.append(validado['mesg'])
                            showTable = True
                        else:
                            messages.append(validado['mesg'])
                            request.session['df_proyectos'] = datosDfDict
        else:
            data["mesg"] = "El valor es inválido"
    data["showTable"] = showTable
    data['messages'] = messages
    data['merror'] = merror
        
    return render(request, "core/subirProyectos.html", data)

def cambiarFormatoAlmacenarDf(df):
    df = df
    df['create_date'] = df['create_date'].astype(str)
    df['Cierre'] = df['Cierre'].astype(str)
    df['Inicio Proyecto'] = df['Inicio Proyecto'].astype(str)
    df['Fin Planificado'] = df['Fin Planificado'].astype(str)
    df.rename(columns={'Proyecto': 'proyecto'}, inplace=True)
    df.rename(columns={'Línea de Negocio': 'lineaNegocio'}, inplace=True)
    df.rename(columns={'create_date': 'createDate'}, inplace=True)
    df.rename(columns={'Cierre': 'cierre'}, inplace=True)
    df.rename(columns={'Egresos No HH CLP': 'egresosNoHHCLP'}, inplace=True)
    df.rename(columns={'Monto Oferta CLP': 'montoOfertaCLP'}, inplace=True)    
    df.rename(columns={'C/Agencia': 'usoAgencia'}, inplace=True)
    df.rename(columns={'Ocupación Al Iniciar (%)': 'ocupacionInicio'}, inplace=True)
    df.rename(columns={'Inicio Proyecto': 'InicioProyecto'}, inplace=True)
    df.rename(columns={'Fin Planificado': 'FinPlanificado'}, inplace=True)
    df['ocupacionInicio'] = df['ocupacionInicio'].round(2)
    df['ocupacionInicio'] = df['ocupacionInicio'] * 100
    return df

def cambiarFormatoAlmacenarDb(df):
    df = pd.DataFrame(df)
    df['createDate'] = pd.to_datetime(df['createDate'])
    df['cierre'] = pd.to_datetime(df['cierre'])
    df['InicioProyecto'] = pd.to_datetime(df['InicioProyecto'])
    df['FinPlanificado'] = pd.to_datetime(df['FinPlanificado'])
    df['cierre'] = df['cierre'].fillna(df['createDate'])
    df['cliente'] = df['cliente'].astype(int)
    df['usoAgencia'] = df['usoAgencia'].fillna(0)
    df['usoAgencia'] = df['usoAgencia'].replace({'Sí': 1, 'Si': 1, 'si': 1 , 'sí': 1, 'no': 0, 'No': 0}).astype(bool)
    df['egresosNoHHCLP'] = df['egresosNoHHCLP'].fillna(0)
    df['montoOfertaCLP'] = df['montoOfertaCLP'].astype(int)
    df['ocupacionInicio'] = df['ocupacionInicio'].astype(float) 
    return df

def verificarDf(df):
    """Verifica que los valores relevantes no sean nulos.
    
    Parametros de Entrada: 
    df (El dataframe a utilizar)
    
    Return: 
    Diccionario con mesg y valido.

        mesg(string) = Mensaje a mostrar en HTML.
    
        valido(boolean) = Si no contiene datos nulos es verdadero 
    """
    columns_to_check = ['id', 'proyecto', 'lineaNegocio', 'tipo', 'cliente', 'createDate', 'montoOfertaCLP', 'ocupacionInicio']
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
                        "'Monto Oferta CLP' y 'Ocupación Al Iniciar' (%) <br>"
                        '<strong>NO PUEDEN CONTENER DATOS NULOS O VACÍOS</strong></li>'
                        '<li>Las columnas deben tener exactamente <strong> el mismo nombre que se solicita</strong></li>'
                    '</ul>'
                    '</div>"></i>'
                    )
            respuesta = {'mesg':mesg,'valido':False}
    else:
        mesg = 'No se han encontrado datos que puedan provocar conflictos'
        respuesta = {'mesg':mesg, 'valido':True}
    return respuesta

def graficar_Datos(request):
    if not request.user.is_authenticated:
        return redirect(iniciar_sesion)
    
    graficos = Graficos.objects.all()
    data_list = list(graficos.values())
    additional_data = pd.DataFrame(data_list)
    
    bar_chart = go.Figure(data=[
        go.Bar(name='HH requerido', x=additional_data['semana'], y=additional_data['hhRequerido']),
        go.Bar(name='HH disponible', x=additional_data['semana'], y=additional_data['hhDisponible'])
    ])
    bar_chart = bar_chart.to_html(full_html=False)
    
    line_chart = px.line(additional_data, x='semana', y='utilizacion', title='Utilización (%)')
    line_chart = line_chart.to_html(full_html=False)
    
    data = {'bar':bar_chart, 'line':line_chart}
    
    sobreU = False
    subU = False
    for val in graficos:
        if(val.utilizacion > 100):
            sobreU = True
        elif(val.utilizacion < 80):
            subU = True
    if(sobreU and subU):
        data['mesg'] = 'Se estima subtilización bajo un 80% y sobreutilización mayor a 100%, por lo que se sugiere ajustar la disponibilidad de equipo de proyecto o modificar requerimientos de horas futuras.'
    elif (sobreU):
        data['mesg'] = 'Se estima sobreutilización sobre un 100%,  por lo que se sugiere ajustar la disponibilidad de equipo de proyecto o modificar requerimientos de horas futuras'
    elif (subU):
        data['mesg'] = 'Se estima subtilización bajo un 80%. por lo que se sugiere ajustar la disponibilidad de equipo de proyecto o modificar requerimientos de horas futuras'
    else:
        data['mesg'] = 'No se visualizaron momentos en que haya sobreutilización ni subtulización.'
    
    return render(request, 'core/dashboard.html', data)   

def development_Buttons(request):
    if not request.user.is_authenticated:
        return redirect(iniciar_sesion)
    
    forms = [VentasForm() for _ in range(5)]
    data = {"VentasForms":forms, "DispForm":DispForm}
    
    #Escribe Tu Código Acá
    #se carga el formulario
    data = {}
    data['form'] = UploadFileForm()  # Inicializa el formulario en GET
    data["datosDB"] = Ventas.objects.all()
    
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            if not file.name.endswith(('.csv', '.xlsx')):
                # Mostrar un mensaje de error
                return render(request, 'boton.html', {'form': form, 'error_message': 'Archivo no compatible. Por favor, selecciona un archivo CSV o XLSX.'})

            df = pd.read_excel(file) if file.name.endswith('.xlsx') else pd.read_csv(file)
            required_columns = ['idTipoProyecto', 'fecha']
            if not all(col in df.columns for col in required_columns):
                return render(request, 'core/boton.html', {'form': form, 'error_message': 'El archivo no contiene las columnas requeridas (idTipoProyecto, fecha). Por favor, sube un archivo con estas columnas.'})
            
           # Convertir el DataFrame a una lista de diccionarios
            datos_formularios = df.to_dict(orient='records')
            
            # Crear formularios VentasForm con datos iniciales
            forms = []
            for datos in datos_formularios:
                fecha=str(datos['fecha'])
                fecha = fecha[:10]
                
                initial_data = {
                    'idTipoProyecto': datos['idTipoProyecto'],
                    'fecha': fecha
                }
                form = VentasForm(initial=initial_data)
                forms.append(form)
            data['VentasForms'] = forms
            return render(request, 'core/boton.html', data)
            
            # forms = [VentasForm(initial=datos) for datos in datos_formularios]
            # data['VentasForms'] = forms
            # return render(request, 'core/boton.html', {'VentasForms': forms})
            
            # Aquí puedes procesar el archivo según tus necesidades
            # Por ejemplo, guardarlo en la base de datos o procesarlo de alguna manera
            # return HttpResponse('Archivo subido correctamente.') 
        else:
            data["mesg"] = "El formulario en inválido"
            return render(request, 'core/boton.html', data)
    else:
        form = UploadFileForm()
        data["form"] = form
    return render(request, 'core/boton.html', data)

def llenar_DB(request):
    # Hh_Estimado_Detalle_Semanal.objects.all().delete()
    # Perfil_hh_Detalle_Semanal.objects.all().delete()
    # historialCambios.objects.all().delete()
    # proyectosAAgrupar.objects.all().delete()
    # User.objects.all().delete()
    
    # usuario = get_object_or_404(User, id=15)
    # usuario.set_password('Admin@123')
    # usuario.save()
    
    usuario = get_object_or_404(User, id=33)
    usuario.set_password('Contra12$%')
    usuario.save()

    
    # proyecto1 = proyectosAAgrupar.objects.update_or_create(
    #         id = 446,
    #         proyecto = 'PRY2023-106',
    #         lineaNegocio = 'SGE',
    #         tipo = 'Reportabilidad y Plataforma',
    #         cliente = 6057,
    #         pm = 'katherina@rodaenergia.cl', 
    #         createDate = datetime.strptime('2023-05-10 21:20:14', "%Y-%m-%d %H:%M:%S"),
    #         cierre = datetime.strptime('2023-05-10', "%Y-%m-%d").date(),
    #         primeraTarea = datetime.strptime('2023-05-04', "%Y-%m-%d").date(),
    #         ultimaTarea = datetime.strptime('2023-05-10', "%Y-%m-%d").date(),
    #         egresosNoHHCLP = 0,
    #         montoOfertaCLP = 1530218,
    #         usoAgencia = False,
    #         desfaseDias = 0,
    #         ocupacionInicio = 69.0
    # )
    
    #Usuario de testing
    # usuario = User.objects.create_user(username="admin", password='Admin@123')
    # usuario.first_name = "Pedro"
    # usuario.last_name = "Martinez"
    # usuario.email = "admin@admin.com"
    # usuario.is_superuser = True
    # usuario.is_staff = True
    # usuario.save()
    
    # perfil = PerfilUsuario.objects.update_or_create(user=usuario, cargo='Administrador')
    
    # #Crear un usuario inactivo y modificar el login para no dejarlo loguearse
    # usuarioAnon = User.objects.create_user(username="Anon", password='anon') #ZKfg!)nkLSp163SD
    # usuarioAnon.first_name = "Anonimo"
    # usuarioAnon.last_name = "anon"
    # usuarioAnon.email = "none"
    # usuarioAnon.is_superuser = False
    # usuarioAnon.is_staff = False
    # usuarioAnon.is_active = False
    # usuarioAnon.save()
    
    # Perfil_hh_Detalle_Semanal.objects.update_or_create(
    #     idTipoProyecto = '1', 
    #     numSemana = '1', 
    #     hh = 1.8
    #     )
    # Perfil_hh_Detalle_Semanal.objects.update_or_create(
    #     idTipoProyecto = '1', 
    #     numSemana = '2', 
    #     hh = 2.1
    #     )
    # Perfil_hh_Detalle_Semanal.objects.update_or_create(
    #     idTipoProyecto = '1', 
    #     numSemana = '3', 
    #     hh = 1.9
    #     )
    # Perfil_hh_Detalle_Semanal.objects.update_or_create(
    #     idTipoProyecto = '1', 
    #     numSemana = '4', 
    #     hh = 1.5
    #     )
    # Perfil_hh_Detalle_Semanal.objects.update_or_create(
    #     idTipoProyecto = '2', 
    #     numSemana = '1', 
    #     hh = 1.5
    #     )
    # Perfil_hh_Detalle_Semanal.objects.update_or_create(
    #     idTipoProyecto = '2', 
    #     numSemana = '2', 
    #     hh = 3
    #     )
    return redirect(pagina_principal)

#Casi Funcional
def newCreateJoinDB():
    # Obtener todas las ventas
    ventas = Ventas.objects.all()

    for venta in ventas:
        # Buscar el correspondiente Perfil_hh_Detalle_Semanal por idTipoProyecto
        perfiles_hh = Perfil_hh_Detalle_Semanal.objects.filter(idTipoProyecto=venta.idTipoProyecto)
        fechaInicial = venta.fecha
        semanaInicial = fechaInicial.isocalendar()[1]
        print(str(venta.id) + ": \n")
        if perfiles_hh:
            for i, perfil in enumerate(perfiles_hh):
                fecha = venta.fecha + timedelta(days=(i*7))
                semanaPredecir = fecha.isocalendar()[1]
                semanaProyecto = (semanaPredecir - semanaInicial) + 1
                perfil_HH = Perfil_hh_Detalle_Semanal.objects.filter(idTipoProyecto=venta.idTipoProyecto, numSemana=semanaProyecto)
                horasHombre = perfil_HH[0].hh
                anio = fecha.year
                
                # print("Fecha: " + str(fecha) + " - ID perfilHH: " + str(perfil_HH[0].id) + " - Ventas: " + str(venta.id) + 
                #       " - Año: " + str(anio) + " - Semana del Año: " +  str(semanaPredecir) + " - Horas: " + str(horasHombre) +
                #       "  - Semana Proyecto: " + str(semanaProyecto))
                
                hhDetalleSemana = Hh_Estimado_Detalle_Semanal(fecha=fecha, anio=anio, semana=semanaPredecir, idVentas=venta, 
                                                             idPerfilHhDetalleSemanal=perfil_HH[0], hh=horasHombre)
                checkData = Hh_Estimado_Detalle_Semanal.objects.filter(semana=semanaPredecir, idVentas=venta, anio=anio)
                checkData = list(checkData.values())
                checkData = len(checkData)
                    
                if(checkData == 0):
                    print("Datos Guardados")
                    hhDetalleSemana.save()
                else:
                    print("Datos NO guardados")
                    continue
    return True

def create_additional_table():
    Graficos.objects.all().delete()
    data = Hh_Estimado_Detalle_Semanal.objects.all()
    data_list = list(data.values())
    df = pd.DataFrame(data_list)
    
    disp = Disponibilidad.objects.all()
    dispList = list(disp.values())
    dfDisp = pd.DataFrame(dispList)
    dfDisp.rename(columns={'hh': 'hh_disp'}, inplace=True)
    
    weekly_data = df.groupby('semana')['hh'].sum().reset_index()
    weekly_data.rename(columns={'hh': 'hh_req'}, inplace=True)
    weekly_data = pd.merge(dfDisp, weekly_data, on='semana', how='outer')
    weekly_data['utilizacion'] = round((weekly_data['hh_req'] / weekly_data['hh_disp']) * 100, 1)
    weekly_data = weekly_data.dropna()
    
    for idx, row in weekly_data.iterrows():
        grafico = Graficos(
            semana=row['semana'],
            hhDisponible=row['hh_disp'],
            hhRequerido=row['hh_req'],
            utilizacion=row['utilizacion']
        )
        grafico.save()
    
    return True

def iniciar_sesion(request):
    if request.user.is_authenticated:
        return redirect(pagina_principal)
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                cat = {'Cat':'A', 'Sub':'1'}
                almacenado = almacenarHistorial(cat, user)
                return redirect(pagina_principal)
            else:
                data = {'mesg':'Usuario o contraseña incorrectos', 'form':LoginForm}
                #form.add_error(None, 'Usuario o contraseña incorrectos')
    else:
         data = {'form': LoginForm}
    return render(request, 'core/login.html', data)

#Crear un cerrar sesión
def cerrar_sesion(request):
    if request.user.is_anonymous:
        user = None
    else:
        user = request.user
    cat = {'Cat':'A','Sub':'2'}
    almacenado = almacenarHistorial(cat, user)
    logout(request)
    return redirect(iniciar_sesion) 

#Carga la página principal con todos los datos necesarios
def pagina_principal(request):
    if not request.user.is_authenticated:
        return redirect(iniciar_sesion)
    data = {}
    subcategorias_incl = [
            "Cambio de parametros",  # B1
            "Cambio de configuraciones en la base de datos", # B2
            "Limpieza de datos",     # C1
            "Agregó Proyectos",      # E1
            "Agregó usuario",        # E2
            "Desactivo usuario",     # E3
            "Activo usuario",        # E4
            "Cambio un cargo",       # F1
            "Actualizó permisos"     # F2
            ]
    historial = historialCambios.objects.all().filter(subcategoria__in=subcategorias_incl).values('idHist','fecha', 'categoria', 'subcategoria', 'prioridad', 'usuario__first_name','usuario__last_name').order_by('-fecha')[:5]
    data['hist'] = historial

    proyectos = proyectosAAgrupar.objects.all().order_by('-id')[:5]
    data['proyectos'] = proyectos
    list = []
    for i in range(5):
        list.append(i)
    data['peng'] = list
    # graficos = Graficos.objects.all()
    # data_list = list(graficos.values())
    # additional_data = pd.DataFrame(data_list)
    
    # bar_chart = go.Figure(data=[
    #     go.Bar(name='HH requerido', x=additional_data['semana'], y=additional_data['hhRequerido']),
    #     go.Bar(name='HH disponible', x=additional_data['semana'], y=additional_data['hhDisponible'])
    # ])
    # bar_chart = bar_chart.to_html(full_html=False)
    
    # line_chart = px.line(additional_data, x='semana', y='utilizacion', title='Utilización (%)')
    # line_chart = line_chart.to_html(full_html=False)
    
    # data = {'bar':bar_chart, 'line':line_chart}
    
    #cargar_empleados()

    #Cargar Dashboard
    proyectos = proyectosSemanas.objects.select_related('proyecto', 'horas').all()
    subir_empleados_db()

    total_proyectos = proyectos.count()
    
    try:
        locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')  # Unix / Linux / MacOS
    except locale.Error:
        locale.setlocale(locale.LC_TIME, 'Spanish_Spain.1252')  # Windows
    
    today = date.today()
    current_month = today.strftime('%B') #Deberia ser Octubre o 'October'.
    current_week = today.strftime('%U')

    # Calcular semanas restantes en el año
    weeks_in_year = 52
    remaining_weeks = weeks_in_year - int(current_week)

    empleados_count = proyectos.values('horas__rol').annotate(count=Count('horas__rol'))

    jefes = proyectosSemanas.objects.filter(horas__rol='Jefe de Proyectos').count()
    ingenieros = proyectosSemanas.objects.filter(horas__rol='Ingeniero de Proyecto').count()

    data['total_proyectos'] = total_proyectos
    data['current_month'] = current_month
    data['current_week'] = current_week
    data['remaining_weeks'] = remaining_weeks
    data['ingenieros'] = ingenieros
    data['jefes'] = jefes

    return render(request, 'core/index1.html', data)

#Almacena el historial solicitando desc, tipoInfo y usuario
def almacenarHistorial(categoria={'Cat':"A",'Sub':'1'}, usuario=None):
    """**Almacena el historial.**

        **Parametros:**\n 
        categoria: Diccionario con la categoria y la subcategoría. Debe venir con clave Cat para categoria, y Sub para la subcategoria.\n
        usuario: Usuario para almacenar e indicar quien realizar la acción. En caso de venir nulo es un usuario anónimo
        
        **Return:**\n
        histCambios: Objeto de tipo HistorialCambios.
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

def verificar_usuario_hist(user):
    if(user is None):
        usuario = User.objects.get(username="Anon")
    else:
        usuario = user
    return usuario

def obtener_subcategorias():
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
    
#Carga todos los distintos proyectos
def ver_proyectos(request):
    if not request.user.is_authenticated:
        return redirect(iniciar_sesion)
    
    proyectos = proyectosAAgrupar.objects.all()
    data = {'proyectos':proyectos}
    return render(request, 'core/verProyectos.html', data)

#Unicamente carga el historial o log de usuarios
def verHistorial(request):
    if not request.user.is_authenticated:
        return redirect(iniciar_sesion)
    
    historial = historialCambios.objects.all().values('idHist','fecha', 'categoria', 'subcategoria', 'prioridad', 'usuario__first_name','usuario__last_name')
    data = {'hist':historial}
    return render(request, 'core/historialAcciones.html', data)

#Unicamente carga los usuarios
def ver_usuarios(request):
    if not request.user.is_authenticated:
        return redirect(iniciar_sesion)
    
    usuarios = PerfilUsuario.objects.all().values('cargo',
                                                  'user__username','user__first_name','user__last_name',
                                                  'user__email','user__is_staff', 'user__is_active', 'user')

    cargos_dict = dict(UsuarioForm.CARGOS)
    for usuario in usuarios:
        usuario['cargo'] = cargos_dict.get(usuario['cargo'], usuario['cargo'])
    
    PerfilUsuario.objects.filter()
    data = {'usuarios':usuarios}
    return render (request, 'core/verUsuarios.html', data)

def crear_usuarios(request):
    if not request.user.is_authenticated:
        return redirect(iniciar_sesion)
    
    data = {"form":CrearUsuarioAdmin}
    if request.method == 'POST':
        form = CrearUsuarioAdmin(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                cargo = form.cleaned_data.get('cargo')
                user.save()
                PerfUsr = PerfilUsuario.objects.update_or_create(user=user, cargo=cargo)
                ##Se obtienen los datos del usuario creado
                cat = {'Cat':'E', 'Sub':'2'}
                almacenado = almacenarHistorial(cat, request.user)
                messages=["Usuario creado con éxito"]
                data["messages"]=messages
                data['form'] = CrearUsuarioAdmin()
            except Exception as e:
                merror=[f'Error guardando usuario. Intente de nuevo más tarde.']
                print(e)
        else:
            # Storing form errors
            error_messages = form.errors.as_data()  # Returns a dict with field names as keys and errors as values
            merror=[]
            for field, errors in error_messages.items():
                field_label=form.FIELD_LABELS.get(field, field)
                for error in errors:
                    errormsg = str(error.message)
                    #messages.error(request, f'Error in {field}: {error}')
                    merror.append(f'Error en {field_label}: {errormsg}.')
            data["merror"]=merror
    else:
        data['form'] = CrearUsuarioAdmin()

    return render(request, 'core/crearUsuarios.html', data)

#Funcion para editar un usuario / Junily was here
def editar_usuario(request, id):
    if not request.user.is_authenticated:
        return redirect(iniciar_sesion)

    usuario = get_object_or_404(User, id=id)
    
    pusuario = get_object_or_404(PerfilUsuario, user=usuario)
    merror = []
    
    if request.method == 'POST':
        form = UsuarioForm(request.POST, instance=usuario, perfil_usuario=pusuario)
        
        if form.is_valid():
            pusuario.cargo = form.cleaned_data['cargo']
            change_pass = False
            password = form.cleaned_data['password']
            new_password = form.cleaned_data['new_password']
            new_password2 = form.cleaned_data['new_password2']
            #print(form.cleaned_data['password'])
            
            if(password):
                print('Se ha cambiado la contra')
                change_pass = True 
                if(not authenticate(username=usuario.username, password=password)):
                    form.add_error('password', 'La contraseña ingresada no es correcta.')
                    merror.append('La contraseña ingresada en el campo Contraseña debe ser la contraseña actual de usuario.')
                    
                if password == new_password:
                    form.add_error('password', 'La contraseña nueva no debe ser igual a la anterior')
                    merror.append('La contraseña nueva no debe ser igual a la anterior')

                if new_password != new_password2:
                    form.add_error('new_password', 'Las contraseñas no coinciden')
                    merror.append('Las contraseñas no coinciden')

            if(usuario.is_active):
                usuario.is_active = True
                user = request.user
                cat = {'Cat':'E','Sub':'4'}
                almacenado = almacenarHistorial(cat, user)
                
            if(not merror):
                userToSave = get_object_or_404(User, id=id)
                if(change_pass):
                    userToSave.set_password(new_password)
                
                userToSave.first_name = usuario.first_name
                userToSave.last_name = usuario.last_name
                userToSave.email = usuario.email
                userToSave.is_active = usuario.is_active
                userToSave.is_staff = usuario.is_staff
                
                userToSave.save()
                pusuario.save()
                messages.success(request, 'Usuario actualizado correctamente')
                return redirect('verUsuarios')  # Redirige de vuelta a la lista de usuarios
        else:
            error_messages = form.errors.as_data()
            merror = []
            for field, errors in error_messages.items():
                field_label=form.FIELD_LABELS.get(field, field)
                for field, errors in error_messages.items():
                    for error in errors:
                        errormsg = str(error.message)
                        merror.append(f'Error en {field_label}: {errormsg}')
                return render(request, 'core/editarUsuario.html', {'form': form, 'merror': merror})

            data["merror"]=merror
    else:
        form = UsuarioForm(instance=usuario, perfil_usuario=pusuario)
        
    data =  {
        'form': form,
        'usuario_editado': usuario,
        'merror' : merror
    }
    return render(request, 'core/editarUsuario.html', data)

#Fin de la funcion para editar un usuario


#Desactiva el usuario, validando si existe y si es superuser o no.
def eliminarUsuarios(request, id):
    if(not request.user.is_staff):
        return redirect(ver_usuarios)
    
    messages = []
    merror = []
    #Se desactiva el usuario
    try:
        usuario = User.objects.get(id=id)
        nombre = usuario.first_name
        apellido = usuario.last_name
        if(usuario.is_staff):
            mesg = f'El usuario {nombre} {apellido} es administrador, no puede ser desactivado.'
            merror.append(mesg)
        else:
            if(usuario.is_active):
                usuario.is_active = False
                usuario.save()
                mesg = f'Se ha desactivado al usuario <strong>{nombre} {apellido}</strong>. Verifique el usuario en la siguiente lista.'
                messages.append(mesg)
                cat = {'Cat':'E','Sub':'3'}
                almacenado = almacenarHistorial(cat, request.user)
            else:
                mesg = f'El usuario <strong>{nombre} {apellido}</strong> ya está desactivado. Verifique el usuario en la siguiente lista.'
                messages.append(mesg)


    except Exception as e:
        print(e)
        mesg = 'Ha ocurrido un error. Por favor verifique nuevamente más tarde.'
        merror.append(mesg)
    
    #Se cargan los datos ya cambiados
    usuarios = PerfilUsuario.objects.all().values('cargo',
                                                  'user__username','user__first_name','user__last_name',
                                                  'user__email','user__is_staff', 'user__is_active', 'user')
    cargos_dict = dict(UsuarioForm.CARGOS)
    for usuario in usuarios:
        usuario['cargo'] = cargos_dict.get(usuario['cargo'], usuario['cargo'])
    data = {'messages':messages, 'usuarios':usuarios, 'merror':merror}
    return render (request, 'core/verUsuarios.html', data)

def ajuste_parametros(request):
    if not request.user.is_authenticated:
        return redirect(iniciar_sesion)
    
    messages = []
    merror = []
    data = {}
    
    if request.method == 'POST':
        form_categorias = CategoriasForm(request.POST, prefix='categorias')
        form_programacion = ProgramacionForm(request.POST, prefix='programacion')
        form_escenarios = EscenariosForm(request.POST, prefix='escenarios')

        if form_categorias.is_valid() and form_programacion.is_valid() and form_escenarios.is_valid():
            try:
                to_keep_categorias = obtener_campos_secundarios(form=form_categorias, tipo='Cat')
                to_keep_programacion = obtener_campos_secundarios(form=form_programacion, tipo='Cron')
                to_keep_escenarios = obtener_campos_secundarios(form=form_escenarios, tipo='Esce')

                hora = int(form_programacion.cleaned_data['hora'])
                minutos = int(form_programacion.cleaned_data['minutos'])
                dias = form_programacion.cleaned_data.get('dia', [])

                to_keep_programacion.append({'hora': hora, 'minutos': minutos, 'dias': dias})###
                tiempo = {'hora':hora, 'minutos':minutos, 'dias': dias}
                print(tiempo)
                
                ##Guarda los valores del historial
                valor_parametro = {
                    'valores_a_mantener': to_keep_categorias,
                    'valores_programacion': to_keep_programacion,
                    'tiempo':tiempo
                }
                parametro, created = Parametro.objects.update_or_create(
                    nombre_parametro='historial.mantener',
                    defaults={'valor': valor_parametro},
                )
                ##Guarda los valores del escenario
                valores_escenario = {
                    'valores_escenarios': to_keep_escenarios
                }
                parametro, created = Parametro.objects.update_or_create(
                    nombre_parametro='asignacion.tipo',
                    defaults={'valor':valores_escenario}
                )
                    
                cambiar_scheduler(hora=hora, minutos=minutos, id='borrar_historial')
                
                user = request.user
                cat = {'Cat':'B','Sub':'1'}
                almacenado = almacenarHistorial(cat, user)
                
                mesg = 'Se ha guardado correctamente'
                messages.append(mesg)
                

            except Exception as e:
                mesg = 'Ha ocurrido un error. Por favor, inténtelo de nuevo más tarde.'
                merror.append(mesg)
                print('Error al procesar el formulario: ' + str(e))
        else:
            if form_categorias.errors:
                print("Errores en form_categorias:", form_categorias.errors)
            if form_programacion.errors:
                print("Errores en form_programacion:", form_programacion.errors)
            if form_escenarios.errors:
                print("Errores en form_programacion:", form_escenarios.errors)
            mesg = 'Ha ocurrido un error. Por favor, verifique los campos correctamente o intentelo de nuevo más tarde.'
            merror.append(mesg)
            
    form_categorias = obtener_valores_formulario_parametro(CategoriasForm(prefix='categorias'))
    form_programacion = obtener_valores_formulario_parametro_programacion(ProgramacionForm(prefix='programacion'))
    form_escenarios = obtener_valores_formulario_parametro_escenarios(EscenariosForm(prefix='escenarios'))

    data['form_categorias'] = form_categorias
    data['form_programacion'] = form_programacion
    data['form_escenarios'] = form_escenarios
    data['messages'] = messages
    data['merror'] = merror
        
    return render(request, 'core/parameters.html',data)

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
    

def obtener_campos_secundarios(form,tipo):
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

#################
def obtener_valores_formulario_parametro_programacion(form):
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
    programaciones_principales  = set(key for key in PROGRAMACION_MAPPING.keys() if len(key) == 1)
    for programacion  in programaciones_principales :
        sub_programaciones   = [sub_key for sub_key in PROGRAMACION_MAPPING.keys() if sub_key.startswith(programacion) and len(sub_key) > 1]
        
        if all(initial_data[PROGRAMACION_MAPPING[sub_key]] for sub_key in sub_programaciones):
            initial_data[PROGRAMACION_MAPPING[programacion]] = True
    return initial_data
#################

def obtener_valores_formulario_parametro_escenarios(form):
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
    escenarios_principales  = set(key for key in ESCENARIOS_MAPPING.keys() if len(key) == 1)
    for escenarios  in escenarios_principales :
        sub_escenarios   = [sub_key for sub_key in ESCENARIOS_MAPPING.keys() if sub_key.startswith(escenarios) and len(sub_key) > 1]
        
        if all(initial_data[ESCENARIOS_MAPPING[sub_key]] for sub_key in sub_escenarios):
            initial_data[ESCENARIOS_MAPPING[escenarios]] = True
    return initial_data

#################

def eliminar_historial(request):
    if not request.user.is_authenticated:
        return redirect(iniciar_sesion)
    
    if request.method == 'POST':
        # Obtener el parámetro con la clave "mantener.historial"
        parametro = Parametro.objects.filter(nombre_parametro='historial.mantener').first()

        if parametro:
            valores_a_mantener = parametro.valor.get('valores_a_mantener', [])
            subcategorias = obtener_subcategorias()
            nombres_subs = []
            
            for idx, val in enumerate(valores_a_mantener):
                nombres_subs.append(subcategorias.get(val, "Subcategoría desconocida"))
                
            if valores_a_mantener:
                # Eliminar registros que no estén en la lista de valores a mantener
                count, _ = historialCambios.objects.exclude(subcategoria__in=nombres_subs).delete()
                messages.success(request, 'Datos eliminados exitosamente.')
                user = request.user
                cat = {'Cat':'C','Sub':'1'}
                almacenado = almacenarHistorial(cat, user)
            else:
                messages.info(request, 'La lista de valores a mantener está vacía. No se eliminaron datos.')
            
            return redirect(verHistorial)
        else:
            messages.error(request, 'Parámetro no encontrado.')
            return redirect(verHistorial)
    
    messages.error(request, 'Método no permitido.')
    return redirect(verHistorial)

def consul_api(request):
    if not request.user.is_authenticated:
        return redirect(iniciar_sesion)

    if request.method == 'POST':
        if 'action' in request.POST and request.POST['action'] == 'add':
            url = 'https://66d8e1384ad2f6b8ed52e306.mockapi.io/Api/Odoo/crm_lead'
            
            try:
                response = requests.get(url)
                response.raise_for_status()
                datos = response.json()
                if isinstance(datos, list):
                    for item in datos:
                        proyectosAAgrupar.objects.update_or_create(
                            id=item.get('id'),
                            defaults={
                                'proyecto': item.get('name'),
                                'lineaNegocio': item.get('business_unit'),
                                'tipo': item.get('business_type'),
                                'cliente': item.get('customer'),
                                'createDate': item.get('create_date'),
                                'cierre': None,
                                'egresosNoHHCLP': 0,
                                'montoOfertaCLP': item.get('amount'),
                                'usoAgencia': item.get('wa'),
                                'ocupacionInicio': 0,
                                'disponibilidad': 0,
                                'utilizacion': 0
                            }
                        )
                    user = request.user
                    cat = {'Cat':'E','Sub':'1'}
                    almacenado = almacenarHistorial(cat, user)
                    return redirect(ver_proyectos)
                else:
                    messages.error(request, 'Datos inesperados.')
                    return redirect(subirProyectos)
            
            except requests.RequestException as e:
                messages.error(request, 'No se pudieron obtener los datos.')
                return redirect(subirProyectos)
            except Exception as e:
                messages.error(request, 'No se pudieron guardar los datos en la base de datos.')
                return redirect(subirProyectos) 

    url = 'https://66d8e1384ad2f6b8ed52e306.mockapi.io/Api/Odoo/crm_lead'
    data = {'form':UploadFileForm}
    try:
        response = requests.get(url)
        response.raise_for_status()
        datos = response.json()
        
        #Forma 2
        url2 = 'https://66faed6a8583ac93b40a65bc.mockapi.io/api/crm_lead/search'
        response2 = requests.get(url2)
        response2.raise_for_status()
        datos2 = response2.json()
        datos2 = datos2[0]
        if(datos2['success']):
            print('Se pueden subir los datos')
            #print(f"Datos del Json: \n {datos2}")
        else:
            print('No se pueden subir los datos')
        
        if isinstance(datos, list):
            data['datos'] = datos
            data['showTableOdoo'] = True
            return render(request, "core/subirProyectos.html", data)
        else:
            data['error'] = 'Datos inesperados'
            return render(request, "core/subirProyectos.html", data)
    

    
    except requests.RequestException as e:
        print(f'error solicitud: {e}')
        data['error'] = 'No se pudieron obtener los datos'
        return render(request, "core/subirProyectos.html", data) 
    
def cluster(request):
    if not request.user.is_authenticated:
        return redirect(iniciar_sesion)
    
    proyectos = HorasPredecidas.objects.all()
    proyectos_data = {'proyectos':proyectos}
    proyectos = proyectosSemanas.objects.select_related('proyecto', 'horas').all()
    
    data = {'proyectos':proyectos}
    if(request.method == 'POST'):
        clusterizacion = realizar_clusterizacion()
        if(clusterizacion):
            data['mesg'] = 'Se ha realizado la clusterización'
            user = request.user
            cat = {'Cat':'G', 'Sub':'1'}
            almacenado = almacenarHistorial(cat, user)
        else:
            data['mesg'] = 'No se ha realizado la clusterización'
        
    return render(request, "core/cluster.html", data)


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
            # Eliminar registros que no estén en la lista de valores a mantener
            count, _ = historialCambios.objects.exclude(subcategoria__in=nombres_subs).delete()
            print(f'{count} registros eliminados exitosamente.')
        else:
            print('La lista de valores a mantener está vacía. No se eliminaron datos.')
    else:
        print('Parámetro no encontrado.')

def carga_Odoo(request):
    ###enviar_datos_planning_slot
    ###tabla asignacion
    ###obtienes la semana por convertir_datos_asignacion
    ###id_empleado, id_recurso, horas_asignadas, fecha_inicio, fecha_fin, nombre_proyecto-semana
    if not request.user.is_authenticated:
        return redirect(iniciar_sesion)
    
    # Obtiene todas las asignaciones y sus empleados
    asignaciones = Asignacion.objects.select_related('empleado').all()
    
    # Inicializa un diccionario para almacenar fechas por empleado
    fechas_por_empleado = {}

    # Agrupa las asignaciones por empleado
    for asignacion in asignaciones:
        empleado_id = asignacion.empleado.id
        semana = asignacion.semana
        anio = asignacion.anio
        
        # Calcula las fechas usando la función proporcionada
        fecha = convertir_datos_asignacion(semana, anio)
        fecha_inicio = fecha['semana_inicio']
        fecha_fin = fecha['semana_fin']
        anio = fecha['año']
        
        # Si el empleado no está en el diccionario, inicializa su entrada
        if empleado_id not in fechas_por_empleado:
            fechas_por_empleado[empleado_id] = {
                'empleado': asignacion.empleado,
                'asignaciones': []
            }
        
        # Añade la asignación con fechas calculadas a la lista del empleado
        fechas_por_empleado[empleado_id]['asignaciones'].append({
            'id_empleado': asignacion.empleado.id_empleado,
            'id_recurso': asignacion.empleado.id_recurso,
            'horas_asignadas': asignacion.horas_asignadas,
            'semana': asignacion.semana,
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'nombre_proyecto': f"{asignacion.proyecto} - {asignacion.semana}",
            'año': anio
        })

    # Convierte el diccionario en una lista para pasar a la plantilla
    fechas_totales = list(fechas_por_empleado.values())
    
    # Ordena la lista por año y semana
    fechas_totales.sort(key=lambda x: (x['asignaciones'][0]['año'], x['asignaciones'][0]['semana']))


    # Prepara los datos para la plantilla
    data = {
        'asignaciones': asignaciones,
        'fechas_totales': fechas_totales,
    }

    if request.method == 'POST':
        cont = 0
        for empleado_data in fechas_totales:
            for asignacion in empleado_data['asignaciones']:
                cont += 1
                id = asignacion['id_recurso']
                employee = asignacion['id_empleado']
                hours = asignacion['horas_asignadas']
                start = asignacion['fecha_inicio']
                end = asignacion['fecha_fin']
                name = asignacion['nombre_proyecto']

                respuesta = enviar_datos_planning_slots(id, employee, hours, start, end, name)
                if respuesta and respuesta['done']:
                    messages.error(request, "Datos enviados correctamente")
                else:
                    messages.error(request, "Error al enviar los datos")
                if(cont == 4):
                    break
            if(cont == 4):
                break
            
        return redirect(carga_Odoo)

    return render(request, "core/cargaOdoo.html", data)
    
##Funciones Grupo 2
##  Acá deben escribir las funciones exclusivas del grupo 2
##  Esto significa que NO deben escribir arriba, A MENOS que sea necesario (PARAMETROS)
##  De otra forma, solo escriben acá
##  Si, acá 
##  Espero se haya entendido, (No entendi)


# LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION 
# LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION 
# LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION 
# LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION # LOGICA DE ASIGNACION 

#ESTA FUNCIÓN TE GENERA LOS DATOS DE LAS TABLAS EN EXEL Y PDF

#Esta es la función que genera el exel de la tabla horas_por_recurso_data
def generar_excel_proyectos(request):
    # Obtener los datos de la tabla horas por recurso
    proyectos = Asignacion.objects.values(
        'empleado__nombre',  # Nombre del recurso
        'empleado__rol',     # Rol del recurso
        'semana',           # Semana
    ).annotate(
        total_horas_rol=Sum('horas_asignadas')  # Total de horas asignadas
    )

    # Crear un DataFrame a partir de los datos de los proyectos
    df = pd.DataFrame(list(proyectos))

    # Crear un nuevo DataFrame pivotado
    df_pivot = df.pivot_table(
        index=['empleado__nombre', 'empleado__rol'],  # Agrupar por nombre y rol del recurso
        columns='semana',                           # Semanas se convierten en columnas
        values='total_horas_rol',                   # Valores que se colocan en la tabla
        fill_value=0                                # Rellenar con 0 donde no hay horas asignadas
    ).reset_index()

    # Renombrar las columnas para incluir "Semana"
    df_pivot.columns.name = None  # Eliminar el nombre de la columna
    df_pivot.columns = [f'Semana {col}' if isinstance(col, int) else str(col) for col in df_pivot.columns]

    # Calcular el total de horas por recurso y añadirlo como una nueva fila por rol
    total_row = df_pivot.iloc[:, 2:].sum().to_frame().T  # Sumar las horas, omitiendo las dos primeras columnas (nombre y rol)
    total_row['empleado__nombre'] = 'Total'  # Asignar el nombre de la fila total
    total_row['empleado__rol'] = ''  # Dejar vacío el campo de rol en la fila total
    df_pivot = pd.concat([df_pivot, total_row], ignore_index=True)

    output = BytesIO()

    # Crear el archivo Excel
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_pivot.to_excel(writer, index=False, sheet_name='Horas por Recurso y Semana')

    # Posicionar el buffer al inicio para leer los datos
    output.seek(0)

    # Preparar la respuesta de Excel
    response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="reporte_horas_por_recurso.xlsx"'
    return response

#Función que genera el exel de la segunda tabla
def generar_excel_recursos(request):
    # Obtener los datos de asignaciones de la tabla actualizada
    asignaciones = Asignacion.objects.values(
        'proyecto__proyecto',  # Nombre del proyecto
        'semana',            # Semana
    ).annotate(
        total_horas_proyecto=Sum('horas_asignadas')  # Total de horas asignadas por proyecto
    )

    # Crear un DataFrame a partir de los datos de las asignaciones
    df = pd.DataFrame(list(asignaciones))

    # Crear un nuevo DataFrame pivotado
    df_pivot = df.pivot_table(
        index='proyecto__proyecto',  # Agrupar por nombre del proyecto
        columns='semana',          # Semanas se convierten en columnas
        values='total_horas_proyecto',  # Valores que se colocan en la tabla
        fill_value=0               # Rellenar con 0 donde no hay horas asignadas
    ).reset_index()

    # Renombrar las columnas para incluir "Semana"
    df_pivot.columns.name = None  # Eliminar el nombre de la columna
    df_pivot.columns = [f'Semana {col}' if isinstance(col, int) else str(col) for col in df_pivot.columns]

    # Calcular el total de horas por proyecto y añadirlo como una nueva fila
    total_row = df_pivot.iloc[:, 1:].sum().to_frame().T  # Sumar las horas, omitiendo la primera columna que es el proyecto
    total_row['proyecto__proyecto'] = 'Total'  # Asignar el nombre de la fila total
    df_pivot = pd.concat([df_pivot, total_row], ignore_index=True)

    output = BytesIO()

    # Crear el archivo Excel
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_pivot.to_excel(writer, index=False, sheet_name='Horas por Proyecto y Semana')

    # Posicionar el buffer al inicio para leer los datos
    output.seek(0)

    # Preparar la respuesta de Excel
    response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="reporte_horas_por_proyecto.xlsx"'
    return response
    
from io import BytesIO
from django.http import HttpResponse
import pandas as pd
from .models import Asignacion  # Asegúrate de que este sea el nombre correcto de tu modelo

#Esta es la función que genera el exel de la tabla asignaciones
def generar_excel_asignacion(request):
    # Obtener el formato seleccionado desde el request
    formato = request.GET.get('formato')

    # Obtener los datos de las asignaciones
    asignaciones = Asignacion.objects.all().values(
        'proyecto__proyecto',  # Accediendo al nombre del proyecto
        'empleado__nombre',   # Accediendo al nombre del recurso
        'empleado__rol',      # Accediendo al rol del recurso
        'semana',
        'año',
        'horas_asignadas'
    )

    # Generar Excel
    if formato == 'excel':
        # Crear un DataFrame a partir de los datos de las asignaciones
        df = pd.DataFrame(list(asignaciones))

        # Crear un nuevo DataFrame pivotado
        df_pivot = df.pivot_table(
            index=['proyecto__proyecto', 'empleado__nombre', 'empleado__rol'],  # Mantener estas columnas como índices
            columns=['semana'],  # Las semanas se convierten en columnas
            values='horas_asignadas',  # Valores que se colocan en la tabla
            fill_value=0  # Rellenar con 0 donde no hay horas asignadas
        ).reset_index()

        # Renombrar las columnas para mayor claridad
        df_pivot.columns.name = None  # Eliminar el nombre de la columna
        df_pivot.columns = [f'Semana {col}' if col not in ['proyecto__proyecto', 'empleado__nombre', 'empleado__rol'] else col for col in df_pivot.columns]

        # Calcular el total de horas por semana
        total_horas = df_pivot.loc[:, df_pivot.columns.str.startswith('Semana ')]
        total_horas_sum = total_horas.sum().to_frame().T  # Transponer para que sea una fila
        total_horas_sum['proyecto__proyecto'] = ''
        total_horas_sum['empleado__nombre'] = ''
        total_horas_sum['empleado__rol'] = 'Total Horas'  # Etiqueta para la fila de totales

        # Concatenar los datos pivotados con los totales
        df_final = pd.concat([df_pivot, total_horas_sum], ignore_index=True)

        output = BytesIO()

        # Crear el archivo Excel
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_final.to_excel(writer, index=False, sheet_name='Asignaciones')

        # Posicionar el buffer al inicio para leer los datos
        output.seek(0)

        # Preparar la respuesta de Excel
        response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="reporte_asignaciones.xlsx"'
        return response

    # Si no se selecciona un formato válido
    else:
        return HttpResponse('Formato no soportado', status=400)

#ESTA ES LA FUNCIÓN DE BUSQUEDA SI TIENE QUE MIDIFICAR ALGO PARA BUSCAR QUE SEA AQUI NO TOQUEN LO DEMAS
def busqueda_de_datos(queryset, search_value, search_fields):
    """
    Función que realiza la búsqueda de datos en los campos especificados.
    
    Args:
        queryset: El conjunto de datos que se va a filtrar.
        search_value: El valor de búsqueda que el usuario ha ingresado.
        search_fields: Una lista de campos donde se debe buscar el valor.

    Returns:
        Un queryset filtrado por el valor de búsqueda.
    """
    if search_value:
        query = Q()
        for field in search_fields:
            query |= Q(**{f"{field}__icontains": search_value})
        queryset = queryset.filter(query)
    
    return queryset

# PRIMERA TABLA
def horas_por_recurso_data(request):
    order_column = request.GET.get('order[0][column]', 0)
    order_dir = request.GET.get('order[0][dir]', 'asc')

    # Definición de las columnas para ordenar
    columns = ['empleado__nombre','empleado__rol', 'semana', 'total_horas_rol']
    order_field = columns[int(order_column)]

    # Búsqueda por valor
    search_value = request.GET.get('search[value]', '')

    # Agrupar por semana y rol requerido
    proyectos = Asignacion.objects.values(
        'empleado__nombre',
        'empleado__rol',
        'semana',
    ).annotate(
        total_horas_rol=Sum('horas_asignadas'),
        
    ).filter(
        Q(empleado__rol__icontains=search_value) |
        Q(semana__icontains=search_value)
    ).order_by(f'{order_field if order_dir == "asc" else "-" + order_field}')

    # Paginar los resultados
    paginator = Paginator(proyectos, request.GET.get('length', 10))
    page_number = int(request.GET.get('start', 0)) // paginator.per_page + 1
    page_obj = paginator.get_page(page_number)

    data = {
        'draw': int(request.GET.get('draw', 1)),
        'recordsTotal': paginator.count,
        'recordsFiltered': paginator.count,
        'data': list(page_obj)
    }

    return JsonResponse(data)


# Recursos agrupados por proyecto (SEGUNDA TABLA)
def horas_por_proyecto_data(request):
    order_column = request.GET.get('order[0][column]', 0)
    order_dir = request.GET.get('order[0][dir]', 'asc')

    # Definición de las columnas para ordenar
    columns = ['proyecto__proyecto', 'semana', 'total_horas_proyecto']
    order_field = columns[int(order_column)]

    search_value = request.GET.get('search[value]', '')

    # Agrupar por semana y nombre del proyecto
    asignaciones = Asignacion.objects.values(
        'proyecto__proyecto',
        'semana'
    ).annotate(
        total_horas_proyecto=Sum('horas_asignadas')
    ).filter(
        Q(proyecto__proyecto__icontains=search_value) |
        Q(semana__icontains=search_value)
    ).order_by(f'{order_field if order_dir == "asc" else "-" + order_field}')

    # Paginación de resultados
    paginator = Paginator(asignaciones, request.GET.get('length', 10))
    page_number = int(request.GET.get('start', 0)) // paginator.per_page + 1
    page_obj = paginator.get_page(page_number)

    data = {
        'draw': int(request.GET.get('draw', 1)),
        'recordsTotal': paginator.count,
        'recordsFiltered': paginator.count,
        'data': list(page_obj)
    }

    return JsonResponse(data)


# # Proyectos (PRIMERA TABLA)
# def proyectos_data(request):
#     # Definir el orden por defecto
#     order_column = request.GET.get('order[0][column]', 0)
#     order_dir = request.GET.get('order[0][dir]', 'asc')

#     columns = ['nombre', 'duracion_semanas', 'horas_demandadas', 'tipo_proyecto__prioridad', 'rol_requerido']
#     order_field = columns[int(order_column)]

#     search_value = request.GET.get('search[value]', '')

#     proyectos = Proyecto.objects.filter(
#         Q(nombre__icontains=search_value) |
#         Q(duracion_semanas__icontains=search_value) |
#         Q(horas_demandadas__icontains=search_value) |
#         Q(tipo_proyecto__prioridad__icontains=search_value) |
#         Q(rol_requerido__icontains=search_value)
#     ).values(
#         'nombre', 'duracion_semanas', 'horas_demandadas', 'tipo_proyecto__prioridad', 'rol_requerido'
#     ).order_by(f'{order_field if order_dir == "asc" else "-" + order_field}')

#     # Si se solicita un formato de salida (solo Excel)
#     if 'formato' in request.GET and request.GET.get('formato') == 'excel':
#         return generar_excel(request, proyectos)  # Pasar los datos de 'proyectos'

#     paginator = Paginator(proyectos, request.GET.get('length', 10))
#     page_number = request.GET.get('start', 1)
#     page_obj = paginator.get_page(int(page_number) // paginator.per_page + 1)

#     data = {
#         'draw': int(request.GET.get('draw', 1)),
#         'recordsTotal': paginator.count,
#         'recordsFiltered': paginator.count,
#         'data': list(page_obj)
#     }

#     return JsonResponse(data)


# # Recursos (SEGUNDA TABLA)
# def recursos_asignados_data(request):
#     # Definir el orden por defecto
#     order_column = request.GET.get('order[0][column]', 0)
#     order_dir = request.GET.get('order[0][dir]', 'asc')

#     columns = ['proyecto__nombre', 'semana', 'total_horas_semanales']
#     order_field = columns[int(order_column)]

#     search_value = request.GET.get('search[value]', '')

#     asignaciones = Asignacion.objects.values(
#         'proyecto__nombre',
#         'semana'
#     ).annotate(
#         total_horas_semanales=Sum('horas_asignadas')
#     ).filter(
#         Q(proyecto__nombre__icontains=search_value) |
#         Q(semana__icontains=search_value)
#     ).order_by(f'{order_field if order_dir == "asc" else "-" + order_field}')

#     # Si se solicita un formato de salida (solo Excel)
#     if 'formato' in request.GET and request.GET.get('formato') == 'excel':
#         return generar_excel(request, asignaciones)

#     paginator = Paginator(asignaciones, request.GET.get('length', 10))
#     page_number = int(request.GET.get('start', 0)) // paginator.per_page + 1
#     page_obj = paginator.get_page(page_number)

#     data = {
#         'draw': int(request.GET.get('draw', 1)),
#         'recordsTotal': paginator.count,
#         'recordsFiltered': paginator.count,
#         'data': list(page_obj)
#     }

#     return JsonResponse(data)

# (TERCERA TABLA)
# Vista para mostrar horas agrupadas por rol y semana
# Vista para mostrar horas agrupadas por rol y semana


# TERCERA TABLA
def asignaciones_data(request):
    order_column = request.GET.get('order[0][column]', 0)
    order_dir = request.GET.get('order[0][dir]', 'asc')

    # Definir las columnas para ordenar
    columns = ['empleado__rol', 'semana', 'total_horas']
    order_field = columns[int(order_column)]

    # Obtener el valor de búsqueda del DataTable
    search_value = request.GET.get('search[value]', '')

    # Agrupar las horas asignadas por rol y semana
    asignaciones_agrupadas = Asignacion.objects.values(
        'empleado__rol',  # Agrupar por rol
        'semana'         # Agrupar por semana
    ).annotate(
        total_horas=Sum('horas_asignadas')  # Sumar todas las horas asignadas en cada semana para el rol
    ).filter(
        Q(empleado__rol__icontains=search_value) |
        Q(semana__icontains=search_value)
    ).order_by(f'{order_field if order_dir == "asc" else "-" + order_field}')

    # Paginación de los resultados
    paginator = Paginator(asignaciones_agrupadas, request.GET.get('length', 10))
    page_number = int(request.GET.get('start', 0)) // paginator.per_page + 1
    page_obj = paginator.get_page(page_number)

    # Preparar el resultado para DataTables
    data = {
        'draw': int(request.GET.get('draw', 1)),
        'recordsTotal': paginator.count,
        'recordsFiltered': paginator.count,
        'data': list(page_obj)
    }

    return JsonResponse(data)

def asignaciones_list(request):
    """
    Vista que muestra la lista de asignaciones en una tabla paginada.
    """

    # Obtener todas las asignaciones
    asignaciones = Asignacion.objects.all().order_by('semana')

    # Configurar el paginador para mostrar 10 asignaciones por página
    paginator = Paginator(asignaciones, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Calcular el rango de páginas para mostrar en la interfaz
    num_pages = paginator.num_pages
    current_page = page_obj.number
    start_page = max(current_page - 5, 1)
    end_page = min(current_page + 5, num_pages)

    # Crear una lista de páginas visibles
    page_range = list(range(start_page, end_page + 1))

    # Renderizar el template con las asignaciones paginadas
    return render(request, 'core/asignaciones_list.html', {
        'asignaciones': page_obj,
        'num_pages': num_pages,
        'current_page': current_page,
        'page_range': page_range,
    })



# Configuración de logging
logger = logging.getLogger(__name__)

def ejecutar_asignacion(request):
    if request.method == 'POST':
        try:
            control, created = AsignacionControl.objects.get_or_create(id=1)  # Usa un único registro para controlar
            mensaje = ""

            if not created:
                # Si ya existe un registro, verifica si se realizó una ejecución hoy
                if control.fecha_ultimo_ejecucion == datetime.today():
                    logger.warning("Intento de ejecutar la asignación más de una vez en el mismo día.")
                    return HttpResponse("La asignación ya ha sido ejecutada hoy.", status=400)

            # Ejecutar la asignación de recursos y capturar el mensaje de retorno
            
            mensaje_asignacion = asignar_recursos()
            
            # Si la asignación fue exitosa o parcial, actualiza el registro de control
            if "éxito" in mensaje_asignacion or "ya existen" in mensaje_asignacion:
                control.ejecuciones_exitosas += 1
                control.fecha_ultimo_ejecucion = datetime.today()
                control.save()
                user = request.user
                cat = {'Cat':'G', 'Sub':'2'}
                almacenado = almacenarHistorial(cat, user)
            mensaje = mensaje_asignacion

        except IntegrityError as e:
            # Manejar errores de integridad (claves duplicadas, etc.)
            control.ejecuciones_fallidas += 1
            control.save()
            logger.error(f"Error de integridad en la asignación: {e}")
            mensaje = f"Error de integridad: {str(e)}"
            return HttpResponse(mensaje, status=500)

        except OperationalError as e:
            # Manejar errores operacionales, como problemas de conexión a la base de datos
            control.ejecuciones_fallidas += 1
            control.save()
            logger.critical(f"Error operacional durante la asignación: {e}")
            mensaje = f"Error operacional: {str(e)}"
            return HttpResponse(mensaje, status=500)

        except DatabaseError as e:
            # Manejar cualquier otro error relacionado con la base de datos
            control.ejecuciones_fallidas += 1
            control.save()
            logger.error(f"Error de base de datos: {e}")
            mensaje = f"Error de base de datos: {str(e)}"
            return HttpResponse(mensaje, status=500)

        except Exception as e:
            # Manejar cualquier otra excepción inesperada
            control.ejecuciones_fallidas += 1
            control.save()
            logger.exception(f"Error inesperado en la asignación: {e}")
            mensaje = f"Error inesperado: {str(e)}"
            return HttpResponse(mensaje, status=500)

        # Asegúrate de devolver una respuesta con el mensaje adecuado
        return HttpResponse(mensaje, status=200)
    
    return HttpResponse(status=405)  # Método no permitido

def eliminar_asignaciones(request):
    """
    Vista para eliminar todas las asignaciones actuales.
    """
    if request.method == 'POST':
        # Eliminar todas las asignaciones
        Asignacion.objects.all().delete()

        # Redirigir o devolver una respuesta de éxito
        return redirect('asignaciones_list')  # Redirige a la página de asignaciones

    return HttpResponse(status=405)  # Devuelve un error si no es un POST


# def proyectos_a_asignar(request):
#     # Filtrar proyectos que necesitan asignación para mostrar
#     proyectos_necesitan_asignacion = proyectos.objects.filter(
#         ocupacionInicio__lt=80.00,  # Ocupación menor al 80%
#         disponibilidad__gt=0        # Debe tener disponibilidad
#     )

#     # Contexto para renderizar
#     context = {
#         'proyectos': proyectos_necesitan_asignacion,
#         'asignaciones': asignacion.objects.all()
#     }

#     return render(request, 'core/proyectos_a_asignar.html', context)

# def limpiar_asignaciones(request):
#     # Limpiar asignaciones previas
#     asignacion.objects.all().delete()
#     return redirect('proyectos_a_asignar')

# def limpiar_proyectos(request):
#     if request.method == 'POST':
#         proyectos.objects.all().delete()
#         messages.success(request, "Todos los proyectos han sido eliminados exitosamente.")
#         return redirect('asignar_recursos')
    
# def pruebas(request):
#     # Puedes incluir lógica aquí si es necesario
#     # Por ahora, esta vista simplemente renderiza la plantilla con el contexto recibido
#     return render(request, 'core/pruebas.html')

def asignar_recursos():
    """
    Algoritmo que asigna recursos semana a semana según la duración y la semana de inicio de cada proyecto.
    Utiliza APIs para obtener disponibilidad de recursos y horas semanales.
    """
    mensaje = ""
    asignacion_realizada = False  # Para verificar si se realizó alguna asignación

    # Iteramos sobre cada proyecto para asignar recursos según su duración
    proyectos = proyectosAAgrupar.objects.all().order_by('-fechaFin')
    hoy = date.today()
    try:
        parametro = Parametro.objects.get(nombre_parametro='asignacion.tipo')
        #print(parametro)
        tipo_horas = parametro.valor['valores_escenarios'][0]
    except Exception as e:
        tipo_horas = 'A2'
    
    for proyecto in proyectos:
        #Verifica que el proyecto no inicie in fin de semana.
        fecha_fin = proyecto.fechaFin
        print(fecha_fin)
        
        if(fecha_fin < hoy):
            break
            
        dia_semana = proyecto.fechaInicio.weekday()
        if(dia_semana >= 5):
            proyecto.fechaInicio += timedelta(days=2)
        
        # Obtener la semana de inicio y la duración del proyecto
        anio, semana_inicio, dia_semana = proyecto.fechaInicio.isocalendar()
        duracion_proyecto = (proyecto.fechaFin - proyecto.fechaInicio)
        semanas = duracion_proyecto.days // 7
        print(f"Procesando proyecto '{proyecto.proyecto}' con duración de {semanas} semanas, comenzando en la semana {semana_inicio}...")
        
        horas_predecidas = HorasPredecidas.objects.filter(linea_negocio = proyecto.lineaNegocio, tipo = proyecto.tipo)
        _, semana_final, dia_semana = proyecto.fechaFin.isocalendar()
        
        # Iteramos sobre las semanas que abarca el proyecto
        for i in range(semanas):
            #BLOQUE IF PARA CALCULAR EL % DE SEMANA Y ROL
            # Calcular la semana de asignación considerando el ciclo de 52 semanas
            semana_asignacion = (semana_inicio + i - 1) % 52 + 1  # Reiniciar el conteo al llegar a la semana 53
            if(semana_asignacion == 1):
                anio += 1
            #print(f"Asignando en la semana {semana_asignacion}...")

            #Obtener el porcentaje de semana actual
            porcentaje = ((i + 1) / semanas) * 100
            
            if(porcentaje < 25):
                tipo_semana = 'Inicial'
            elif(porcentaje >= 25 and porcentaje <=75):
                tipo_semana = 'Intermedia'
            elif(porcentaje > 75):
                tipo_semana = 'Final'
            # Obtener los recursos disponibles para el rol requerido - Buscar todos los roles
            horas_tipo_semana = horas_predecidas.filter(tipo_semana=tipo_semana)
            
            #Agregar obtener las horas
            for horas in horas_tipo_semana:
                if(tipo_horas == 'A1'):
                    cant_horas = horas.hh_min
                elif(tipo_horas == 'A3'):
                    cant_horas = horas.hh_max
                else:
                    cant_horas = horas.hh_prom
                empleado = obtener_empleado(proyecto.id, horas.rol, semana_asignacion, anio, cant_horas)
                Asignacion.objects.update_or_create(
                    proyecto = proyecto,
                    empleado = empleado,
                    semana = semana_asignacion,
                    anio = anio,
                    defaults={'horas_asignadas': cant_horas}
                )
        break
                
    # Mensaje final de depuración
    if asignacion_realizada:
        return "Asignación de recursos realizada con éxito."
    else:
        return "No se pudo realizar la asignación. Verifique la disponibilidad de recursos y la demanda de horas."

def subir_empleados_db():
    cargar_empleados()
    
def obtener_empleado(proyecto_id, rol, semana, anio, cant_horas):
    """
    Obtiene un empleado que esté disponible. Primero intenta utilizar al empleado asignado anteriormente, en caso de no
    tener un asignado a un empleado anteriormente o que este no esté disponible, buscará un empleado disponible dentro de la 
    DB.
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
        empleados = Empleado.objects.filter(rol=rol)
        for idx, empleado in enumerate(empleados):
            disponible = verificar_disponibilidad(empleado, semana, anio, cant_horas)
            if(disponible):
                asignado = True
                return empleado

def verificar_disponibilidad(id_emp, semana, anio, cant_horas):
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


##Junily Disponibilidad views.py.
def disponibilidad(request):
    if not request.user.is_authenticated:
        return redirect(iniciar_sesion)

    asignaciones = Asignacion.objects.select_related('empleado').order_by('anio','semana').all()
    data = defaultdict(lambda: defaultdict(list)) #Agrupacion por semanas
    
    Asignacion.objects.update_or_create(
        proyecto = proyectosAAgrupar.objects.get(id=459),
        empleado = Empleado.objects.get(id=3),
        semana = 24, #Cualquiera
        anio = 2025, #Cualquiera
        defaults={'horas_asignadas': 18}
    )

    for asignacion in asignaciones:
        empleado = asignacion.empleado
        horas_asignadas = Asignacion.objects.filter(empleado=empleado, semana=asignacion.semana, anio=asignacion.anio).aggregate(Sum('horas_asignadas'))['horas_asignadas__sum'] or 0
        horas_disponibles = empleado.horas_totales - horas_asignadas
        porcentaje_uso = round((horas_asignadas / empleado.horas_totales * 100)) if empleado.horas_totales > 0 else 0

        if porcentaje_uso <= 50.0:
            color = "bg-success"
        elif porcentaje_uso <= 75.0:
            color = "bg-warning"
        else:
            color = "bg-danger"



        data[empleado]['nombre'] = empleado.nombre
        data[empleado]['rol'] = empleado.rol
        data[empleado]['color'] = color
        data[empleado]['horas_totales'] = empleado.horas_totales
        data[empleado]['asignaciones'].append({
            'semana': asignacion.semana,
            'año': asignacion.anio,
            'horas_disponibles': horas_disponibles,
            'porcentaje_uso': porcentaje_uso,
            'color': color
        })

    def agrupacion(iterable, n):
        it = iter(iterable)
        while True:
            chunk = list(islice(it, n))
            if not chunk:
                break
            yield chunk
    
    for empleado, values in data.items():
        semanas = values['asignaciones']
        semanas_agrupadas = list(agrupacion(semanas, 4))
        data[empleado]['semanas_agrupadas'] = semanas_agrupadas

    data_list = [{'empleado': empleado, **values} for empleado, values in data.items()]
        
    return render(request, 'core/disponibilidad.html', {'data': data_list})

