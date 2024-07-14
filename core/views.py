from django.shortcuts import redirect, render
from .models import Ventas, Perfil_hh_Detalle_Semanal, Disponibilidad, Hh_Estimado_Detalle_Semanal
from .forms import VentasForm, DispForm, UploadFileForm
from datetime import datetime, timedelta, time
import random
import requests
import json
from openpyxl import load_workbook
import csv
from django.contrib import messages
import pandas as pd

# Create your views here.

def index(request):
    #Obtener y cargar los datos en el formlario
    formsVentas = [VentasForm(prefix=str(i)) for i in range(5)]
    formsDisp = [DispForm(prefix=str(i)) for i in range(5)]
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
                else:
                    data['mesg'] = 'Se han encontrado los siguientes errores: ' + form.errors
            else:
                continue
                
    return render(request, "core/index.html", data)

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

    #return render(request, "core/boton.html", data)

def llenar_DB(request):
    Perfil_hh_Detalle_Semanal.objects.update_or_create(
        idTipoProyecto = '1', 
        numSemana = '33', 
        hh = 1.8
        )
    Perfil_hh_Detalle_Semanal.objects.update_or_create(
        idTipoProyecto = '2', 
        numSemana = '31', 
        hh = '1'
        )
    Perfil_hh_Detalle_Semanal.objects.update_or_create(
        idTipoProyecto = '2', 
        numSemana = '35', 
        hh = 2.4
        )
    Perfil_hh_Detalle_Semanal.objects.update_or_create(
        idTipoProyecto = '1', 
        numSemana = '34', 
        hh = 1.8
        )
    Perfil_hh_Detalle_Semanal.objects.update_or_create(
        idTipoProyecto = '1', 
        numSemana = '34', 
        hh = 1.9
        )
    Perfil_hh_Detalle_Semanal.objects.update_or_create(
        idTipoProyecto = '2', 
        numSemana = '31', 
        hh = 3.5
        )
    Perfil_hh_Detalle_Semanal.objects.update_or_create(
        idTipoProyecto = '2', 
        numSemana = '35', 
        hh = 2.1
        )
    Perfil_hh_Detalle_Semanal.objects.update_or_create(
        idTipoProyecto = '2', 
        numSemana = '34', 
        hh = 1.8
        )
    Perfil_hh_Detalle_Semanal.objects.update_or_create(
        idTipoProyecto = '1', 
        numSemana = '32', 
        hh = 3.1
        )
    Perfil_hh_Detalle_Semanal.objects.update_or_create(
        idTipoProyecto = '1', 
        numSemana = '34', 
        hh = '5'
        )
    Perfil_hh_Detalle_Semanal.objects.update_or_create(
        idTipoProyecto = '2', 
        numSemana = '34', 
        hh = '1'
        )
    Perfil_hh_Detalle_Semanal.objects.update_or_create(
        idTipoProyecto = '2', 
        numSemana = '31', 
        hh = 3.4
        )
    Perfil_hh_Detalle_Semanal.objects.update_or_create(
        idTipoProyecto = '1', 
        numSemana = '33', 
        hh = 2.8
        )
    Perfil_hh_Detalle_Semanal.objects.update_or_create(
        idTipoProyecto = '1', 
        numSemana = '33', 
        hh = '2'
        )
    Perfil_hh_Detalle_Semanal.objects.update_or_create(
        idTipoProyecto = '2', 
        numSemana = '33', 
        hh = 1.4
        )
    Perfil_hh_Detalle_Semanal.objects.update_or_create(
        idTipoProyecto = '1', 
        numSemana = '35', 
        hh = 4.8
        )
    Perfil_hh_Detalle_Semanal.objects.update_or_create(
        idTipoProyecto = '1', 
        numSemana = '33', 
        hh = 4.4
        )
    Perfil_hh_Detalle_Semanal.objects.update_or_create(
        idTipoProyecto = '1', 
        numSemana = '34', 
        hh = 3.4
        )
    Perfil_hh_Detalle_Semanal.objects.update_or_create(
        idTipoProyecto = '2', 
        numSemana = '31', 
        hh = 0.4
        )
    Perfil_hh_Detalle_Semanal.objects.update_or_create(
        idTipoProyecto = '1', 
        numSemana = '33', 
        hh = 0.8
        )
    Perfil_hh_Detalle_Semanal.objects.update_or_create(
        idTipoProyecto = '2', 
        numSemana = '35', 
        hh = '10'
        )    
    return redirect(index)

def join_DB(request):
    # Obtener todas las ventas
    ventas = Ventas.objects.all()

    for venta in ventas:
        print("se inicio el for en ventas")
        # Buscar el correspondiente Perfil_hh_Detalle_Semanal por idTipoProyecto
        perfil_hh = Perfil_hh_Detalle_Semanal.objects.filter(idTipoProyecto=venta.idTipoProyecto)
        print(len(perfil_hh))

        if perfil_hh:
            for perfil in perfil_hh:
                
                ##Obtener la semana a través de código. PERO, de todas los valores
                #Obtener las fechas de 9 semanas al futuro
                #Semana 1-> 12/07 + 9 semanas
                #Semana 2->16/08
                #...
                
                
                # Calcular el año y la semana a partir de la fecha de Ventas
                anio = venta.fecha.year
                semana = venta.fecha.isocalendar()[1]  # Obtener la semana del año

                # Crear una nueva instancia de Hh_Estimado_Detalle_Semanal
                # nueva_instancia = Hh_Estimado_Detalle_Semanal(
                #     idVentas=venta,
                #     idPerfilHhDetalleSemanal=perfil_hh,
                #     fecha=venta.fecha,
                #     hh=perfil_hh[0].hh,
                #     anio=anio,
                #     semana=semana
                # )
                #nueva_instancia.save()
                #print(nueva_instancia)
    return redirect(index)