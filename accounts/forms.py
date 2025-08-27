from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile
import logging

logger = logging.getLogger(__name__)


class ExtendedUserCreationForm(UserCreationForm):
    """Formulario de registro extendido con campos adicionales"""

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
            'placeholder': 'tu@email.com'
        }),
        help_text="Ingresa un email válido para recuperar tu contraseña si es necesario."
    )

    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
            'placeholder': 'Tu nombre'
        }),
        help_text="Tu nombre real."
    )

    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
            'placeholder': 'Tu apellido'
        }),
        help_text="Tu apellido."
    )

    tipo_usuario = forms.ChoiceField(
        choices=UserProfile.TIPO_USUARIO_CHOICES,
        initial='PARTICIPANTE',
        required=True,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent'
        }),
        help_text="Selecciona tu rol inicial. Puedes solicitar promoción más tarde."
    )

    codigo_invitacion = forms.CharField(
        max_length=10,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
            'placeholder': 'Código opcional'
        }),
        help_text="Si tienes un código de invitación, ingrésalo aquí (opcional)."
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Aplicar estilos a campos heredados
        self.fields['username'].widget.attrs.update({
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
            'placeholder': 'Nombre de usuario'
        })

        self.fields['password1'].widget.attrs.update({
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
            'placeholder': 'Contraseña segura'
        })

        self.fields['password2'].widget.attrs.update({
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
            'placeholder': 'Confirma tu contraseña'
        })

    def clean_email(self):
        """Validar que el email no esté en uso"""
        email = self.cleaned_data.get('email')
        if email:
            if User.objects.filter(email=email).exists():
                raise forms.ValidationError("Este email ya está registrado.")
        return email

    def clean_username(self):
        """Validación adicional para username"""
        username = self.cleaned_data.get('username')
        if username:
            # Verificar caracteres especiales no deseados
            if not username.replace('_', '').isalnum():
                raise forms.ValidationError(
                    "El nombre de usuario solo puede contener letras, números y guiones bajos."
                )
        return username

    def clean_codigo_invitacion(self):
        """Validar código de invitación si se proporciona"""
        codigo = self.cleaned_data.get('codigo_invitacion')
        if codigo:
            # Aquí puedes agregar lógica para validar códigos de invitación
            # Por ahora solo validamos el formato
            if len(codigo) < 3:
                raise forms.ValidationError("El código de invitación debe tener al menos 3 caracteres.")
        return codigo

    def save(self, commit=True):
        """Guardar usuario con información adicional"""
        try:
            user = super().save(commit=False)
            user.email = self.cleaned_data['email']
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']

            if commit:
                user.save()
                logger.info(f"Usuario creado exitosamente: {user.username}")

                # Crear o actualizar el perfil
                profile, created = UserProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'tipo_usuario': self.cleaned_data['tipo_usuario'],
                        'codigo_invitacion_usado': self.cleaned_data.get('codigo_invitacion', '')
                    }
                )

                if not created:
                    # Si el perfil ya existía (por el signal), actualizar los campos
                    profile.tipo_usuario = self.cleaned_data['tipo_usuario']
                    profile.codigo_invitacion_usado = self.cleaned_data.get('codigo_invitacion', '')
                    profile.save()
                    logger.info(f"Perfil actualizado para usuario {user.username}")
                else:
                    logger.info(f"Perfil creado manualmente para usuario {user.username}")

            return user

        except Exception as e:
            logger.error(f"Error guardando usuario: {str(e)}")
            raise forms.ValidationError(f"Error creando la cuenta: {str(e)}")


class UserProfileForm(forms.ModelForm):
    """Formulario para actualizar perfil de usuario"""

    class Meta:
        model = UserProfile
        fields = ['tipo_usuario']
        widgets = {
            'tipo_usuario': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Solo permitir cambio a ORGANIZADOR si cumple requisitos
        if self.instance and not self.instance.puede_solicitar_promocion:
            self.fields['tipo_usuario'].choices = [
                ('PARTICIPANTE', 'Participante'),
            ]


class SolicitudPromocionForm(forms.Form):
    """Formulario para solicitar promoción a organizador"""

    motivo = forms.CharField(
        max_length=500,
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
            'placeholder': 'Explica por qué quieres ser organizador...',
            'rows': 4
        }),
        help_text="Explica brevemente por qué deseas ser organizador (máximo 500 caracteres)."
    )

    def clean_motivo(self):
        motivo = self.cleaned_data.get('motivo')
        if motivo and len(motivo.strip()) < 10:
            raise forms.ValidationError("El motivo debe tener al menos 10 caracteres.")
        return motivo
