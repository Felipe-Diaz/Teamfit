from django.urls import path
from .views import index, development_Buttons, llenar_DB, join_DB #asd
urlpatterns = [ 
    path('',index, name="index"),
    path('b',development_Buttons, name="b"),
    path('llenar_db', llenar_DB, name='llenar_db'),
    path('join_DB', join_DB, name='join_DB')
]
