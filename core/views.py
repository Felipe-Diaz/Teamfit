from django.shortcuts import redirect, render
from .models import Ventas, Perfil_hh_Detalle_Semanal, Disponibilidad, Hh_Estimado_Detalle_Semanal, Graficos
from .forms import VentasForm, DispForm, UploadFileForm
from datetime import datetime, timedelta, time
import random
import requests
import json
from openpyxl import load_workbook
import csv
from django.contrib import messages
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html
from django_plotly_dash import DjangoDash

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
                        fecha=str(datos['fecha'])
                        fecha = fecha[:10]
                        initial_data = {
                            'idTipoProyecto': datos['idTipoProyecto'],
                            'fecha': fecha
                        }
                        form = VentasForm(initial=initial_data, prefix=str(i))
                        forms.append(form)
                    data['VentasForms'] = forms
        else:
            data["mesg"] = "El valor es inválido"
            return render(request, 'core/boton.html', data)
        
    #Guardar los datos en la DB
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
        try:
            if(nuevasVentas):
                createDetalle = newCreateJoinDB()
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
            
            #forms = [VentasForm(initial=datos) for datos in datos_formularios]
            #data['VentasForms'] = forms
            #return render(request, 'core/boton.html', {'VentasForms': forms})
            
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
    Perfil_hh_Detalle_Semanal.objects.update_or_create(
        idTipoProyecto = '1', 
        numSemana = '1', 
        hh = 1.8
        )
    Perfil_hh_Detalle_Semanal.objects.update_or_create(
        idTipoProyecto = '1', 
        numSemana = '2', 
        hh = 2.8
        )
    Perfil_hh_Detalle_Semanal.objects.update_or_create(
        idTipoProyecto = '1', 
        numSemana = '3', 
        hh = 2.4
        )
    Perfil_hh_Detalle_Semanal.objects.update_or_create(
        idTipoProyecto = '1', 
        numSemana = '4', 
        hh = 1.8
        )
    Perfil_hh_Detalle_Semanal.objects.update_or_create(
        idTipoProyecto = '1', 
        numSemana = '5', 
        hh = 1.9
        )
    Perfil_hh_Detalle_Semanal.objects.update_or_create(
        idTipoProyecto = '2', 
        numSemana = '1', 
        hh = 3.5
        )
    Perfil_hh_Detalle_Semanal.objects.update_or_create(
        idTipoProyecto = '2', 
        numSemana = '2', 
        hh = 2.1
        )
    Perfil_hh_Detalle_Semanal.objects.update_or_create(
        idTipoProyecto = '2', 
        numSemana = '3', 
        hh = 1.8
        )
    Perfil_hh_Detalle_Semanal.objects.update_or_create(
        idTipoProyecto = '2', 
        numSemana = '4', 
        hh = 3.1
        )
    Perfil_hh_Detalle_Semanal.objects.update_or_create(
        idTipoProyecto = '2', 
        numSemana = '5', 
        hh = 5
        ) #--> Tipo 2 - Semana 5
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
                print("Fecha: " + str(fecha) + " - ID perfilHH: " + str(perfil_HH[0].id) + " - Ventas: " + str(venta.id) + 
                      " - Año: " + str(anio) + " - Semana del Año: " +  str(semanaPredecir) + " - Horas: " + str(horasHombre) +
                      "  - Semana Proyecto: " + str(semanaProyecto))
                hhDetalleSemana = Hh_Estimado_Detalle_Semanal(fecha=fecha, anio=anio, semana=semanaPredecir, idVentas=venta, 
                                                             idPerfilHhDetalleSemanal=perfil_HH[0], hh=horasHombre)
                hhDetalleSemana.save()
    return True

def create_additional_table():
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