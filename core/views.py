from django.shortcuts import redirect, render, get_object_or_404, redirect
from .models import Ventas, Perfil_hh_Detalle_Semanal, Disponibilidad, Hh_Estimado_Detalle_Semanal
from .models import Graficos, historialCambios, proyectosAAgrupar, PerfilUsuario, Parametro, User
from .forms import VentasForm, DispForm, UploadFileForm, LoginForm, CrearUsuarioAdmin, proyectosForm, CategoriasForm , UsuarioForm #, PerfilUsuarioForm
from .forms import CATEGORIAS_MAPPING
from datetime import datetime, timedelta, time
import random
import requests
import json
#from openpyxl import load_workbook
import csv
from django.contrib import messages
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.utils import timezone
import pytz
from django.http import HttpResponse, JsonResponse
from .clusters_data import realizar_clusterizacion

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
                disponibilidad = 0,
                utilizacion = 0
            )
            cont += 1
            proyecto.save()
        cat = {'Cat':'E','Sub':'1'}
        almacenado = almacenarHistorial(cat, request.user)
        request.session.pop('df_proyectos')
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
                                    'C/Agencia', 'Ocupación Al Iniciar (%)']
                if not all(col in df.columns for col in required_columns):
                    mesg = ('<div style="container col-md-6"> El archivo <strong>no contiene</strong> las columnas requeridas:'
                                    '<ul> <li>id</li> <li>Proyecto</li> <li>Línea de Negocio</li> <li>tipo</li>'
                                    '<li>cliente</li> <li>create_date</li> <li>Cierre</li> <li>Egresos No HH CLP</li>'
                                    '<li>Monto Oferta CLP</li> <li>C/Agencia</li> <li>Ocupación Al Iniciar (%)</li> </ul>'
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
    df.rename(columns={'Proyecto': 'proyecto'}, inplace=True)
    df.rename(columns={'Línea de Negocio': 'lineaNegocio'}, inplace=True)
    df.rename(columns={'create_date': 'createDate'}, inplace=True)
    df.rename(columns={'Cierre': 'cierre'}, inplace=True)
    df.rename(columns={'Egresos No HH CLP': 'egresosNoHHCLP'}, inplace=True)
    df.rename(columns={'Monto Oferta CLP': 'montoOfertaCLP'}, inplace=True)    
    df.rename(columns={'C/Agencia': 'usoAgencia'}, inplace=True)
    df.rename(columns={'Ocupación Al Iniciar (%)': 'ocupacionInicio'}, inplace=True)
    df['ocupacionInicio'] = df['ocupacionInicio'].round(2)
    df['ocupacionInicio'] = df['ocupacionInicio'] * 100
    return df

def cambiarFormatoAlmacenarDb(df):
    df = pd.DataFrame(df)
    df['createDate'] = pd.to_datetime(df['createDate'])
    df['cierre'] = pd.to_datetime(df['cierre'])
    df['cierre'] = df['cierre'].fillna(df['createDate'])
    df['cliente'] = df['cliente'].astype(int)
    df['usoAgencia'] = df['usoAgencia'].fillna(0)
    df['usoAgencia'] = df['usoAgencia'].replace({'Sí': 1, 'no': 0}).astype(bool)
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
        if(len(ids_nulos) > 5):
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
    Hh_Estimado_Detalle_Semanal.objects.all().delete()
    Perfil_hh_Detalle_Semanal.objects.all().delete()
    historialCambios.objects.all().delete()
    proyectosAAgrupar.objects.all().delete()
    User.objects.all().delete()

    
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
    usuario = User.objects.create_user(username="admin", password='Admin@123')
    usuario.first_name = "Pedro"
    usuario.last_name = "Martinez"
    usuario.email = "admin@admin.com"
    usuario.is_superuser = True
    usuario.is_staff = True
    usuario.save()
    
    perfil = PerfilUsuario.objects.update_or_create(user=usuario, cargo='Administrador')
    
    #Crear un usuario inactivo y modificar el login para no dejarlo loguearse
    usuarioAnon = User.objects.create_user(username="Anon", password='anon') #ZKfg!)nkLSp163SD
    usuarioAnon.first_name = "Anonimo"
    usuarioAnon.last_name = "anon"
    usuarioAnon.email = "none"
    usuarioAnon.is_superuser = False
    usuarioAnon.is_staff = False
    usuarioAnon.is_active = False
    usuarioAnon.save()
    
    Perfil_hh_Detalle_Semanal.objects.update_or_create(
        idTipoProyecto = '1', 
        numSemana = '1', 
        hh = 1.8
        )
    Perfil_hh_Detalle_Semanal.objects.update_or_create(
        idTipoProyecto = '1', 
        numSemana = '2', 
        hh = 2.1
        )
    Perfil_hh_Detalle_Semanal.objects.update_or_create(
        idTipoProyecto = '1', 
        numSemana = '3', 
        hh = 1.9
        )
    Perfil_hh_Detalle_Semanal.objects.update_or_create(
        idTipoProyecto = '1', 
        numSemana = '4', 
        hh = 1.5
        )
    Perfil_hh_Detalle_Semanal.objects.update_or_create(
        idTipoProyecto = '2', 
        numSemana = '1', 
        hh = 1.5
        )
    Perfil_hh_Detalle_Semanal.objects.update_or_create(
        idTipoProyecto = '2', 
        numSemana = '2', 
        hh = 3
        )
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
            "Elimino usuario",       # E3
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


    return render(request, 'core/index1.html', data)

#Almacena el historial solicitando desc, tipoInfo y usuario
def almacenarHistorial(categoria={'Cat':"A",'Sub':'1'}, usuario=None):
    """Almacena el historial.

        Parametros: 
        categoria: Diccionario con la categoria y la subcategoría. Debe venir con clave Cat para categoria, y Sub para la subcategoria.
        usuario: Usuario para almacenar e indicar quien realizar la acción. En caso de venir nulo es un usuario anónimo
        
        Return:
        histCambios: Objeto de tipo Historial Cambios.
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
    "E3": "Elimino usuario",
    "F1": "Cambio un cargo",
    "F2": "Actualizó permisos",
    "G1": "Realizó la clusterización"
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
        "B1": "3",
        "B2": "3",
        "C1": "3",
        "C2": "3",
        "C3": "3",
        "D1": "2",
        "E1": "2",
        "E2": "3",
        "E3": "3",
        "F1": "3",
        "F2": "3",
        "F3": "2",
        "G1": "3"
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

    usuario = get_object_or_404(User, id=id)
    pusuario = get_object_or_404(PerfilUsuario, user=usuario)
    
    if request.method == 'POST':
        form = UsuarioForm(request.POST, instance=usuario, perfil_usuario=pusuario)
        
        if form.is_valid():
            form.save()
            pusuario.cargo = form.cleaned_data['cargo']
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
        'usuario_editado': usuario
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
    
    data = {'messages':messages, 'usuarios':usuarios, 'merror':merror}
    return render (request, 'core/verUsuarios.html', data)

def ajuste_parametros(request):
    if not request.user.is_authenticated:
        return redirect(iniciar_sesion)
    
    messages = []
    merror = []
    data = {}
    
    if request.method == 'POST':
        form = CategoriasForm(request.POST)
        if(form.is_valid()):
            try:
                to_keep = obtener_campos_secundarios(form=form)
                print(to_keep)
                valor_parametro = {
                    'valores_a_mantener':to_keep
                }
                parametro, created = Parametro.objects.update_or_create(
                    nombre_parametro='historial.mantener',
                    defaults={'valor': valor_parametro},
                )
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
            mesg = 'Ha ocurrido un error. Por favor, verifique los campos correctamente o intentelo de nuevo más tarde.'
            merror.append(mesg)
            
    form = obtener_valores_formulario_parametro(CategoriasForm())
    data['form'] = form
    data['messages'] = messages
    data['merror'] = merror
        
    return render(request, 'core/parameters.html',data)


def obtener_campos_secundarios(form):
    sub_cats = obtener_subcategorias()
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
    print(initial_data)            
    initial_data = marcar_categorias_principales_parametros(initial_data=initial_data)

    form = CategoriasForm(initial=initial_data)
    return form


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
                print(datos)

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
                    print(almacenado)
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
    
    data = {}
    if(request.method == 'POST'):
        clusterizacion = realizar_clusterizacion
        if(clusterizacion):
            data = {'mesg':'Se ha realizado la clusterización'}
        else:
            data = {'mesg':'No se ha realizado la clusterización'}
        
    return render(request, "core/cluster.html", data)

def cluster2_testing(request):
    if not request.user.is_authenticated:
        return redirect(iniciar_sesion)
    
    data = {}
    if(request.method == 'POST'):
        print('Nanananana asdasd')
        clusterizacion = realizar_clusterizacion
        if(clusterizacion):
            data = {'mesg':'Se ha realizado la clusterización'}
        else:
            data = {'mesg':'No se ha realizado la clusterización'}
        
    return render(request, "core/cluster.html", data)
    