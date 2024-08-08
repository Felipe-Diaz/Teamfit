from django.urls import path
from django.contrib.auth import views as auth_views

from .views import index, development_Buttons, llenar_DB, iniciar_sesion, crear_usuarios, graficar_Datos, pagina_principal, cerrar_sesion #asd
urlpatterns = [ 
    path('',index, name="index"),
    path('b',development_Buttons, name="b"),
    path('llenar_db', llenar_DB, name='llenar_db'),
    path('login', iniciar_sesion, name="login"),
    path("crear_usuarios", crear_usuarios, name="crearUsuarios"),
    path('graficar_Datos', graficar_Datos, name='graficar_Datos'),
    path('index1', pagina_principal, name="index1"),
    path('logout', cerrar_sesion, name='logout')
]
