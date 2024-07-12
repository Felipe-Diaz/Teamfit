from django.urls import path
from .views import index #asd
urlpatterns = [ 
    path('',index, name="index"),
]