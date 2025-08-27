from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from .models import UserProfile
from .forms import ExtendedUserCreationForm
import logging

logger = logging.getLogger(__name__)


class RegistroView(CreateView):
    """Vista para registro de nuevos usuarios con formulario extendido"""
    form_class = ExtendedUserCreationForm
    template_name = 'registration/registro.html'
    success_url = reverse_lazy('quinielas:home')

    def form_valid(self, form):
        """Procesar formulario válido con transacción atómica"""
        try:
            with transaction.atomic():
                # Guardar el usuario (el formulario maneja la creación del perfil)
                response = super().form_valid(form)

                # Verificar que el perfil se creó correctamente
                user = self.object

                # Dar tiempo para que el signal procese
                user.refresh_from_db()

                if not hasattr(user, 'profile'):
                    # Fallback: crear perfil manualmente si el signal falló
                    profile = UserProfile.objects.create(
                        user=user,
                        tipo_usuario=form.cleaned_data.get('tipo_usuario', 'PARTICIPANTE'),
                        codigo_invitacion_usado=form.cleaned_data.get('codigo_invitacion', '')
                    )
                    logger.warning(f"Perfil creado manualmente como fallback para {user.username}")

                # Iniciar sesión automáticamente
                login(self.request, user)

                # Mensaje de éxito personalizado
                tipo_display = user.profile.get_tipo_usuario_display()
                messages.success(
                    self.request,
                    f'¡Bienvenido {user.first_name or user.username}! '
                    f'Tu cuenta ha sido creada como {tipo_display}. '
                    f'¡Ya puedes comenzar a participar en quinielas!'
                )

                logger.info(f"Registro exitoso para usuario {user.username} como {user.profile.tipo_usuario}")
                return response

        except Exception as e:
            logger.error(f"Error en registro de usuario: {str(e)}")
            messages.error(
                self.request,
                'Hubo un problema al crear tu cuenta. Por favor, inténtalo de nuevo.'
            )
            return self.form_invalid(form)

    def form_invalid(self, form):
        """Manejo mejorado de formulario inválido"""
        logger.warning(f"Intento de registro fallido: {form.errors}")
        messages.error(
            self.request,
            'Por favor, corrige los errores en el formulario.'
        )
        return super().form_invalid(form)

    def get(self, request, *args, **kwargs):
        """Redirigir si ya está autenticado"""
        if request.user.is_authenticated:
            messages.info(request, 'Ya tienes una cuenta activa.')
            return redirect('quinielas:home')
        return super().get(request, *args, **kwargs)


@login_required
def logout_view(request):
    """Vista personalizada para logout"""
    username = request.user.username
    logout(request)
    messages.success(request, f'¡Hasta luego {username}! Has cerrado sesión exitosamente.')
    return redirect('quinielas:home')
