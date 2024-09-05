from dataclasses import field
from msilib.schema import CheckBox
from pyexpat import model
from django import forms
from django.forms import ModelForm, fields, Form
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from pkg_resources import require
from .models import Ventas, Disponibilidad, PerfilUsuario
from datetime import date, timedelta
from django.core.exceptions import ValidationError
from django import forms

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
                            widget=forms.ClearableFileInput(attrs={
                            'accept': '.csv, .xlsx',
                            'class':'custom-button',
                            'style': 'background-color: var(--junily-white);',
                            'placeholder': 'Selecciona un archivo'}))
    class Meta:
        fields = ['file']


#formulario para validar sesion
class LoginForm(forms.Form):
    username = forms.CharField(label='Usuario', max_length=100)
    password = forms.CharField(label='Contraseña', widget=forms.PasswordInput)
    
        
class CrearUsuarioAdmin(UserCreationForm):
    CARGOS = [
        ("na", 'Seleccione Cargo'),
        ('1', 'Administrador'),
        ('2', 'Jefe de Proyecto'),
        ('3', 'Ingenierio de Proyecto'),
    ]
    cargo = forms.ChoiceField(
        required=True,
        choices=CARGOS,
        widget=forms.Select(attrs={'class':'form-control'}),
        label="Cargo"
    )
    def clean_cargo(self):
        cargo = self.cleaned_data.get('cargo')
        if cargo == "na":
            raise ValidationError("Debe seleccionar un cargo válido.")
        return cargo
    username = forms.CharField(
                            label="Usuario",
                            required=True,
                            max_length=150,
                            widget=forms.TextInput(attrs={'class':'form-control'})
                            )
    first_name = forms.CharField(
                            label="Nombre",
                            required=True,
                            max_length=150,
                            widget=forms.TextInput(attrs={'class':'form-control'})
                            )
    last_name = forms.CharField(
                            label="Apellidos",
                            required=True,
                            max_length=150,
                            widget=forms.TextInput(attrs={'class':'form-control'})
                            )
    email = forms.CharField(
                            label="Correo electrónico",
                            required=True,
                            max_length=150,
                            widget=forms.TextInput(attrs={'class':'form-control'})
                            )
    FIELD_LABELS={
        'username':'Usuario',
        'cargo':'Cargo',
        'first_name':'Nombre',
        'last_name':'Apellido',
        'email':'Correo electrónico',
        'password1':'Contraseña',
        'password2':'Contraseña (Confirmación)'
    }
    class Meta:
        model = User
        fields = ['username', 'first_name','last_name', 'email', 'is_staff', 'cargo']
        labels = {'is_staff':'Administrador',}


class UsuarioForm(forms.ModelForm):
    CARGOS = [
        ("na", 'Seleccione Cargo'),
        ('1', 'Administrador'),
        ('2', 'Jefe de Proyecto'),
        ('3', 'Ingenierio de Proyecto'),
    ]
    cargo = forms.ChoiceField(
        required=True,
        choices=CARGOS,
        widget=forms.Select(attrs={'class':'form-control'}),
        label="Cargo"
    )
    def clean_cargo(self):
        cargo = self.cleaned_data.get('cargo')
        if cargo == "na":
            raise ValidationError("Debe seleccionar un cargo válido.")
        return cargo
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'cargo', 'is_active']

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
        
        

CATEGORIAS_MAPPING = {
    'A': 'autenticacion',
    'A1': 'login',
    'A2': 'logout',
    'B': 'configuracion',
    'B1': 'cambio_parametros',
    'B2': 'cambio_conf_bd',
    'C': 'mantenimiento',
    'C1': 'limpieza_datos',
    'D':'error',
    'D1': 'errores_sistema',
    'E': 'auditoria',
    'E1': 'quien_agrego_documentos',
    'E2': 'quien_agrego_usuario',
    'E3': 'quien_elimino_usuario',
    'F': 'seguridad',
    'F1': 'cambio_de_cargo',
    'F2': 'actualizacion_permisos',
    'G': 'modelo',
    'G1': 'realizacion_clusterizacion',
}

class CategoriasForm(forms.Form):
    # Autentificación
    autenticacion = forms.BooleanField(
        required=False, 
        label="Autentificación", 
        widget=forms.CheckboxInput(attrs={'class':'form-check-input'})
        )
    
    login = forms.BooleanField(
        label='Login',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    logout = forms.BooleanField(
        required=False, 
        label="Logout",
        widget=forms.CheckboxInput(attrs={'class':'form-check-input'})
        )
    #logout_exp_token = forms.BooleanField(required=False, label="Logout por expiración de token")
    #error_ingreso = forms.BooleanField(required=False, label="Error al ingresar contraseña")

    # Configuración
    configuracion = forms.BooleanField(required=False, label="Configuración", widget=forms.CheckboxInput(attrs={'class':'form-check-input'}))
    cambio_parametros = forms.BooleanField(required=False, label="Cambio de Parametros", widget=forms.CheckboxInput(attrs={'class':'form-check-input'}))
    cambio_conf_bd = forms.BooleanField(required=False, label="Cambio de Configuraciones de la Base de Datos", widget=forms.CheckboxInput(attrs={'class':'form-check-input'}))

    # Mantenimiento
    mantenimiento = forms.BooleanField(required=False, label="Mantenimiento", widget=forms.CheckboxInput(attrs={'class':'form-check-input'}))
    limpieza_datos = forms.BooleanField(required=False, label="Limpieza de datos", widget=forms.CheckboxInput(attrs={'class':'form-check-input'}))
    #actualizacion_sistema = forms.BooleanField(required=False, label="Actualizaciones del sistema")
    #copias_seguridad = forms.BooleanField(required=False, label="Copias de seguridad")

    # Error
    error = forms.BooleanField(required=False, label="Error", widget=forms.CheckboxInput(attrs={'class':'form-check-input'}))
    errores_sistema = forms.BooleanField(required=False, label="Errores del Sistema", widget=forms.CheckboxInput(attrs={'class':'form-check-input'}))
    
    # Auditoría
    auditoria = forms.BooleanField(required=False, label="Auditoría", widget=forms.CheckboxInput(attrs={'class':'form-check-input'}))
    quien_agrego_documentos = forms.BooleanField(required=False, label="Quien agregó documentos", widget=forms.CheckboxInput(attrs={'class':'form-check-input'}))
    quien_agrego_usuario = forms.BooleanField(required=False, label="Quién agregó usuario", widget=forms.CheckboxInput(attrs={'class':'form-check-input'}))
    quien_elimino_usuario = forms.BooleanField(required=False, label="Quien eliminó usuario", widget=forms.CheckboxInput(attrs={'class':'form-check-input'}))
    
    # Seguridad
    seguridad = forms.BooleanField(required=False, label="Seguridad", widget=forms.CheckboxInput(attrs={'class':'form-check-input'}))
    #cambio_contraseña = forms.BooleanField(required=False, label="Cambio de contraseña")
    cambio_de_cargo = forms.BooleanField(required=False, label="Cambio de Cargo", widget=forms.CheckboxInput(attrs={'class':'form-check-input'}))
    actualizacion_permisos = forms.BooleanField(required=False, label="Actualización de Permisos", widget=forms.CheckboxInput(attrs={'class':'form-check-input'}))
    
    # Modelo
    modelo = forms.BooleanField(required=False, label="Modelo", widget=forms.CheckboxInput(attrs={'class':'form-check-input'}))
    realizacion_clusterizacion = forms.BooleanField(required=False, label="Realización de la clusterización", widget=forms.CheckboxInput(attrs={'class':'form-check-input'}))
    
    def get_field_by_code(self, code):
        field_name = CATEGORIAS_MAPPING.get(code)
        if field_name:
            return self[field_name]
        return None
    


