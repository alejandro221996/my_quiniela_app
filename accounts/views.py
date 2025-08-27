from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth.decorators import login_required
from .models import UserProfile


class RegistroView(CreateView):
    """Vista para registro de nuevos usuarios"""
    form_class = UserCreationForm
    template_name = 'registration/registro.html'
    success_url = reverse_lazy('quinielas:home')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Configurar el tipo de usuario como ORGANIZADOR para registro directo
        if hasattr(self.object, 'profile'):
            self.object.profile.tipo_usuario = 'ORGANIZADOR'
            self.object.profile.save()
        else:
            UserProfile.objects.create(user=self.object, tipo_usuario='ORGANIZADOR')
        
        # Iniciar sesión automáticamente después del registro
        login(self.request, self.object)
        messages.success(
            self.request, 
            f'¡Bienvenido {self.object.username}! Tu cuenta ha sido creada como Organizador. ¡Ya puedes crear quinielas!'
        )
        return response
    
    def get(self, request, *args, **kwargs):
        # Redirigir si ya está autenticado
        if request.user.is_authenticated:
            return redirect('quinielas:home')
        return super().get(request, *args, **kwargs)


@login_required
def logout_view(request):
    """Vista personalizada para logout"""
    username = request.user.username
    logout(request)
    messages.success(request, f'¡Hasta luego {username}! Has cerrado sesión exitosamente.')
    return redirect('quinielas:home')
