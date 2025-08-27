from django.contrib import admin
from .models import Quiniela, Participante, Equipo, Jornada, Partido, Apuesta


@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'nombre_corto', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre', 'nombre_corto')


@admin.register(Jornada)
class JornadaAdmin(admin.ModelAdmin):
    list_display = ('numero', 'nombre', 'fecha_inicio', 'fecha_fin', 'activa')
    list_filter = ('activa', 'fecha_inicio')
    ordering = ('numero',)


@admin.register(Partido)
class PartidoAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'jornada', 'fecha_hora', 'resultado_oficial', 'finalizado')
    list_filter = ('jornada', 'finalizado', 'fecha_hora')
    search_fields = ('equipo_local__nombre', 'equipo_visitante__nombre')
    date_hierarchy = 'fecha_hora'
    
    def resultado_oficial(self, obj):
        return obj.resultado_oficial
    resultado_oficial.short_description = 'Resultado'


@admin.register(Quiniela)
class QuinielaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'creador', 'codigo_acceso', 'fecha_limite', 'total_participantes', 'activa')
    list_filter = ('activa', 'fecha_creacion', 'fecha_limite')
    search_fields = ('nombre', 'codigo_acceso', 'creador__username')
    readonly_fields = ('codigo_acceso', 'fecha_creacion')
    date_hierarchy = 'fecha_creacion'


@admin.register(Participante)
class ParticipanteAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'quiniela', 'puntos_totales', 'fecha_union')
    list_filter = ('fecha_union', 'quiniela')
    search_fields = ('usuario__username', 'quiniela__nombre')
    readonly_fields = ('fecha_union',)


@admin.register(Apuesta)
class ApuestaAdmin(admin.ModelAdmin):
    list_display = ('participante', 'partido', 'resultado_apostado', 'puntos', 'fecha_modificacion')
    list_filter = ('partido__jornada', 'fecha_apuesta', 'puntos')
    search_fields = ('participante__usuario__username', 'partido__equipo_local__nombre', 'partido__equipo_visitante__nombre')
    readonly_fields = ('fecha_apuesta', 'fecha_modificacion', 'puntos')
    
    def resultado_apostado(self, obj):
        return obj.resultado_apostado
    resultado_apostado.short_description = 'Resultado Apostado'
