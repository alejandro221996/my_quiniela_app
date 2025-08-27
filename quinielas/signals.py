"""
Signals para invalidación automática de cache
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Apuesta, Participante, Quiniela
from .cache_optimizations import invalidar_cache_usuario, invalidar_cache_global


@receiver(post_save, sender=Apuesta)
def invalidar_cache_apuesta(sender, instance, created, **kwargs):
    """Invalida cache cuando se crea o actualiza una apuesta"""
    if instance.participante and instance.participante.usuario:
        invalidar_cache_usuario(instance.participante.usuario.id)
    
    # Si es una nueva apuesta, también invalidar ranking global
    if created:
        invalidar_cache_global()


@receiver(post_delete, sender=Apuesta)
def invalidar_cache_apuesta_delete(sender, instance, **kwargs):
    """Invalida cache cuando se elimina una apuesta"""
    if instance.participante and instance.participante.usuario:
        invalidar_cache_usuario(instance.participante.usuario.id)
    invalidar_cache_global()


@receiver(post_save, sender=Participante)
def invalidar_cache_participante(sender, instance, created, **kwargs):
    """Invalida cache cuando se crea o actualiza un participante"""
    if instance.usuario:
        invalidar_cache_usuario(instance.usuario.id)
    
    # Si es un nuevo participante, invalidar ranking global
    if created:
        invalidar_cache_global()


@receiver(post_delete, sender=Participante)
def invalidar_cache_participante_delete(sender, instance, **kwargs):
    """Invalida cache cuando se elimina un participante"""
    if instance.usuario:
        invalidar_cache_usuario(instance.usuario.id)
    invalidar_cache_global()


@receiver(post_save, sender=Quiniela)
def invalidar_cache_quiniela(sender, instance, created, **kwargs):
    """Invalida cache cuando se crea o actualiza una quiniela"""
    # Si cambia el estado de activa, puede afectar datos generales
    if not created and 'activa' in getattr(instance, '_dirty_fields', []):
        invalidar_cache_global()
