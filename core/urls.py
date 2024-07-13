from django.urls import path
from .views import index, development_Buttons #asd
urlpatterns = [ 
    path('',index, name="index"),
    path('b',development_Buttons, name="b"),
]
