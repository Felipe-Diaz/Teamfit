from dataclasses import field
from msilib.schema import CheckBox
from pyexpat import model
from django import forms
from django.forms import ModelForm, fields, Form
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from pkg_resources import require
from .models import Ventas, Disponibilidad
from datetime import date, timedelta


#Formulario de Ventas
class VentasForm(forms.Form):
    TIPOS_PROYECTO = [
        ("na", 'Seleccione Tipo de Proyecto'),
        ('tipo_1', 'Tipo 1'),
        ('tipo_2', 'Tipo 2'),
        ('na', 'No Aplica'),
    ]

    idTipoProyecto = forms.ChoiceField(
        required=False,
        choices=TIPOS_PROYECTO,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Tipo de Proyecto"
    )

    fecha = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Fecha",
    )

    class Meta:
        fields = ['idTipoProyecto', 'fecha']

    def clean_fecha(self):
        fecha = self.cleaned_data['fecha']
        if fecha < date.today() + timedelta(days=1):
            raise forms.ValidationError("La fecha debe ser desde mañana en adelante.")
        return fecha

#Formulario de Disponibilidad
##Idea: Calcular las semanas en base a las fechas que se utilizarán.
class DispForm(forms.Form):
    
    semana = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control col-md-5 text-center mx-auto', 'placeholder': '31'}),
    )
    
    HorasHombre = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control col-md-5 text-center mx-auto', 'placeholder': '5'}),
    )
    
    class Meta:
        fields = ['semana', 'HorasHombre']
       
#Formulario para subir archivos 
#######
class UploadFileForm(forms.Form):
    file = forms.FileField()