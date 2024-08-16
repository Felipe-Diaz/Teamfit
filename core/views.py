from django.shortcuts import redirect, render
from django.db.models import Sum
from .models import Ventas, Perfil_hh_Detalle_Semanal, Disponibilidad, Hh_Estimado_Detalle_Semanal, Graficos, historialCambios,Distribuidor_HH,HorasRequeridas
from .forms import VentasForm, DispForm, UploadFileForm, LoginForm, CrearUsuarioAdmin, AsignadorHHForm
from datetime import datetime, timedelta, time
import random
import requests
import json
import plotly.io as pio
from openpyxl import load_workbook
import csv
from django.contrib import messages
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
# from dash import Dash, dcc, html
# from django_plotly_dash import DjangoDash
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.utils import timezone
import pytz

# Create your views here.

def index(request):
    #Obtener y cargar los datos en el formlario
    formsVentas = [VentasForm(prefix=str(i)) for i in range(5)]
    formsDisp = [DispForm(prefix=str(i)) for i in range(5)]
    nuevasVentas = False
    nuevasHoras = False
    data = {"VentasForms":formsVentas, "DispForms":formsDisp, 'form':UploadFileForm()}
    
    if request.method == 'POST' and 'file' in request.FILES:
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            if not file.name.endswith(('.csv', '.xlsx')):
                data['mesg'] = 'Archivo no compatible. Por favor, selecciona un archivo CSV o XLSX.'
            else:
                df = pd.read_excel(file) if file.name.endswith('.xlsx') else pd.read_csv(file)
                required_columns = ['idTipoProyecto', 'fecha']
                if not all(col in df.columns for col in required_columns):
                    data['mesg'] = 'El archivo no contiene las columnas requeridas (idTipoProyecto, fecha). Por favor, sube un archivo con estas columnas.'
                else:
                    datos_formularios = df.to_dict(orient='records')
                    forms = []
                    for i, datos in enumerate(datos_formularios):
                        #Modificar para implementar las nuevas columnas
                        fecha=str(datos['fecha'])
                        fecha = fecha[:10]
                        initial_data = {
                            'idTipoProyecto': datos['idTipoProyecto'],
                            'fecha': fecha
                        }
                        #Modificar y crear un nuevo formulario
                        form = VentasForm(initial=initial_data, prefix=str(i))
                        forms.append(form)
                    data['VentasForms'] = forms
        else:
            data["mesg"] = "El valor es inválido"
            return render(request, 'core/boton.html', data)
        
    #Guardar los datos en la DB
    #Modifica para nuevo tipo de archivo
    if request.method == "POST" and not ('file' in request.FILES):
        formsVentas = [VentasForm(request.POST, prefix=str(i)) for i in range(150)]
        for i, form in enumerate(formsVentas):
            fecha = request.POST.get(f"{i}-fecha", None)
            if(form['idTipoProyecto'] == 'na' or fecha==None):
                break
            else:
                try:
                    if form.is_valid(): 
                        if(form.cleaned_data['idTipoProyecto'] == 'na'):
                            print("Datos No Seleccionables")
                        else:
                            idTipoProyecto = form.cleaned_data['idTipoProyecto']
                            fecha = form.cleaned_data['fecha']
                            obj = Ventas(idTipoProyecto=idTipoProyecto, fecha=fecha)
                            obj.save()
                            data['mesg'] = 'Se han almacenado ' + str(i) + ' datos de proyectos nuevos' 
                            nuevasVentas = True
                    else:
                        data['mesg'] = 'Se han encontrado los siguientes errores: ' + form.errors
                except Exception as e:
                    print(e)
                
        ##No considerar
        formsDisp = [DispForm(request.POST, prefix=str(i)) for i in range(5)]
        for form in formsDisp:
            if form.has_changed():
                if form.is_valid():
                    semana = form.cleaned_data['semana']
                    hh = form.cleaned_data['HorasHombre']
                    obj = Disponibilidad(semana=semana, hh=hh)
                    obj.save()
                    data['mesg'] = 'Se han almacenado ' + str(i) + ' datos de horas disponibles' 
                    nuevasHoras = True
                else:
                    data['mesg'] = 'Se han encontrado los siguientes errores: ' + form.errors
            else:
                continue
        #No considerar
        try:
            if(nuevasVentas):
                createDetalle = newCreateJoinDB()
                createGraficos = create_additional_table()
            if(nuevasHoras):
                createGraficos = create_additional_table()
            return redirect(graficar_Datos)
        except Exception as e:
            data['mesg'] = 'Han ocurrido errores, por favor, verifique los datos ingresados'
            print(e)
        
    return render(request, "core/index.html", data)


def graficar_Datos(request):
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
    User.objects.all().delete()
    
    #Usuario de testing
    usuario = User.objects.create_user(username="admin", password='Admin@123')
    usuario.first_name = "Admin"
    usuario.last_name = "Admin 1"
    usuario.email = "admin@admin.com"
    usuario.is_superuser = True
    usuario.is_staff = True
    usuario.save()
    
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
    return redirect(index)

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

#Aqui crear validaciones
def create_additional_table():
    Graficos.objects.all().delete()
    #agregar datos de hoy en adelante
    data = Hh_Estimado_Detalle_Semanal.objects.all()
    #validaciones para detalle semanal
    data_list = list(data.values())
    df = pd.DataFrame(data_list)
    
    disp = Disponibilidad.objects.all()
    #validaciones para disponibilidad
    dispList = list(disp.values())
    dfDisp = pd.DataFrame(dispList)
    dfDisp.rename(columns={'hh': 'hh_disp'}, inplace=True)
    
    #validaciones con el dataframe listo
    weekly_data = df.groupby('semana')['hh'].sum().reset_index()#linea de codigo donde se obtine las horas requeridas
    weekly_data.rename(columns={'hh': 'hh_req'}, inplace=True)
    weekly_data = pd.merge(dfDisp, weekly_data, on='semana', how='outer')
    weekly_data['utilizacion'] = round((weekly_data['hh_req'] / weekly_data['hh_disp']) * 100, 1)# saca la utilización del proyecto
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
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                nombre = user.first_name
                apellido = user.last_name
                desc = f"El usuario {nombre} {apellido} ha iniciado sesión"
                almacenado = almacenarHistorial(desc, "2", user)
                print(almacenado)
                return redirect(pagina_principal)
            else:
                data = {'mesg':'Usuario o contraseña incorrectos', 'form':LoginForm}
                #form.add_error(None, 'Usuario o contraseña incorrectos')
    else:
         data = {'form': LoginForm}
    return render(request, 'core/login.html', data)

#Crear un cerrar sesión
def cerrar_sesion(request):
    nombre = request.user.first_name
    apellido = request.user.last_name
    user = request.user
    desc = f"El usuario {nombre} {apellido} ha cerrado sesión"
    almacenado = almacenarHistorial(desc, "2", user)
    logout(request)
    return redirect(iniciar_sesion) 

def crear_usuarios(request):
    data = {'form':CrearUsuarioAdmin}
    return render(request, 'core/crearUsuarios.html', data)

def pagina_principal(request):
    data = {}
    return render(request, 'core/index1.html', data)

#Almacena el historial solicitando desc, tipoInfo y usuario
def almacenarHistorial(desc, tipoInfo, usuario):
    histCambios = historialCambios()   

    fecha = timezone.now()
    print(fecha)
    histCambios.fecha = fecha
    
    print(histCambios.fecha)
        
    if(len(desc) > 300):
        desc = desc[:300]
        print("Demasiados caracteres en la descripción")
    histCambios.desc = desc
        
    tiposInformaciones = {"1":"Modificación en la DB", "2": "Informativo", "3":"Error", "4":"Otro"}
    if(tipoInfo not in tiposInformaciones):
        tipoInfo = "4"
    histCambios.tipoInfo = tiposInformaciones[tipoInfo]
    
    if(usuario is None):
        print("El usuario es inexistente")
        usuario = User.objects.get(username="Anon")
        histCambios.usuario = usuario
        
    histCambios.usuario = usuario
    histCambios.save()
    #return True
    return histCambios

from django.shortcuts import render
from .forms import AsignadorHHForm
from .models import Distribuidor_HH  # Asegúrate de que este sea el nombre correcto de tu modelo
import pandas as pd

def AsignadorHH_subir_archivo_Exel(request):
    if request.method == "POST":
        form = AsignadorHHForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['file']
            df = pd.read_excel(excel_file)

            if 'Guardar Datos' in request.POST:
                # Guardar los datos editados en la base de datos
                for i, row in df.iterrows():
                    id_empleado = request.POST.get(f'id_empleado_{i + 1}')
                    nombre = request.POST.get(f'nombre_empleado_{i + 1}')
                    cargo = request.POST.get(f'cargo_{i + 1}')
                    telefono = request.POST.get(f'telefono_{i + 1}')
                    id_categoria = request.POST.get(f'id_categoria_{i + 1}')
                    horas_dis_empleado = request.POST.get(f'horas_dis_empleado_{i + 1}')

                    # Crear o actualizar el registro en la base de datos
                    distribuidor, created = Distribuidor_HH.objects.update_or_create(
                        id_empleado=id_empleado,
                        defaults={
                            'nombre': nombre,
                            'cargo': cargo,
                            'telefono': telefono,
                            'idcategoria': id_categoria,
                            'disponibilidad': horas_dis_empleado,
                        }
                    )
                # Redirigir a una página de éxito o volver a la misma página con un mensaje de éxito
                return render(request, 'core/asignador_hh.html', {'form': form, 'success': True})

            elif 'Previsualizar Datos' in request.POST:
                # Convertir los datos del DataFrame en una lista de diccionarios para la previsualización
                data_list = df.to_dict(orient='records')

                # Renderizar la página para revisar y editar los datos
                return render(request, 'core/asignador_hh.html', {'form': form, 'data_list': data_list})

    else:
        form = AsignadorHHForm()

    return render(request, 'core/asignador_hh.html', {'form': form})

def asignar_horas(request):
    if request.method == "POST":
        semanas_horas = HorasRequeridas.objects.all().order_by('id_semana')
        empleados = Distribuidor_HH.objects.filter(horas_dis_empleado__gt=0).order_by('id_categoria')
        
        asignaciones = []

        for semana_horas in semanas_horas:
            proyecto = f"Semana {semana_horas.id_semana}"
            horas_requeridas = semana_horas.horas_requeridas
            horas_asignadas = 0
            proyecto_asignaciones = []

            print(f"\nAsignando recursos para {proyecto} (Horas requeridas: {horas_requeridas})")
            
            for empleado in empleados:
                if horas_asignadas >= horas_requeridas:
                    break

                horas_disponibles = empleado.horas_dis_empleado
                horas_a_asignar = min(horas_disponibles, horas_requeridas - horas_asignadas)
                
                if horas_a_asignar > 0:
                    horas_asignadas += horas_a_asignar
                    proyecto_asignaciones.append({
                        'proyecto': proyecto,
                        'empleado': empleado.nombre_empleado,
                        'horas_asignadas': horas_a_asignar
                    })

                    print(f"Empleado asignado: {empleado.nombre_empleado} ({empleado.cargo}) - Horas asignadas: {horas_a_asignar}")

            asignaciones.append({
                'proyecto': proyecto,
                'horas_requeridas': horas_requeridas,
                'asignaciones': proyecto_asignaciones
            })

        return render(request, 'core/resultados.html', {'asignaciones': asignaciones})

    # Si es GET, mostrar las semanas y horas requeridas desde la base de datos
    semanas_horas = HorasRequeridas.objects.all().order_by('id_semana')

    return render(request, 'core/asignarR.html', {'semanas_horas': semanas_horas})

def resultados(request):
    # Puedes incluir lógica aquí si es necesario
    # Por ahora, esta vista simplemente renderiza la plantilla con el contexto recibido
    return render(request, 'core/resultados.html')

def dashboardP_Profesional(request):
    # Obtener los datos agrupados por cargo
    empleados_por_cargo = Distribuidor_HH.objects.values('cargo').annotate(total_horas=Sum('horas_dis_empleado'))

    # Crear listas para nombres de cargos y horas
    cargos = [empleado['cargo'] for empleado in empleados_por_cargo]
    horas = [empleado['total_horas'] for empleado in empleados_por_cargo]

    # Crear gráfico interactivo con plotly
    fig = go.Figure([go.Bar(x=cargos, y=horas)])
    fig.update_layout(title='Distribución de Horas Semanales por Perfil Profesional',
                      xaxis_title='Perfil Profesional',
                      yaxis_title='Horas a Consumir',
                      barmode='stack')

    # Convertir el gráfico en HTML
    graph_html = pio.to_html(fig, full_html=False)

    return render(request, 'core/dashboardP_Profesional.html', {
        'graph_html': graph_html,
        'cargos': cargos,  # Pasar los cargos al HTML
    })