from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.utils.text import slugify
import string
import random


class Quiniela(models.Model):
    """Modelo para representar una quiniela"""
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    codigo_acceso = models.CharField(max_length=10, unique=True, editable=False)
    creador = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quinielas_creadas')
    fecha_limite = models.DateTimeField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    activa = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Quiniela"
        verbose_name_plural = "Quinielas"
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return self.nombre
    
    def save(self, *args, **kwargs):
        if not self.codigo_acceso:
            self.codigo_acceso = self.generar_codigo_unico()
        super().save(*args, **kwargs)
    
    def generar_codigo_unico(self):
        """Genera un código único de 6 caracteres alfanuméricos"""
        while True:
            codigo = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if not Quiniela.objects.filter(codigo_acceso=codigo).exists():
                return codigo
    
    @property
    def puede_apostar(self):
        """Verifica si aún se puede apostar en esta quiniela"""
        return timezone.now() < self.fecha_limite and self.activa
    
    def total_participantes(self):
        """Retorna el número total de participantes"""
        return self.participantes.count()
    
    def get_slug(self):
        """Genera un slug amigable para URLs"""
        return f"{slugify(self.nombre)}-{self.codigo_acceso.lower()}"
    
    def get_absolute_url(self):
        """URL absoluta de la quiniela"""
        from django.urls import reverse
        return reverse('quinielas:detalle_slug', kwargs={'slug': self.get_slug()})


class Participante(models.Model):
    """Modelo para representar la participación de un usuario en una quiniela"""
    
    # Estados de participante
    ESTADOS_PARTICIPANTE = [
        ('PENDIENTE', 'Pendiente de pago'),
        ('PAGADO', 'Pagado y activo'),
        ('SUSPENDIDO', 'Suspendido temporalmente'),
        ('ELIMINADO', 'Eliminado de la quiniela'),
    ]
    
    # Información básica
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    quiniela = models.ForeignKey(Quiniela, on_delete=models.CASCADE, related_name='participantes')
    fecha_union = models.DateTimeField(auto_now_add=True)
    puntos_totales = models.IntegerField(default=0)
    
    # Gestión de participante
    estado = models.CharField(
        max_length=20, 
        choices=ESTADOS_PARTICIPANTE, 
        default='PENDIENTE',
        help_text="Estado actual del participante"
    )
    fecha_pago = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Fecha en que se registró el pago"
    )
    monto_pagado = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Monto pagado por el participante"
    )
    metodo_pago = models.CharField(
        max_length=50, 
        blank=True,
        help_text="Método de pago utilizado (efectivo, transferencia, etc.)"
    )
    notas_admin = models.TextField(
        blank=True,
        help_text="Notas privadas del administrador sobre este participante"
    )
    
    # Timestamps
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    actualizado_por = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='participantes_gestionados',
        help_text="Usuario que realizó la última actualización"
    )
    
    class Meta:
        unique_together = ('usuario', 'quiniela')
        verbose_name = "Participante"
        verbose_name_plural = "Participantes"
        ordering = ['-puntos_totales', 'fecha_union']
    
    def __str__(self):
        return f"{self.usuario.username} en {self.quiniela.nombre} ({self.get_estado_display()})"
    
    @property
    def puede_apostar(self):
        """Determina si el participante puede realizar apuestas"""
        return self.estado == 'PAGADO'
    
    @property
    def dias_desde_union(self):
        """Días transcurridos desde que se unió"""
        from django.utils import timezone
        return (timezone.now() - self.fecha_union).days
    
    @property
    def esta_al_dia(self):
        """Verifica si el participante está al día con sus pagos"""
        return self.estado in ['PAGADO']
    
    @property
    def total_apuestas(self):
        """Total de apuestas realizadas por el participante"""
        return self.apuestas.count()
    
    def marcar_como_pagado(self, monto, metodo_pago, admin_user):
        """Marca al participante como pagado"""
        from django.utils import timezone
        self.estado = 'PAGADO'
        self.fecha_pago = timezone.now()
        self.monto_pagado = monto
        self.metodo_pago = metodo_pago
        self.actualizado_por = admin_user
        self.save()
    
    def suspender(self, razon, admin_user):
        """Suspende al participante"""
        self.estado = 'SUSPENDIDO'
        self.notas_admin = f"Suspendido: {razon}"
        self.actualizado_por = admin_user
        self.save()
    
    def reactivar(self, admin_user):
        """Reactiva al participante"""
        if self.fecha_pago:
            self.estado = 'PAGADO'
        else:
            self.estado = 'PENDIENTE'
        self.actualizado_por = admin_user
        self.save()
    
    def calcular_puntos_totales(self):
        """Calcula y actualiza los puntos totales del participante"""
        total = sum(apuesta.puntos for apuesta in self.apuestas.all())
        self.puntos_totales = total
        self.save()
        return total


class Equipo(models.Model):
    """Modelo para representar equipos"""
    nombre = models.CharField(max_length=50)
    nombre_corto = models.CharField(max_length=10)
    logo = models.ImageField(upload_to='equipos/', blank=True, null=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Equipo"
        verbose_name_plural = "Equipos"
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre


class Jornada(models.Model):
    """Modelo para representar jornadas o fechas de partidos"""
    nombre = models.CharField(max_length=50)
    numero = models.IntegerField()
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    activa = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Jornada"
        verbose_name_plural = "Jornadas"
        ordering = ['numero']
    
    def __str__(self):
        return f"Jornada {self.numero} - {self.nombre}"


class Partido(models.Model):
    """Modelo para representar partidos"""
    jornada = models.ForeignKey(Jornada, on_delete=models.CASCADE, related_name='partidos')
    equipo_local = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='partidos_local')
    equipo_visitante = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='partidos_visitante')
    fecha_hora = models.DateTimeField()
    
    # Resultados oficiales
    goles_local = models.IntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(0)]
    )
    goles_visitante = models.IntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(0)]
    )
    finalizado = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Partido"
        verbose_name_plural = "Partidos"
        ordering = ['fecha_hora']
    
    def __str__(self):
        return f"{self.equipo_local} vs {self.equipo_visitante}"
    
    def get_slug(self):
        """Genera un slug amigable para URLs"""
        local_slug = slugify(str(self.equipo_local))
        visitante_slug = slugify(str(self.equipo_visitante))
        return f"{local_slug}-vs-{visitante_slug}-{self.id}"
    
    def get_absolute_url(self):
        """URL absoluta del partido"""
        from django.urls import reverse
        return reverse('quinielas:apostar_slug', kwargs={'slug': self.get_slug()})
    
    @property
    def resultado_oficial(self):
        """Retorna el resultado oficial del partido si está disponible"""
        if self.goles_local is not None and self.goles_visitante is not None:
            return f"{self.goles_local}-{self.goles_visitante}"
        return "Sin resultado"
    
    @property
    def estado_actual(self):
        """Determina el estado actual del partido basado en fecha y finalización"""
        from django.utils import timezone
        now = timezone.now()
        
        if self.finalizado:
            return "FINALIZADO"
        elif self.fecha_hora <= now:
            # Si ya pasó la fecha pero no está marcado como finalizado
            if now - self.fecha_hora <= timezone.timedelta(hours=3):
                return "EN_CURSO"
            else:
                return "PENDIENTE_RESULTADO"  # Partido que debería haber terminado
        else:
            return "PROGRAMADO"
    
    @property
    def puede_apostar(self):
        """Determina si se puede apostar en este partido"""
        from django.utils import timezone
        now = timezone.now()
        
        # No se puede apostar si ya finalizó o si ya empezó
        return not self.finalizado and self.fecha_hora > now
    
    @property
    def minutos_para_inicio(self):
        """Retorna los minutos que faltan para el inicio del partido"""
        from django.utils import timezone
        now = timezone.now()
        
        if self.fecha_hora <= now:
            return 0
        
        diff = self.fecha_hora - now
        return int(diff.total_seconds() / 60)
    
    def marcar_resultado(self, goles_local, goles_visitante):
        """Marca el resultado oficial y actualiza puntuaciones"""
        self.goles_local = goles_local
        self.goles_visitante = goles_visitante
        self.finalizado = True
        self.save()
        
        # Actualizar puntuaciones de todas las apuestas relacionadas
        for apuesta in self.apuestas.all():
            apuesta.calcular_puntos()


class Apuesta(models.Model):
    """Modelo para representar las apuestas de los participantes"""
    participante = models.ForeignKey(Participante, on_delete=models.CASCADE, related_name='apuestas')
    partido = models.ForeignKey(Partido, on_delete=models.CASCADE, related_name='apuestas')
    goles_local_apostados = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(20)]
    )
    goles_visitante_apostados = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(20)]
    )
    fecha_apuesta = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    puntos = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ('participante', 'partido')
        verbose_name = "Apuesta"
        verbose_name_plural = "Apuestas"
        ordering = ['-fecha_modificacion']
    
    def __str__(self):
        return f"{self.participante.usuario.username}: {self.goles_local_apostados}-{self.goles_visitante_apostados}"
    
    @property
    def resultado_apostado(self):
        """Retorna el resultado apostado"""
        return f"{self.goles_local_apostados}-{self.goles_visitante_apostados}"
    
    def calcular_puntos(self):
        """Calcula los puntos obtenidos basado en el resultado oficial"""
        if not self.partido.finalizado:
            self.puntos = 0
            self.save()
            return 0
        
        puntos = 0
        goles_local_oficial = self.partido.goles_local
        goles_visitante_oficial = self.partido.goles_visitante
        
        # Resultado exacto: 5 puntos
        if (self.goles_local_apostados == goles_local_oficial and 
            self.goles_visitante_apostados == goles_visitante_oficial):
            puntos = 5
        else:
            # Tendencia correcta: 3 puntos
            diferencia_oficial = goles_local_oficial - goles_visitante_oficial
            diferencia_apostada = self.goles_local_apostados - self.goles_visitante_apostados
            
            # Verificar si acertó la tendencia (local gana, empate, visitante gana)
            if ((diferencia_oficial > 0 and diferencia_apostada > 0) or
                (diferencia_oficial == 0 and diferencia_apostada == 0) or
                (diferencia_oficial < 0 and diferencia_apostada < 0)):
                puntos = 3
        
        self.puntos = puntos
        self.save()
        
        # Actualizar puntos totales del participante
        self.participante.calcular_puntos_totales()
        
        return puntos
    
    def puede_modificar(self):
        """Verifica si la apuesta puede ser modificada"""
        return (self.participante.quiniela.puede_apostar and 
                timezone.now() < self.partido.fecha_hora)
