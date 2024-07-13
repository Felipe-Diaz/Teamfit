from django.shortcuts import redirect, render
from .models import Ventas, Perfil_hh_Detalle_Semanal
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
    forms = [VentasForm() for _ in range(5)]
    data = {"VentasForms":forms, "DispForm":DispForm}
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
            uploaded_file = request.FILES['file']
            file_name = uploaded_file.name
            # Verificar si es un archivo CSV
            if file_name.endswith('.csv'):
                try:
                    df = pd.read_csv(uploaded_file)
                    if validar_datos_csv(df):
                        save_to_database(df)
                        data['mesg'] = "Archivo CSV procesado y cargado en la base de datos."
                    else:
                        data['mesg'] = "El archivo CSV no cumple con los criterios de validación."
                except Exception as e:
                    data['mesg'] = f"Error al procesar archivo CSV: {str(e)}"
            # Verificar si es un archivo XLSX
            elif file_name.endswith('.xlsx'):
                try:
                    workbook = load_workbook(uploaded_file)
                    df = pd.DataFrame(workbook.active.values)
                    if validar_datos_xlsx(df):
                        save_to_database(df)
                        data['mesg'] = "Archivo XLSX procesado y cargado en la base de datos."
                    else:
                        data['mesg'] = "El archivo XLSX no cumple con los criterios de validación."
                except Exception as e:
                    data['mesg'] = f"Error al procesar archivo XLSX: {str(e)}"
            else:
                data['mesg'] = "El archivo debe ser CSV o XLSX."
        else:
            data['mesg'] = "Formulario no válido. Por favor, revise los campos."
    return render(request, "core/boton.html", data)

def llenar_DB(request):
    Perfil_hh_Detalle_Semanal.objects.update_or_create(
        idTipoProyecto = '1', 
        numSemana = '33', 
        hh = '1,8'
        )
    Perfil_hh_Detalle_Semanal.objects.update_or_create(
        idTipoProyecto = '2', 
        numSemana = '31', 
        hh = '1'
        )
    Perfil_hh_Detalle_Semanal.objects.update_or_create(
        idTipoProyecto = '2', 
        numSemana = '35', 
        hh = '2,4'
        )
    Perfil_hh_Detalle_Semanal.objects.update_or_create(
        idTipoProyecto = '1', 
        numSemana = '34', 
        hh = '1,8'
        )
    Perfil_hh_Detalle_Semanal.objects.update_or_create(
        idTipoProyecto = '1', 
        numSemana = '34', 
        hh = '1,9'
        )
    Perfil_hh_Detalle_Semanal.objects.update_or_create(
        idTipoProyecto = '2', 
        numSemana = '31', 
        hh = '3,5'
        )
    Perfil_hh_Detalle_Semanal.objects.update_or_create(
        idTipoProyecto = '2', 
        numSemana = '35', 
        hh = '2,1'
        )
    Perfil_hh_Detalle_Semanal.objects.update_or_create(
        idTipoProyecto = '2', 
        numSemana = '34', 
        hh = '1,8'
        )
    Perfil_hh_Detalle_Semanal.objects.update_or_create(
        idTipoProyecto = '1', 
        numSemana = '32', 
        hh = '3,1'
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
        hh = '3,4'
        )
    Perfil_hh_Detalle_Semanal.objects.update_or_create(
        idTipoProyecto = '1', 
        numSemana = '33', 
        hh = '2,8'
        )
    Perfil_hh_Detalle_Semanal.objects.update_or_create(
        idTipoProyecto = '1', 
        numSemana = '33', 
        hh = '2'
        )
    Perfil_hh_Detalle_Semanal.objects.update_or_create(
        idTipoProyecto = '2', 
        numSemana = '33', 
        hh = '1,4'
        )
    Perfil_hh_Detalle_Semanal.objects.update_or_create(
        idTipoProyecto = '1', 
        numSemana = '35', 
        hh = '4,8'
        )
    Perfil_hh_Detalle_Semanal.objects.update_or_create(
        idTipoProyecto = '1', 
        numSemana = '33', 
        hh = '4,4'
        )
    Perfil_hh_Detalle_Semanal.objects.update_or_create(
        idTipoProyecto = '1', 
        numSemana = '34', 
        hh = '3,4'
        )
    Perfil_hh_Detalle_Semanal.objects.update_or_create(
        idTipoProyecto = '2', 
        numSemana = '31', 
        hh = '0,4'
        )
    Perfil_hh_Detalle_Semanal.objects.update_or_create(
        idTipoProyecto = '1', 
        numSemana = '33', 
        hh = '0,8'
        )
    Perfil_hh_Detalle_Semanal.objects.update_or_create(
        idTipoProyecto = '2', 
        numSemana = '35', 
        hh = '10'
        )    
    return redirect(index)

#####

def validar_datos_csv(df):
    required_columns = ['idTipoProyecto', 'fecha']
    if not set(required_columns).issubset(df.columns):
        return False
    return True  # Retorna True si pasa la validación

def validar_datos_xlsx(df):
    required_columns = ['idTipoProyecto', 'fecha']
    if not set(required_columns).issubset(df.columns):
        return False
    return True  # Retorna True si pasa la validación

def save_to_database(df):
    for index, row in df.iterrows():
        venta = Ventas(
            idTipoProyecto=row['idTipoProyecto'],
            fecha=row['fecha'],
            # Agrega más columnas según sea necesario
        )
        venta.save()