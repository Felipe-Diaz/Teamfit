from django.urls import path
from django.contrib.auth import views as auth_views

from .views import development_Buttons, llenar_DB, iniciar_sesion, crear_usuarios, graficar_Datos, pagina_principal, cerrar_sesion, subirProyectos, ver_proyectos, verHistorial, ver_usuarios, eliminarUsuarios
#asd
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
    path('eliminarUsuarios/<id>', eliminarUsuarios, name='eliminarUsuario')
]
