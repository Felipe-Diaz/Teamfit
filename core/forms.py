from dataclasses import field
from msilib.schema import CheckBox
from pyexpat import model
from django import forms
from django.forms import ModelForm, fields, Form
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from pkg_resources import require
from .models import Ventas, Disponibilidad

class VentasForm(ModelForm):
    class Meta:
        model = Ventas
        fields = ['id', 'idTipoProyecto', 'fecha']

class DispForm(ModelForm):
    class Meta:
        model = Disponibilidad
        fields = ['semana', 'hh']
        