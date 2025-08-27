#!/usr/bin/env python3
"""
Script para generar datos de prueba para las analíticas del dashboard
Crear partidos, apuestas, y resultados realistas para testear todas las funcionalidades
"""

import os
import sys
import django
from datetime import datetime, timedelta
import random
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quinielas_project.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from quinielas.models import (
    Quiniela, Participante, Jornada, Equipo, Partido, Apuesta
)

class GeneradorDatosAnaliticas:
    def __init__(self):
        self.equipos_liga_mx = [
            "América", "Chivas", "Cruz Azul", "Pumas", "Tigres", "Monterrey",
            "Santos", "León", "Toluca", "Atlas", "Pachuca", "Necaxa",
            "Puebla", "Querétaro", "Mazatlán", "Juárez", "Tijuana", "San Luis"
        ]
        
        # Usuarios de prueba existentes
        self.usuarios = [
            'admin', 'testuser', 'juan', 'maria', 'carlos', 'ana', 
            'aleja', 'prueba123', 'pruebatres'
        ]
        
    def crear_equipos(self):
        """Crear equipos de Liga MX si no existen"""
        print("🏈 Creando equipos de Liga MX...")
        
        equipos_creados = 0
        for nombre in self.equipos_liga_mx:
            equipo, created = Equipo.objects.get_or_create(
                nombre=nombre,
                defaults={
                    'liga': 'Liga MX',
                    'activo': True
                }
            )
            if created:
                equipos_creados += 1
                
        print(f"✅ Equipos creados: {equipos_creados}")
        return Equipo.objects.all()
    
    def crear_jornadas(self):
        """Crear jornadas de la temporada"""
        print("📅 Creando jornadas...")
        
        jornadas_creadas = 0
        for i in range(1, 18):  # 17 jornadas
            jornada, created = Jornada.objects.get_or_create(
                numero=i,
                defaults={
                    'nombre': f'Jornada {i}',
                    'activa': i <= 3,  # Solo las primeras 3 activas
                    'fecha_inicio': timezone.now() - timedelta(days=(17-i)*7),
                    'fecha_fin': timezone.now() - timedelta(days=(17-i)*7) + timedelta(days=3)
                }
            )
            if created:
                jornadas_creadas += 1
                
        print(f"✅ Jornadas creadas: {jornadas_creadas}")
        return Jornada.objects.all()
    
    def crear_partidos_con_resultados(self, equipos, jornadas):
        """Crear partidos con resultados variados para analíticas"""
        print("⚽ Creando partidos con resultados...")
        
        partidos_creados = 0
        
        for jornada in jornadas[:15]:  # Primeras 15 jornadas con resultados
            equipos_disponibles = list(equipos)
            random.shuffle(equipos_disponibles)
            
            # 9 partidos por jornada (18 equipos / 2)
            for i in range(0, len(equipos_disponibles)-1, 2):
                if i+1 < len(equipos_disponibles):
                    equipo_local = equipos_disponibles[i]
                    equipo_visitante = equipos_disponibles[i+1]
                    
                    # Fecha en el pasado para jornadas anteriores
                    fecha_partido = jornada.fecha_inicio + timedelta(days=random.randint(0, 2))
                    
                    partido, created = Partido.objects.get_or_create(
                        equipo_local=equipo_local,
                        equipo_visitante=equipo_visitante,
                        jornada=jornada,
                        defaults={
                            'fecha_hora': fecha_partido,
                            'finalizado': True,
                            'goles_local': random.randint(0, 4),
                            'goles_visitante': random.randint(0, 4),
                        }
                    )
                    
                    if created:
                        partidos_creados += 1
        
        # Crear algunos partidos futuros para las jornadas activas
        for jornada in jornadas[15:]:
            equipos_disponibles = list(equipos[:10])  # Solo algunos equipos
            random.shuffle(equipos_disponibles)
            
            for i in range(0, min(6, len(equipos_disponibles)-1), 2):
                equipo_local = equipos_disponibles[i]
                equipo_visitante = equipos_disponibles[i+1]
                
                # Fechas futuras
                fecha_partido = timezone.now() + timedelta(days=random.randint(1, 14))
                
                partido, created = Partido.objects.get_or_create(
                    equipo_local=equipo_local,
                    equipo_visitante=equipo_visitante,
                    jornada=jornada,
                    defaults={
                        'fecha_hora': fecha_partido,
                        'finalizado': False,
                    }
                )
                
                if created:
                    partidos_creados += 1
                    
        print(f"✅ Partidos creados: {partidos_creados}")
        return Partido.objects.all()
    
    def crear_quiniela_con_participantes(self):
        """Crear una quiniela con todos los usuarios como participantes"""
        print("🎯 Creando quiniela principal...")
        
        admin_user = User.objects.filter(username='admin').first()
        if not admin_user:
            print("❌ Usuario admin no encontrado")
            return None
            
        quiniela, created = Quiniela.objects.get_or_create(
            nombre='Liga MX 2025 - Analíticas',
            creador=admin_user,
            defaults={
                'descripcion': 'Quiniela principal para testear analíticas del dashboard',
                'fecha_limite': timezone.now() + timedelta(days=30),
                'activa': True
            }
        )
        
        if created:
            print("✅ Quiniela creada")
        
        # Agregar participantes
        participantes_creados = 0
        for username in self.usuarios:
            user = User.objects.filter(username=username).first()
            if user and user != admin_user:  # El creador no participa
                participante, created = Participante.objects.get_or_create(
                    usuario=user,
                    quiniela=quiniela,
                    defaults={
                        'estado': 'ACTIVO',
                        'fecha_pago': timezone.now() - timedelta(days=random.randint(1, 30)),
                        'monto_pagado': Decimal('100.00')
                    }
                )
                if created:
                    participantes_creados += 1
                    
        print(f"✅ Participantes agregados: {participantes_creados}")
        return quiniela
    
    def generar_apuestas_realistas(self, quiniela, partidos):
        """Generar apuestas variadas para analíticas interesantes"""
        print("🎲 Generando apuestas realistas...")
        
        if not quiniela:
            print("❌ No hay quiniela disponible")
            return
            
        participantes = Participante.objects.filter(quiniela=quiniela)
        partidos_finalizados = partidos.filter(finalizado=True)
        
        apuestas_creadas = 0
        
        for participante in participantes:
            # Cada participante apuesta en un porcentaje aleatorio de partidos
            porcentaje_apuestas = random.uniform(0.6, 0.9)  # Entre 60% y 90% de partidos
            num_apuestas = int(len(partidos_finalizados) * porcentaje_apuestas)
            
            partidos_a_apostar = random.sample(list(partidos_finalizados), num_apuestas)
            
            for partido in partidos_a_apostar:
                # Simular diferentes tipos de apostadores
                if random.random() < 0.3:  # 30% son buenos apostadores
                    # Apostadores con mejor precisión
                    goles_local = partido.goles_local + random.randint(-1, 1)
                    goles_visitante = partido.goles_visitante + random.randint(-1, 1)
                else:
                    # Apostadores promedio/malos
                    goles_local = random.randint(0, 4)
                    goles_visitante = random.randint(0, 4)
                
                goles_local = max(0, goles_local)
                goles_visitante = max(0, goles_visitante)
                
                apuesta, created = Apuesta.objects.get_or_create(
                    participante=participante,
                    partido=partido,
                    defaults={
                        'goles_local_apostados': goles_local,
                        'goles_visitante_apostados': goles_visitante,
                        'fecha_apuesta': partido.fecha_hora - timedelta(hours=random.randint(1, 48)),
                        'fecha_modificacion': partido.fecha_hora - timedelta(hours=random.randint(1, 24))
                    }
                )
                
                if created:
                    apuestas_creadas += 1
                    
        print(f"✅ Apuestas generadas: {apuestas_creadas}")
        
        # Calcular puntos para todas las apuestas
        self.calcular_puntos_apuestas()
    
    def calcular_puntos_apuestas(self):
        """Calcular puntos para todas las apuestas según resultados"""
        print("📊 Calculando puntos...")
        
        apuestas_actualizadas = 0
        
        for apuesta in Apuesta.objects.filter(partido__finalizado=True):
            partido = apuesta.partido
            
            # Sistema de puntos simple
            puntos = 0
            
            # Resultado exacto: 5 puntos
            if (apuesta.goles_local_apostados == partido.goles_local and 
                apuesta.goles_visitante_apostados == partido.goles_visitante):
                puntos = 5
            
            # Tendencia correcta (ganador): 3 puntos
            elif ((apuesta.goles_local_apostados > apuesta.goles_visitante_apostados and 
                   partido.goles_local > partido.goles_visitante) or
                  (apuesta.goles_local_apostados < apuesta.goles_visitante_apostados and 
                   partido.goles_local < partido.goles_visitante) or
                  (apuesta.goles_local_apostados == apuesta.goles_visitante_apostados and 
                   partido.goles_local == partido.goles_visitante)):
                puntos = 3
            
            # Un marcador correcto: 1 punto
            elif (apuesta.goles_local_apostados == partido.goles_local or 
                  apuesta.goles_visitante_apostados == partido.goles_visitante):
                puntos = 1
            
            apuesta.puntos = puntos
            apuesta.save()
            apuestas_actualizadas += 1
            
        print(f"✅ Puntos calculados para {apuestas_actualizadas} apuestas")
    
    def generar_todo(self):
        """Ejecutar todo el proceso de generación"""
        print("🚀 Iniciando generación de datos para analíticas...")
        print("=" * 50)
        
        try:
            # 1. Crear equipos
            equipos = self.crear_equipos()
            
            # 2. Crear jornadas
            jornadas = self.crear_jornadas()
            
            # 3. Crear partidos con resultados
            partidos = self.crear_partidos_con_resultados(equipos, jornadas)
            
            # 4. Crear quiniela principal
            quiniela = self.crear_quiniela_con_participantes()
            
            # 5. Generar apuestas
            self.generar_apuestas_realistas(quiniela, partidos)
            
            print("=" * 50)
            print("🎉 DATOS GENERADOS EXITOSAMENTE!")
            print("")
            print("📊 Resumen de datos generados:")
            print(f"   • Equipos: {Equipo.objects.count()}")
            print(f"   • Jornadas: {Jornada.objects.count()}")
            print(f"   • Partidos: {Partido.objects.count()}")
            print(f"   • Partidos finalizados: {Partido.objects.filter(finalizado=True).count()}")
            print(f"   • Quinielas: {Quiniela.objects.count()}")
            print(f"   • Participantes: {Participante.objects.count()}")
            print(f"   • Apuestas: {Apuesta.objects.count()}")
            print("")
            print("🎯 Puedes ahora:")
            print("   1. Ir al dashboard para ver analíticas completas")
            print("   2. Ver 'Mis Apuestas' con datos realistas")
            print("   3. Revisar rankings con puntuaciones")
            print("   4. Analizar estadísticas de precisión")
            
        except Exception as e:
            print(f"❌ Error durante la generación: {e}")
            raise

if __name__ == '__main__':
    generador = GeneradorDatosAnaliticas()
    generador.generar_todo()
