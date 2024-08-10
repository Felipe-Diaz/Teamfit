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


#Agregar nuevo formulario para ingresar los nuevos valores del modelo Proyectos.
class proyectosForm(forms.Form):
    
    idProy = forms.CharField(
        label="ID Proyecto",
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control text-center mx-auto'})
    )
    
    proyecto = forms.CharField(
        label="Proyecto",
        required=True,
        max_length=12,
        widget=forms.TextInput(attrs={'class': 'form-control text-center mx-auto'})
    )
    
    lineaNegocio = forms.CharField(
        label="Linea de Negocio",
        required=True,
        max_length=6,
        widget=forms.TextInput(attrs={'class': 'form-control text-center mx-auto'})
    )
    
    tipo = forms.CharField(
        label="Tipo Proyecto",
        required=True,
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control text-center mx-auto'})
    )
    
    usoAgencia = forms.BooleanField(
        label="Participación de Agencia Energética",
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input mx-auto col-lg-12'})
    )
    
    ocupacionInicio = forms.DecimalField(
        label="Ocupación de personal",
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control text-center mx-auto'})
    )
    
    class Meta:
        fields = ['idProy', 'proyecto', 'lineaNegocio', 'tipo', 'usoAgencia', 'ocupacionInicio']