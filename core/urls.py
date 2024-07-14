from django.urls import path
from .views import index, development_Buttons, llenar_DB, newCreateJoinDB, create_additional_table, graficar_Datos #asd
urlpatterns = [ 
    path('',index, name="index"),
    path('b',development_Buttons, name="b"),
    path('llenar_db', llenar_DB, name='llenar_db'),
    path('newCreateJoinDB', newCreateJoinDB, name='newCreateJoinDB'),
    path('create_additional_table', create_additional_table, name='create_additional_table'),
    path('graficar_Datos', graficar_Datos, name='graficar_Datos')
]
