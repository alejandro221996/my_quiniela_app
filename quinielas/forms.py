from django import forms
from django.utils import timezone
from .models import Quiniela, Apuesta


class QuinielaForm(forms.ModelForm):
    """Formulario para crear una quiniela"""
    
    class Meta:
        model = Quiniela
        fields = ['nombre', 'descripcion', 'fecha_limite']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'Nombre de la quiniela'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'rows': 3,
                'placeholder': 'Descripción opcional'
            }),
            'fecha_limite': forms.DateTimeInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'type': 'datetime-local'
            }),
        }
        labels = {
            'nombre': 'Nombre de la Quiniela',
            'descripcion': 'Descripción',
            'fecha_limite': 'Fecha Límite para Apostar',
        }
    
    def clean_fecha_limite(self):
        fecha_limite = self.cleaned_data['fecha_limite']
        if fecha_limite <= timezone.now():
            raise forms.ValidationError("La fecha límite debe ser en el futuro.")
        return fecha_limite


class UnirseQuinielaForm(forms.Form):
    """Formulario para unirse a una quiniela con código de acceso"""
    codigo_acceso = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'placeholder': 'Ingresa el código de acceso',
            'style': 'text-transform: uppercase;'
        }),
        label='Código de Acceso'
    )
    
    def clean_codigo_acceso(self):
        codigo = self.cleaned_data['codigo_acceso'].upper().strip()
        if len(codigo) != 6:
            raise forms.ValidationError("El código debe tener 6 caracteres.")
        return codigo


class ApuestaForm(forms.Form):
    """Formulario para realizar apuestas"""
    goles_local = forms.IntegerField(
        min_value=0,
        max_value=20,
        widget=forms.NumberInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'min': '0',
            'max': '20'
        }),
        label='Goles Equipo Local'
    )
    
    goles_visitante = forms.IntegerField(
        min_value=0,
        max_value=20,
        widget=forms.NumberInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'min': '0',
            'max': '20'
        }),
        label='Goles Equipo Visitante'
    )


class ResultadoPartidoForm(forms.ModelForm):
    """Formulario para que los administradores ingresen resultados"""
    
    class Meta:
        model = Quiniela  # Se usará para validar el partido
        fields = []
    
    goles_local = forms.IntegerField(
        min_value=0,
        max_value=50,
        widget=forms.NumberInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'min': '0',
            'max': '50'
        }),
        label='Goles Equipo Local'
    )
    
    goles_visitante = forms.IntegerField(
        min_value=0,
        max_value=50,
        widget=forms.NumberInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
            'min': '0',
            'max': '50'
        }),
        label='Goles Equipo Visitante'
    )
