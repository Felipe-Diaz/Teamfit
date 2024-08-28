from django.urls import path
from django.contrib.auth import views as auth_views

from .views import development_Buttons, llenar_DB, iniciar_sesion, crear_usuarios, graficar_Datos 
from .views import pagina_principal, cerrar_sesion, subirProyectos, ver_proyectos, verHistorial
from .views import ver_usuarios, eliminarUsuarios, ajuste_parametros
from .views import eliminar_historial

#Se indican las distintas URL para el sistema.
##A la izquierda es el valor que aparecerá en la URL
##En el centro se llama a la función que renderiza la página
##A la derecha se indica el nombre para llamar dentro el código

urlpatterns = [ 
    path('subirProyectos',subirProyectos, name="subirProyectos"),
    path('subirProyectos/<upload>',subirProyectos, name="decidirSubida"),
    path('b',development_Buttons, name="b"),
    path('llenar_db', llenar_DB, name='llenar_db'),
    path('login', iniciar_sesion, name="login"),
    path("historial", verHistorial, name="historial"),
    path("crearUsuarios", crear_usuarios, name="crearUsuarios"),
    path('graficar_Datos', graficar_Datos, name='graficar_Datos'),
    path('', pagina_principal, name="index"),
    path('logout', cerrar_sesion, name='logout'),
    path('verProyectos', ver_proyectos, name='verProyectos'),
    path('verUsuarios', ver_usuarios, name='verUsuarios'),
    path('eliminarUsuarios/<id>', eliminarUsuarios, name='eliminarUsuario'),
    path('parametros', ajuste_parametros, name="parametros"),
    path('eliminar_historial', eliminar_historial, name='eliminar_historial'),
]
