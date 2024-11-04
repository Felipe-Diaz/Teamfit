#importaciones de Django
from django.shortcuts import redirect, render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db import DatabaseError, IntegrityError, OperationalError
from django.db.models import Sum, Count, Q
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
#Importaciones de models
from .models import Graficos, historialCambios, proyectosAAgrupar, PerfilUsuario, Parametro, User 
from .models import Asignacion, AsignacionControl, HorasPredecidas, proyectosSemanas, Empleado

#Importaciones de forms
from .forms import DispForm, UploadFileForm, LoginForm, CrearUsuarioAdmin
from .forms import CategoriasForm , UsuarioForm, ProgramacionForm, EscenariosForm
from .forms import CATEGORIAS_MAPPING, PROGRAMACION_MAPPING, ESCENARIOS_MAPPING
#Importaciones de apis
from .apis import cargar_empleados, enviar_datos_planning_slots, convertir_datos_asignacion
#Importaciones de util
from .utils import obtener_empleado, obtener_subcategorias, almacenarHistorial, cambiar_scheduler, obtener_campos_secundarios
from .utils import obtener_valores_formulario_parametro, obtener_valores_formulario_parametro_escenarios, obtener_valores_formulario_parametro_programacion
from .utils import obtener_proyectos_sin_asignar, verificarDf, MONTH_TRANSLATION
#Importaciones de clusters_data
from .clusters_data import realizar_clusterizacion
#Importaciones de módulos de Python
import logging
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
from decimal import Decimal
from itertools import islice
from collections import defaultdict
from datetime import timedelta, datetime, date

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
                        print(datosDfDict)
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
    df['usoAgencia'] = df['usoAgencia'].replace({
        'SI': 1,
        'SÍ': 1,
        'Sí': 1,
        'sÍ': 1,
        'sI': 1, 
        'Si': 1, 
        'si': 1, 
        'sí': 1,
        'NO': 0,
        'No': 0, 
        'nO': 0,
        'no': 0,
        0  : 0
    }).astype(bool)
    df['egresosNoHHCLP'] = df['egresosNoHHCLP'].fillna(0)
    df['montoOfertaCLP'] = df['montoOfertaCLP'].astype(int)
    df['ocupacionInicio'] = df['ocupacionInicio'].astype(float) 
    return df



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
    #cargar_empleados()
    
    proyectos = proyectosAAgrupar.objects.all().order_by('-id')[:5]
    data['proyectos'] = proyectos
    list = []
    for i in range(5):
        list.append(i)
    data['peng'] = list

    #Cargar Dashboard
    today = timezone.now().date()
    total_proyectos = proyectosAAgrupar.objects.filter(fechaFin__gt=today)
    total_proyectos = proyectosAAgrupar.objects.all()
    total_proyectos = total_proyectos.count()
    
    proyectos = proyectosSemanas.objects.select_related('proyecto', 'horas').all()
    
    current_month = today.strftime('%B') #Deberia ser Octubre o 'October'.
    current_month = MONTH_TRANSLATION.get(current_month, current_month)
    current_week = today.strftime('%U')

    # Calcular semanas restantes en el año
    weeks_in_year = 52
    remaining_weeks = weeks_in_year - int(current_week)

    empleados_count = proyectos.values('horas__rol').annotate(count=Count('horas__rol'))

    jefes = proyectosSemanas.objects.filter(horas__rol='Jefe de Proyectos').count()
    ingenieros = proyectosSemanas.objects.filter(horas__rol='Ingeniero de Proyecto').count()
    jefes = Empleado.objects.filter(rol='Jefe de Proyectos', activo=True).count()
    ingenieros = Empleado.objects.filter(rol='Ingeniero de Proyecto', activo=True).count()
    

    data['total_proyectos'] = total_proyectos
    data['current_month'] = current_month
    data['current_week'] = current_week
    data['remaining_weeks'] = remaining_weeks
    data['ingenieros'] = ingenieros
    data['jefes'] = jefes

    return render(request, 'core/index1.html', data)
    
#Carga todos los distintos proyectos
def ver_proyectos(request):
    if not request.user.is_authenticated:
        return redirect(iniciar_sesion)
    
    proyectos = proyectosAAgrupar.objects.all()
    data = {'proyectos':proyectos}
    return render(request, 'core/verProyectos.html', data)

#vista carga empleados para poder llamarla con un botón en asignaciones
def vista_carga_empleados(request):
    if request.method == "POST":
        success = cargar_empleados()
        if success:
            messages.success(request, 'Se actualizaron correctamente los empleados.')
            return redirect('disponibilidad')
        else:
            return JsonResponse({'success': False, 'message': 'Error al cargar empleados'})
    return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)

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
    
    if(not request.user.is_staff):
        return redirect(ver_usuarios)
    
    data = {"form":CrearUsuarioAdmin}
    if request.method == 'POST':
        form = CrearUsuarioAdmin(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                cargo = form.cleaned_data.get('cargo')
                PerfUsr = PerfilUsuario.objects.update_or_create(user=user, cargo=cargo)
                cat = {'Cat':'E', 'Sub':'2'}
                almacenado = almacenarHistorial(cat, request.user)
                messages=["Usuario creado con éxito"]
                data["messages"]=messages
                data['form'] = CrearUsuarioAdmin()
            except Exception as e:
                merror=[f'Error guardando usuario. Intente de nuevo más tarde.']
                data['merror'] = merror
                print(e)
        else:
            error_messages = form.errors.as_data()
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
    
    if(not request.user.is_staff):
        return redirect(ver_usuarios)

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

#Desactiva el usuario, validando si existe y si es superuser o no.
def eliminarUsuarios(request, id):
    if(not request.user.is_staff):
        return redirect(ver_usuarios)
    
    if(not request.user.is_staff):
        return redirect(ver_usuarios)
    
    messages = []
    merror = []
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
    
    if(not request.user.is_staff):
        return redirect(pagina_principal)
    
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
                
                ##Guarda los valores del historial
                print(to_keep_programacion)
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
                if not to_keep_escenarios:
                    to_keep_escenarios = ['A2']
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


def carga_Odoo(request):
    if not request.user.is_authenticated:
        return redirect(iniciar_sesion)
    
    # Obtiene todas las asignaciones y sus empleados
    asignaciones = Asignacion.objects.select_related('empleado').filter(enviado = False)
    
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
            'id_asignacion': asignacion.id,
            'id_empleado': asignacion.empleado.id_empleado,
            'id_recurso': asignacion.empleado.id_recurso,
            'nombre': asignacion.empleado.nombre,
            'horas_asignadas': asignacion.horas_asignadas,
            'semana': asignacion.semana,
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'nombre_proyecto': f"{asignacion.proyecto} - Semana {asignacion.semana}",
            'año': anio,
            'enviado': asignacion.enviado
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
        success = False
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
                    try:
                        asignacion_obj = Asignacion.objects.get(id = asignacion['id_asignacion'])
                        asignacion_obj.enviado = True
                        asignacion_obj.save()
                        success = True
                    except Exception as e:
                        print(f'Ha ocurrido un error en la carga odoo: {e}')
                else:
                    mensaje_error = (
                        f"Error al subir los datos a Odoo en la tarea: '{name}', "
                        f"perteneciente a la semana {asignacion['semana']} del año {asignacion['año']}."
                    )
                    messages.error(request, mensaje_error)
        if success:
            messages.success(request, "El proceso se ha realizado correctamente.")
        return redirect(carga_Odoo)

    return render(request, "core/cargaOdoo.html", data)
    
##Funciones Grupo 2

#Esta es la función que genera el exel de la tabla horas_por_recurso_data
def generar_excel_proyectos(request):
    if not request.user.is_authenticated:
        return redirect(iniciar_sesion)
    
    # Obtener el año y la semana desde el request (ajusta esto según tu lógica)
    anio = request.GET.get('anio')
    semana = request.GET.get('semana')

    # Obtener los datos de la tabla horas por recurso
    proyectos = Asignacion.objects.values(
        'empleado__nombre',  # Nombre del recurso
        'empleado__rol',     # Rol del recurso
        'semana',            # Semana
        'anio',              # Año
    ).annotate(
        total_horas_rol=Sum('horas_asignadas')  # Total de horas asignadas
    )

    # Crear un DataFrame a partir de los datos de los proyectos
    df = pd.DataFrame(list(proyectos))

    # Crear un nuevo DataFrame pivotado
    df_pivot = df.pivot_table(
        index=['empleado__nombre', 'empleado__rol'],  # Agrupar por nombre y rol del recurso
        columns=['anio', 'semana'],                    # Asegúrate de que 'anio' esté incluido en las columnas
        values='total_horas_rol',                      # Valores que se colocan en la tabla
        fill_value=0                                    # Rellenar con 0 donde no hay horas asignadas
    ).reset_index()

    # Renombrar las columnas para incluir "Nombre" y "Rol"
    df_pivot.columns.name = None  # Eliminar el nombre de la columna
    df_pivot.columns = [
        'Nombre' if col[0] == 'empleado__nombre' else 'Rol' if col[0] == 'empleado__rol' else f'Semana {col[1]} del Año {col[0]}'
        for col in df_pivot.columns
    ]

    # Calcular el total de horas por recurso y añadirlo como una nueva fila
    total_row = df_pivot.iloc[:, 2:].sum().to_frame().T  # Sumar las horas, omitiendo las dos primeras columnas (Nombre y Rol)
    total_row['Nombre'] = ''  # Asignar el nombre de la fila total
    total_row['Rol'] = 'Total Horas'         # Dejar vacío el campo de rol en la fila total
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
    if not request.user.is_authenticated:
        return redirect(iniciar_sesion)
    
    # Obtener el año y la semana desde el request (ajusta esto según tu lógica)
    anio = request.GET.get('anio')
    semana = request.GET.get('semana')

    # Obtener los datos de asignaciones de la tabla actualizada
    asignaciones = Asignacion.objects.values(
        'proyecto__proyecto',  # Nombre del proyecto
        'semana',              # Semana
        'anio',                # Asegúrate de que también esté incluido el año
    ).annotate(
        total_horas_proyecto=Sum('horas_asignadas')  # Total de horas asignadas por proyecto
    )

    # Crear un DataFrame a partir de los datos de las asignaciones
    df = pd.DataFrame(list(asignaciones))

    # Crear un nuevo DataFrame pivotado
    df_pivot = df.pivot_table(
        index='proyecto__proyecto',  # Agrupar por nombre del proyecto
        columns=['anio', 'semana'],   # Asegúrate de que 'anio' esté incluido en las columnas
        values='total_horas_proyecto',  # Valores que se colocan en la tabla
        fill_value=0                   # Rellenar con 0 donde no hay horas asignadas
    ).reset_index()

    # Renombrar las columnas para incluir "Proyectos"
    df_pivot.columns.name = None  # Eliminar el nombre de la columna
    df_pivot.columns = [
        'Proyectos' if col[0] == 'proyecto__proyecto' else f'Semana {col[1]} del Año {col[0]}'
        for col in df_pivot.columns
    ]

    # Calcular el total de horas por proyecto y añadirlo como una nueva fila
    total_row = df_pivot.iloc[:, 1:].sum().to_frame().T  # Sumar las horas, omitiendo la primera columna que es el proyecto
    total_row['Proyectos'] = 'Total Horas'  # Asignar el nombre de la fila total
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

#Generar Reportes de Asignaciónes
def generar_excel_asignacion(request):
    if not request.user.is_authenticated:
        return redirect(iniciar_sesion)
    # Obtener el formato seleccionado desde el request
    formato = request.GET.get('formato')

    # Obtener los datos de las asignaciones
    asignaciones = Asignacion.objects.all().values(
        'proyecto__proyecto',  # Accediendo al nombre del proyecto
        'empleado__nombre',    # Accediendo al nombre del recurso
        'empleado__rol',       # Accediendo al rol del recurso
        'semana',
        'anio',
        'horas_asignadas'
    )

    # Generar Excel
    if formato == 'excel':
        # Crear un DataFrame a partir de los datos de las asignaciones
        df = pd.DataFrame(list(asignaciones))
        df = df.sort_values(by=['anio', 'semana'], ascending=[True, True])
        
        # Crear un nuevo DataFrame pivotado
        df_pivot = df.pivot_table(
            index=['proyecto__proyecto', 'empleado__nombre', 'empleado__rol'],  # Mantener estas columnas como índices
            columns=['anio', 'semana'],  # Añadir 'anio' a las columnas junto con 'semana'
            values='horas_asignadas',  # Valores que se colocan en la tabla
            fill_value=0  # Rellenar con 0 donde no hay horas asignadas
        ).reset_index()

        # Evitar modificar las columnas de índice, solo renombrar las de las semanas
        df_pivot.columns.name = None  # Eliminar el nombre de la columna
        df_pivot.columns = [
            col[0] if isinstance(col, tuple) and col[0] == '' else (
                'Proyecto' if col[0] == 'proyecto__proyecto' else
                'Nombre Empleado' if col[0] == 'empleado__nombre' else
                'Rol Empleado' if col[0] == 'empleado__rol' else
                f'Semana {col[1]} Del Año {col[0]}'
            )
            for col in df_pivot.columns
        ]

        # Eliminar columnas vacías que puedan haberse generado
        df_pivot = df_pivot.loc[:, (df_pivot != 0).any(axis=0)]

        # Calcular el total de horas por empleado (suma por filas)
        df_pivot['Total Horas'] = df_pivot.loc[:, df_pivot.columns.str.startswith('Semana ')].sum(axis=1)

        # Calcular el total de horas por semana (suma por columnas)
        total_horas_por_semana = df_pivot.loc[:, df_pivot.columns.str.startswith('Semana ')].sum()

        # Crear la fila de totales generales (suma de todas las horas por columna)
        total_horas_fila = pd.DataFrame(data=[['', '', 'Total Horas'] + total_horas_por_semana.tolist() + [total_horas_por_semana.sum()]], columns=df_pivot.columns)

        # Concatenar los datos pivotados con la fila de totales
        df_final = pd.concat([df_pivot, total_horas_fila], ignore_index=True)

        # Crear el archivo Excel
        output = BytesIO()
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
    if not request.user.is_authenticated:
        return redirect(iniciar_sesion)
    
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
    if not request.user.is_authenticated:
        return redirect(iniciar_sesion)
    
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

# TERCERA TABLA
def asignaciones_data(request):
    if not request.user.is_authenticated:
        return redirect(iniciar_sesion)
    
    order_column = request.GET.get('order[0][column]', 0)
    order_dir = request.GET.get('order[0][dir]', 'asc')

    # Definir las columnas para ordenar
    columns = ['empleado__rol', 'empleado__nombre' ,'semana', 'total_horas']
    order_field = columns[int(order_column)]

    # Obtener el valor de búsqueda del DataTable
    search_value = request.GET.get('search[value]', '')

    # Agrupar las horas asignadas por rol y semana
    asignaciones_agrupadas = Asignacion.objects.values(
        'empleado__rol',  # Agrupar por rol
        'empleado__nombre',
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
    if not request.user.is_authenticated:
        return redirect(iniciar_sesion)
    
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
    
    try:
        parametro = Parametro.objects.get(nombre_parametro='asignacion.tipo')
        #print(parametro)
        tipo_horas = parametro.valor['valores_escenarios'][0]
    except Exception as e:
        tipo_horas = 'A2'
        
    if(tipo_horas == 'A1'):
        horas = 'horas optimistas.'
    elif(tipo_horas == 'A3'):
        horas = 'horas pesimistas.'
    else:
        horas = 'horas normales.'
    

    # Renderizar el template con las asignaciones paginadas
    data = {
        'asignaciones': page_obj,
        'num_pages': num_pages,
        'current_page': current_page,
        'page_range': page_range,
        'tipo_horas' : horas,
    }
    return render(request, 'core/asignaciones_list.html', data)



# Configuración de logging
logger = logging.getLogger(__name__)

def ejecutar_asignacion(request):
    if not request.user.is_authenticated:
        return redirect(iniciar_sesion)
    
    if request.method == 'POST':
        try:
            control, created = AsignacionControl.objects.get_or_create(id=1)  # Usa un único registro para controlar
            mensaje = ""

            if not created:
                # Si ya existe un registro, verifica si se realizó una ejecución hoy
                if control.fecha_ultimo_ejecucion == datetime.today():
                    logger.warning("Intento de ejecutar la asignación más de una vez en el mismo día.")
                    return HttpResponse("La asignación ya ha sido ejecutada hoy.", status=400)
                
            check_unasigned = obtener_proyectos_sin_asignar()
            if(not check_unasigned):
                logger.warning("Intento de ejecutar la asignación cuando no hay proyectos.")
                return HttpResponse("No existen proyectos para asignar. Verifique que se hayan subido los proyectos correctamente", status=400)
            
            if(check_unasigned.count() <=0):
                logger.warning("Intento de ejecutar la asignación cuando no hay proyectos")
                return HttpResponse("No existen proyectos para asignar. Verifique que se hayan subido los proyectos correctamente", status=400)

            empleados = Empleado.objects.all()
            if(empleados.count() <= 0):
                logger.warning('Intento de asignar recursos sin empleados obtenidos')
                return HttpResponse("Ha intentado realizar la asignación sin haber cargado empleados. "
                                    "Por favor, carque los empleados a través del menú Disponibilidad", status=400)

            # Ejecutar la asignación de recursos y capturar el mensaje de retorno
            realizar_asignacion = asignar_recursos()
            mensaje_asignacion = realizar_asignacion['mesg']
            
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
    if not request.user.is_authenticated:
        return redirect(iniciar_sesion)
    
    if request.method == 'POST':
        # Eliminar todas las asignaciones
        Asignacion.objects.all().delete()

        # Redirigir o devolver una respuesta de éxito
        return redirect('asignaciones_list')  # Redirige a la página de asignaciones

    return HttpResponse(status=405)  # Devuelve un error si no es un POST

#Que hacer si se acaban las horas? -> Tabla con resultado asignaciones?
# X cantidad de proyectos no fueron asignados por falta de horas
def asignar_recursos():
    """
    **Asigna recursos verificando si el usuario está disponible o no**\n
    **Parametros**\n
        parametros_necesario (tipo_dato): lore ipsum \n
    **Return**\n
        VariableReturn (tipo_dato): lore ipsum
    """
    
    mensaje = ""
    asignacion_realizada = False  # Para verificar si se realizó alguna asignación

    #Obtener todos los proyectos que no se hayan asignado anteriormente
    proyectos = obtener_proyectos_sin_asignar()
    
    hoy = date.today()
    anio_actual, semana_actual, _ = hoy.isocalendar()
    try:
        parametro = Parametro.objects.get(nombre_parametro='asignacion.tipo')
        tipo_horas = parametro.valor['valores_escenarios'][0]
    except Exception as e:
        tipo_horas = 'A2'
    cant_proyectos = 0
    
    if proyectos:
        for proyecto in proyectos:
            desfase_semanas = 0
            
            fecha_fin = proyecto.fechaFin
            
            if(fecha_fin < hoy):
                break
            
            #Verifica que el proyecto no inicie un fin de semana.
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
                semana_asignacion = ((semana_inicio + desfase_semanas) + i - 1) % 52 + 1  # Reiniciar el conteo al llegar a la semana 53
                if(semana_asignacion == 1):
                    anio += 1
                
                if(semana_asignacion < semana_actual and anio <= anio_actual):
                    print(f'Semana saltada: {semana_asignacion} del año {anio} \nDebido a estar antes del {semana_actual}/{anio_actual}')
                    continue
                

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
                    if(empleado == None):
                        while(True):
                            desfase_semanas += 1
                            semana_asignacion += 1
                            if semana_asignacion == 53:
                                semana_asignacion = 1
                                anio += 1
                            empleado = obtener_empleado(proyecto.id, horas.rol, semana_asignacion, anio, cant_horas)
                            if empleado:
                                break
                    Asignacion.objects.update_or_create(
                        proyecto = proyecto,
                        empleado = empleado,
                        semana = semana_asignacion,
                        anio = anio,
                        defaults={
                            'horas_asignadas': cant_horas,
                            'enviado': False
                            }
                    )
            cant_proyectos += 1
    
    if(cant_proyectos > 0):
        asignacion_realizada = True
                
    # Mensaje final de depuración
    if asignacion_realizada:
        respuesta = {
            'CantAsign':cant_proyectos, 
            'hecho':asignacion_realizada, 
            'mesg':"Asignación de recursos realizada con éxito."
            }
        return respuesta
    else:
        respuesta = {
            'CantAsign':cant_proyectos, 
            'hecho':asignacion_realizada, 
            'mesg': "No se pudo realizar la asignación. Verifique la disponibilidad de recursos y la demanda de horas."
            }
        return respuesta

    
##Junily Disponibilidad views.py.
def disponibilidad(request):
    if not request.user.is_authenticated:
        return redirect(iniciar_sesion)

    asignaciones = Asignacion.objects.select_related('empleado').order_by('anio', 'semana').all()
    empleados = Empleado.objects.all()
    semanas = range(1, 53)
    data = defaultdict(lambda: defaultdict(list)) #Agrupacion por semanas
    
    # Asignacion.objects.update_or_create(
    #     proyecto = proyectosAAgrupar.objects.get(id=459),
    #     empleado = Empleado.objects.get(id=3),
    #     semana = 24, #Cualquiera
    #     anio = 2025, #Cualquiera
    #     defaults={'horas_asignadas': 18}
    # )
    roles = ['Jefe de Proyectos', 'Ingeniero de Proyecto']
    
    hoy = date.today()
    anio, semana_actual, _ = hoy.isocalendar()
    
    for empleado in empleados:
        if empleado.rol not in roles:
            continue
        empleado_asignaciones = asignaciones.filter(empleado=empleado)
        anio_asignacion = anio
        
        for semana in semanas:
            semana_disponibilidad = (semana_actual + semana - 1) % 52 + 1
            if(semana_disponibilidad == 1):
                anio_asignacion += 1
            
            horas_asignadas = empleado_asignaciones.filter(semana=semana_disponibilidad, anio=anio_asignacion).aggregate(Sum('horas_asignadas'))['horas_asignadas__sum'] or 0
            horas_disponibles = empleado.horas_totales - horas_asignadas
            porcentaje_uso = round((horas_asignadas / empleado.horas_totales * 100)) if empleado.horas_totales > 0 else 0
            
            if porcentaje_uso <= 50.0:
                color = "bg-success"
            elif porcentaje_uso <= 75.0:
                color = "bg-warning"
            else:
                color = "bg-danger"

            #Determinar si la semana es nueva
            nueva = semana_disponibilidad in range(semana_actual - 1, semana_actual + 5)

            #Determinar si hubo cambios recientes
            cambio = False
            if data[empleado]['asignaciones']:
                ultima_semana = data[empleado]['asignaciones'][-1]
                if ultima_semana['porcentaje_uso'] != porcentaje_uso:
                    cambio = True
                
            data[empleado]['nombre'] = empleado.nombre
            data[empleado]['rol'] = empleado.rol
            data[empleado]['color'] = color
            data[empleado]['horas_totales'] = empleado.horas_totales
            data[empleado]['asignaciones'].append({
                'semana': semana_disponibilidad,
                'año': anio_asignacion,
                'horas_disponibles': horas_disponibles,
                'porcentaje_uso': porcentaje_uso,
                'color': color,
                'nueva': nueva,
                'cambio': cambio
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

