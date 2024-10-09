from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

from .views import development_Buttons, llenar_DB, iniciar_sesion, crear_usuarios, graficar_Datos 
from .views import pagina_principal, cerrar_sesion, subirProyectos, ver_proyectos, verHistorial
from .views import ver_usuarios, editar_usuario, eliminarUsuarios, ajuste_parametros
from .views import eliminar_historial, consul_api, cluster

from .views import asignaciones_data,eliminar_asignaciones
from .views import asignaciones_list, ejecutar_asignacion, asignaciones_list
from .views import disponibilidad
from .views import (subirProyectos,
    pagina_principal,
    ver_proyectos,
    asignaciones_list,
    ejecutar_asignacion,
    generar_excel_proyectos,
    generar_excel_asignacion,
    eliminar_asignaciones,
    asignaciones_data,
    horas_por_recurso_data,
    horas_por_proyecto_data,
    generar_excel_recursos,
    asignar_recursos)
#Se indican las distintas URL para el sistema.
##A la izquierda es el valor que aparecerá en la URL
##En el centro se llama a la función que renderiza la página
##A la derecha se indica el nombre para llamar dentro el código

urlpatterns = [ 
    path('subirProyectos/',subirProyectos, name="subirProyectos"),
    path('subirProyectos/<upload>/',subirProyectos, name="decidirSubida"),
    path('b',development_Buttons, name="b"),
    path('llenar_db', llenar_DB, name='llenar_db'),
    path('login', iniciar_sesion, name="login"),
    path("historial", verHistorial, name="historial"),
    path("crearUsuarios", crear_usuarios, name="crearUsuarios"),
    path('graficar_Datos', graficar_Datos, name='graficar_Datos'),
    path('', pagina_principal, name="index"),
    path('logout', cerrar_sesion, name='logout'),
    path('verProyectos/', ver_proyectos, name='verProyectos'),
    path('verUsuarios', ver_usuarios, name='verUsuarios'),
    path('editarUsuarios/<id>', editar_usuario, name='editarUsuario'),
    path('eliminarUsuarios/<id>', eliminarUsuarios, name='eliminarUsuario'),
    path('parametros', ajuste_parametros, name="parametros"),
    path('eliminar_historial', eliminar_historial, name='eliminar_historial'),
    path('consul_api', consul_api, name='consul_api'),
    path('cluster', cluster, name='cluster'),

    ###Ingresar las URLS del grupo 2 desde acá hacia abajo.
    path('asignaciones/', asignaciones_list, name='asignaciones_list'),
    path('asignaciones/data/', asignaciones_data, name='asignaciones_data'),
    path('horas_por_recurso_data/', horas_por_recurso_data, name='horas_por_recurso_data'),
    path('horas_por_proyecto_data/', horas_por_proyecto_data, name='horas_por_proyecto_data'),

    # Vistas nuevas para los reportes adicionales
    path('disponibilidad/', disponibilidad, name='disponibilidad'),

    # Acciones sobre las asignaciones y generación de reportes
    path('ejecutar_asignacion/', ejecutar_asignacion, name='ejecutar_asignacion'),
    path('eliminar-asignaciones/', eliminar_asignaciones, name='eliminar_asignaciones'),
    path('generar-reporte/', generar_excel_proyectos, name='generar_reporte'),
    path('generar-reporte2/', generar_excel_asignacion, name='generar_reporte2'),
    path('generar-reporte-recursos/', generar_excel_recursos, name='generar_excel_recursos'),
]
