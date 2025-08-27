#!/usr/bin/env python3
"""
Script para generar datos específicos de "Mis Apuestas" para un usuario
Útil para testear la vista individual de apuestas
"""

import os
import sys
import django
from datetime import datetime, timedelta
import random

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quinielas_project.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from quinielas.models import Participante, Partido, Apuesta

def generar_mis_apuestas(username='testuser'):
    """
    Generar apuestas para un usuario específico para testear 'Mis Apuestas'
    """
    print(f"🎯 Generando apuestas para el usuario: {username}")
    
    # Verificar que el usuario existe
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        print(f"❌ Usuario '{username}' no encontrado")
        return
    
    # Verificar que el usuario tiene participaciones
    participantes = Participante.objects.filter(usuario=user)
    if not participantes.exists():
        print(f"❌ Usuario '{username}' no participa en ninguna quiniela")
        print("💡 Ejecuta primero: python generar_datos_analiticas.py")
        return
    
    # Obtener partidos disponibles
    partidos_finalizados = Partido.objects.filter(finalizado=True)
    partidos_futuros = Partido.objects.filter(finalizado=False)
    
    print(f"📊 Partidos disponibles:")
    print(f"   • Finalizados: {partidos_finalizados.count()}")
    print(f"   • Futuros: {partidos_futuros.count()}")
    
    apuestas_creadas = 0
    
    for participante in participantes:
        print(f"\n🏆 Quiniela: {participante.quiniela.nombre}")
        
        # Generar apuestas en partidos finalizados (con resultados variados)
        for partido in partidos_finalizados[:20]:  # Primeros 20 partidos
            if not Apuesta.objects.filter(participante=participante, partido=partido).exists():
                
                # Simular diferentes niveles de acierto
                probabilidad_acierto = random.random()
                
                if probabilidad_acierto < 0.2:  # 20% resultados exactos
                    goles_local = partido.goles_local
                    goles_visitante = partido.goles_visitante
                elif probabilidad_acierto < 0.5:  # 30% tendencia correcta
                    if partido.goles_local > partido.goles_visitante:
                        goles_local = partido.goles_local + random.randint(-1, 1)
                        goles_visitante = partido.goles_visitante - random.randint(0, 1)
                    elif partido.goles_local < partido.goles_visitante:
                        goles_local = partido.goles_local - random.randint(0, 1)
                        goles_visitante = partido.goles_visitante + random.randint(-1, 1)
                    else:  # Empate
                        goles_local = random.randint(1, 3)
                        goles_visitante = goles_local
                else:  # 50% apuestas incorrectas
                    goles_local = random.randint(0, 4)
                    goles_visitante = random.randint(0, 4)
                
                # Asegurar valores no negativos
                goles_local = max(0, goles_local)
                goles_visitante = max(0, goles_visitante)
                
                apuesta = Apuesta.objects.create(
                    participante=participante,
                    partido=partido,
                    goles_local_apostados=goles_local,
                    goles_visitante_apostados=goles_visitante,
                    fecha_apuesta=partido.fecha_hora - timedelta(hours=random.randint(2, 48)),
                    fecha_modificacion=partido.fecha_hora - timedelta(hours=random.randint(1, 24))
                )
                
                # Calcular puntos
                puntos = 0
                if (goles_local == partido.goles_local and goles_visitante == partido.goles_visitante):
                    puntos = 5  # Resultado exacto
                elif ((goles_local > goles_visitante and partido.goles_local > partido.goles_visitante) or
                      (goles_local < goles_visitante and partido.goles_local < partido.goles_visitante) or
                      (goles_local == goles_visitante and partido.goles_local == partido.goles_visitante)):
                    puntos = 3  # Tendencia correcta
                elif (goles_local == partido.goles_local or goles_visitante == partido.goles_visitante):
                    puntos = 1  # Un marcador correcto
                
                apuesta.puntos = puntos
                apuesta.save()
                apuestas_creadas += 1
        
        # Generar algunas apuestas en partidos futuros
        for partido in partidos_futuros[:10]:  # Primeros 10 partidos futuros
            if not Apuesta.objects.filter(participante=participante, partido=partido).exists():
                
                goles_local = random.randint(0, 3)
                goles_visitante = random.randint(0, 3)
                
                Apuesta.objects.create(
                    participante=participante,
                    partido=partido,
                    goles_local_apostados=goles_local,
                    goles_visitante_apostados=goles_visitante,
                    fecha_apuesta=timezone.now() - timedelta(hours=random.randint(1, 24)),
                    fecha_modificacion=timezone.now() - timedelta(minutes=random.randint(1, 60))
                )
                apuestas_creadas += 1
    
    # Estadísticas finales
    total_apuestas = Apuesta.objects.filter(participante__usuario=user).count()
    apuestas_con_puntos = Apuesta.objects.filter(participante__usuario=user, puntos__gt=0).count()
    puntos_totales = sum(a.puntos or 0 for a in Apuesta.objects.filter(participante__usuario=user))
    
    print(f"\n✅ DATOS DE APUESTAS GENERADOS!")
    print(f"   • Apuestas creadas en esta ejecución: {apuestas_creadas}")
    print(f"   • Total de apuestas del usuario: {total_apuestas}")
    print(f"   • Apuestas con puntos: {apuestas_con_puntos}")
    print(f"   • Puntos totales: {puntos_totales}")
    
    if total_apuestas > 0:
        precision = (apuestas_con_puntos / total_apuestas) * 100
        print(f"   • Precisión: {precision:.1f}%")
    
    print(f"\n🎯 Para testear:")
    print(f"   1. Ingresa como '{username}'")
    print(f"   2. Ve a 'Mis Apuestas' en el menú")
    print(f"   3. Verás apuestas con resultados variados")
    print(f"   4. Revisa estadísticas de precisión y puntos")

if __name__ == '__main__':
    # Permitir especificar el usuario como argumento
    username = sys.argv[1] if len(sys.argv) > 1 else 'testuser'
    generar_mis_apuestas(username)
