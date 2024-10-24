from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

from .views import iniciar_sesion, crear_usuarios, graficar_Datos, eliminar_historial
from .views import pagina_principal, cerrar_sesion, subirProyectos, ver_proyectos, verHistorial, consul_api
from .views import ver_usuarios, editar_usuario, eliminarUsuarios, ajuste_parametros, cluster, carga_Odoo, disponibilidad
from .views import asignaciones_data,eliminar_asignaciones, horas_por_proyecto_data, generar_excel_recursos
from .views import asignaciones_list, ejecutar_asignacion, generar_excel_asignacion, horas_por_recurso_data, generar_excel_proyectos, vista_carga_empleados

urlpatterns = [ 
    path('subirProyectos/',subirProyectos, name="subirProyectos"),
    path('subirProyectos/<upload>/',subirProyectos, name="decidirSubida"),
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
    path('cargaOdoo', carga_Odoo, name='cargaOdoo'),
    path('cargar_empleados/', vista_carga_empleados, name='cargar_empleados'),
    path('asignaciones/', asignaciones_list, name='asignaciones_list'),
    path('asignaciones/data/', asignaciones_data, name='asignaciones_data'),
    path('horas_por_recurso_data/', horas_por_recurso_data, name='horas_por_recurso_data'),
    path('horas_por_proyecto_data/', horas_por_proyecto_data, name='horas_por_proyecto_data'),
    path('disponibilidad/', disponibilidad, name='disponibilidad'),
    path('ejecutar_asignacion/', ejecutar_asignacion, name='ejecutar_asignacion'),
    path('eliminar-asignaciones/', eliminar_asignaciones, name='eliminar_asignaciones'),
    path('generar-reporte/', generar_excel_proyectos, name='generar_reporte'),
    path('generar-reporte2/', generar_excel_asignacion, name='generar_reporte2'),
    path('generar-reporte-recursos/', generar_excel_recursos, name='generar_excel_recursos'),
]
