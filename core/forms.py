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
from django.core.exceptions import ValidationError

#Validaciones en Django Python
def validar_longitud_maxima(value):
    if len(str(value)) > 12:
        raise ValidationError('El número no puede tener más de 12 dígitos.')

def validar_longitud_maxima_nombres(value):
    if len(str(value)) > 100:
        raise ValidationError('El nombre del empelado no puede tener más de 100 caracteres.')

#Formulario de Ventas
class VentasForm(forms.Form):
    TIPOS_PROYECTO = [
        ("na", 'Seleccione Tipo de Proyecto'),
        ('1', 'Tipo 1'),
        ('2', 'Tipo 2'),
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
    
    HorasHombre = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control col-md-5 text-center mx-auto', 'placeholder': '5'}),
        decimal_places=1,
        max_digits=10
    )
    
    class Meta:
        fields = ['semana', 'HorasHombre']
       
#Formulario para subir archivos 

class UploadFileForm(forms.Form):
    file = forms.FileField( label='Selecciona un archivo CSV o XLSX',
                            help_text=' <br> Solo se permiten archivos CSV y XLSX',
                            widget=forms.ClearableFileInput(attrs={'accept': '.csv, .xlsx', 'class':'btn btn-primary'}))
    class Meta:
        fields = ['file']


#formulario para validar sesion
class LoginForm(forms.Form):
    username = forms.CharField(label='Usuario', max_length=100)
    password = forms.CharField(label='Contraseña', widget=forms.PasswordInput)
    
        
class CrearUsuarioAdmin(UserCreationForm):
    NUMRUT = forms.IntegerField(
                                label="Rut", 
                                required=True, 
                                validators=[validar_longitud_maxima],
                                widget=forms.NumberInput(attrs={'class':'form-control'})
                                )
    DVRUN = forms.CharField(
                            label="Dígito verificador",
                            required=True,
                            max_length=1,
                            widget=forms.TextInput(attrs={'class':'form-control'})
                            )
    fechaNacimiento = forms.DateField(
                                        label="Fecha de Nacimiento",
                                        required=True,
                                        widget=forms.DateInput(attrs={'class':'form-control'})
                                      )
    cargo = forms.CharField(
                            label="Cargo",
                            required=True,
                            max_length=150,
                            widget=forms.TextInput(attrs={'class':'form-control'})
                            )
    telefono = forms.IntegerField(
                                    label="Número de contacto",
                                    required=True,
                                    validators=[validar_longitud_maxima],
                                    widget=forms.NumberInput(attrs={'class':'form-control'})
                                  )
    class Meta:
        model = User
        fields = ['username', 'first_name','last_name', 'email', 'is_staff', 'NUMRUT', 'DVRUN','fechaNacimiento','cargo','telefono']

class AsignadorHHForm(forms.Form):
    id_empleado= forms.IntegerField(
        label="id del empleado",
        required=True)
    
    nombre_empleado= forms.CharField(
        label="Nombre del empleado",
        required=True,
        max_length = 100,
        validators=[validar_longitud_maxima_nombres],
        widget=forms.TextInput(attrs={'class':'form-control'})
    )

    cargo=forms.CharField(
        label="Cargo o Rol del empleado",
        required=True,
        max_length = 100,
        widget=forms.TextInput(attrs={'class':'form-control'})
    )

    telefono=forms.CharField(
        label="Numero del empleado",
        required=True,
        max_length = 100,
        validators=[validar_longitud_maxima],
        widget=forms.TextInput(attrs={'class':'form-control'}))
    
    id_categoria = forms.IntegerField(
        label="Categoria del empleado",
        required=True)
    
    id_proyecto = forms.IntegerField(
        label="id del proyecto",
        required=True)
    
    horas_empleado = forms.IntegerField(
        label="Horario de trabajo del empleado",
        required=True
    )
    horas_dis_empleado = forms.IntegerField(
        label="Horario del trabajo del empleado Disponible",
        required=True
    )

#Agregar nuevo formulario para ingresar los nuevos valores del modelo Proyectos.