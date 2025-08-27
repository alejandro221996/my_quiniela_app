#!/usr/bin/env python3
"""
Demostración del flujo de cálculo de puntos en el sistema de quinielas
"""

import os
import sys
import django
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quinielas_project.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from quinielas.models import Partido, Apuesta, Participante

def demostrar_flujo_puntos():
    """
    Demuestra el flujo completo de cálculo de puntos
    """
    print("🎯 DEMOSTRACIÓN DEL FLUJO DE CÁLCULO DE PUNTOS")
    print("=" * 60)
    
    # 1. Buscar un partido no finalizado con apuestas
    partido = Partido.objects.filter(
        finalizado=False,
        apuestas__isnull=False
    ).first()
    
    if not partido:
        print("❌ No se encontraron partidos no finalizados con apuestas")
        print("💡 Ejecuta 'python3 generar_datos_analiticas.py' primero")
        return
    
    print(f"🏈 Partido seleccionado: {partido}")
    print(f"   📅 Fecha: {partido.fecha_hora}")
    print(f"   ⚽ Estado: {'Finalizado' if partido.finalizado else 'Pendiente'}")
    
    # 2. Mostrar apuestas existentes
    apuestas = partido.apuestas.all()[:5]  # Primeras 5 apuestas
    print(f"\n📊 Apuestas realizadas ({apuestas.count()} total):")
    
    for i, apuesta in enumerate(apuestas, 1):
        usuario = apuesta.participante.usuario.username
        resultado = f"{apuesta.goles_local_apostados}-{apuesta.goles_visitante_apostados}"
        puntos_actuales = apuesta.puntos
        print(f"   {i}. {usuario}: {resultado} (Puntos actuales: {puntos_actuales})")
    
    # 3. Simular resultado del partido
    print(f"\n🎲 SIMULANDO RESULTADO DEL PARTIDO...")
    goles_local_real = 2
    goles_visitante_real = 1
    
    print(f"   🥅 Resultado simulado: {partido.equipo_local} {goles_local_real} - {goles_visitante_real} {partido.equipo_visitante}")
    
    # 4. Aplicar resultado y mostrar cálculo automático
    print(f"\n⚙️  APLICANDO RESULTADO Y CALCULANDO PUNTOS...")
    
    # Guardar estado anterior para comparación
    puntos_anteriores = {}
    for apuesta in apuestas:
        puntos_anteriores[apuesta.id] = apuesta.puntos
    
    # AQUÍ ES DONDE OCURRE LA MAGIA - El método marcar_resultado
    # hace AUTOMÁTICAMENTE el cálculo de puntos para todas las apuestas
    partido.marcar_resultado(goles_local_real, goles_visitante_real)
    
    print("✅ Resultado marcado - Puntos calculados automáticamente")
    
    # 5. Mostrar resultados después del cálculo
    print(f"\n🏆 RESULTADOS DESPUÉS DEL CÁLCULO:")
    print(f"   ⚽ Resultado oficial: {partido.resultado_oficial}")
    print(f"   ✅ Partido finalizado: {partido.finalizado}")
    
    # Recargar apuestas para ver puntos actualizados
    apuestas_actualizadas = Apuesta.objects.filter(partido=partido)[:5]
    
    print(f"\n📈 PUNTOS ACTUALIZADOS:")
    for apuesta in apuestas_actualizadas:
        usuario = apuesta.participante.usuario.username
        resultado_apostado = f"{apuesta.goles_local_apostados}-{apuesta.goles_visitante_apostados}"
        resultado_real = f"{partido.goles_local}-{partido.goles_visitante}"
        puntos_nuevos = apuesta.puntos
        puntos_anteriores_val = puntos_anteriores.get(apuesta.id, 0)
        
        # Determinar tipo de acierto
        if puntos_nuevos == 5:
            tipo_acierto = "🎯 RESULTADO EXACTO"
        elif puntos_nuevos == 3:
            tipo_acierto = "✅ TENDENCIA CORRECTA"
        elif puntos_nuevos == 0:
            tipo_acierto = "❌ SIN ACIERTO"
        else:
            tipo_acierto = f"📊 {puntos_nuevos} PUNTOS"
        
        cambio = puntos_nuevos - puntos_anteriores_val
        
        print(f"   👤 {usuario}:")
        print(f"      Apostó: {resultado_apostado}")
        print(f"      Real: {resultado_real}")
        print(f"      Puntos: {puntos_anteriores_val} → {puntos_nuevos} (+{cambio})")
        print(f"      {tipo_acierto}")
        print()
    
    # 6. Mostrar cómo se actualizaron los puntos totales
    print(f"🎯 PUNTOS TOTALES ACTUALIZADOS AUTOMÁTICAMENTE:")
    participantes_actualizados = Participante.objects.filter(
        apuestas__partido=partido
    ).distinct()[:3]
    
    for participante in participantes_actualizados:
        print(f"   🏆 {participante.usuario.username}: {participante.puntos_totales} puntos totales")
    
    print(f"\n" + "=" * 60)
    print("🔄 RESUMEN DEL FLUJO:")
    print("1️⃣  Los usuarios hacen apuestas ANTES del partido")
    print("2️⃣  Admin marca resultado en Django Admin o por API")
    print("3️⃣  Se ejecuta partido.marcar_resultado() AUTOMÁTICAMENTE")
    print("4️⃣  Se calculan puntos de TODAS las apuestas del partido")
    print("5️⃣  Se actualizan puntos totales de TODOS los participantes")
    print("6️⃣  Rankings se actualizan automáticamente")
    print("\n💡 Todo esto sucede EN UNA SOLA OPERACIÓN cuando se marca el resultado!")

if __name__ == '__main__':
    demostrar_flujo_puntos()
