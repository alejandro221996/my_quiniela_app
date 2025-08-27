from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import logging

logger = logging.getLogger(__name__)

class UserProfile(models.Model):
    """Perfil extendido del usuario con información adicional"""

    TIPO_USUARIO_CHOICES = [
        ('PARTICIPANTE', 'Participante'),
        ('ORGANIZADOR', 'Organizador'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    tipo_usuario = models.CharField(
        max_length=20,
        choices=TIPO_USUARIO_CHOICES,
        default='PARTICIPANTE'
    )
    fecha_promocion = models.DateTimeField(null=True, blank=True)
    codigo_invitacion_usado = models.CharField(max_length=10, null=True, blank=True)
    apuestas_realizadas = models.IntegerField(default=0)
    promocion_solicitada = models.BooleanField(default=False)
    fecha_solicitud_promocion = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_tipo_usuario_display()}"

    @property
    def puede_crear_quinielas(self):
        """Verifica si el usuario puede crear quinielas"""
        return self.tipo_usuario == 'ORGANIZADOR'

    @property
    def puede_solicitar_promocion(self):
        """Verifica si puede solicitar promoción a organizador"""
        return (
            self.tipo_usuario == 'PARTICIPANTE' and
            not self.promocion_solicitada and
            self.apuestas_realizadas >= 5  # Criterio mínimo
        )

    def promover_a_organizador(self):
        """Promociona al usuario a organizador"""
        from django.utils import timezone
        self.tipo_usuario = 'ORGANIZADOR'
        self.fecha_promocion = timezone.now()
        self.promocion_solicitada = False
        self.save()

    def solicitar_promocion(self):
        """Solicita promoción a organizador"""
        from django.utils import timezone
        self.promocion_solicitada = True
        self.fecha_solicitud_promocion = timezone.now()
        self.save()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Crear perfil automáticamente cuando se crea un usuario"""
    if created:
        try:
            # Verificar si ya existe un perfil
            if not hasattr(instance, 'profile'):
                profile = UserProfile.objects.create(
                    user=instance,
                    tipo_usuario='PARTICIPANTE'  # Por defecto
                )
                logger.info(f"Perfil creado para usuario {instance.username} - ID: {profile.id}")
            else:
                logger.warning(f"El perfil ya existe para usuario {instance.username}")
        except Exception as e:
            logger.error(f"Error creando perfil para usuario {instance.username}: {str(e)}")
            # Re-lanzar la excepción para que no pase silenciosamente
            raise e
