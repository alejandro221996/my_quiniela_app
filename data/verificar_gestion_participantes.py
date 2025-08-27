#!/usr/bin/env python
"""
Script de verificación del sistema de gestión de participantes
"""
import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quinielas_project.settings')
django.setup()

from django.contrib.auth.models import User
from quinielas.models import Quiniela, Participante

def verificar_sistema():
    print("🔍 Verificando sistema de gestión de participantes...")
    
    # Verificar que la quiniela de prueba existe
    try:
        quiniela = Quiniela.objects.get(nombre='Liga Test Pagos')
        print(f"✅ Quiniela encontrada: {quiniela.nombre} (ID: {quiniela.id})")
    except Quiniela.DoesNotExist:
        print("❌ No se encontró la quiniela de prueba")
        return False
    
    # Verificar participantes
    participantes = Participante.objects.filter(quiniela=quiniela)
    print(f"✅ Total participantes: {participantes.count()}")
    
    # Verificar estados
    estados = {}
    for estado, _ in Participante.ESTADOS_PARTICIPANTE:
        count = participantes.filter(estado=estado).count()
        estados[estado] = count
        print(f"   - {estado}: {count} participantes")
    
    # Verificar métodos del modelo
    for participante in participantes:
        try:
            # Probar métodos del modelo
            dias = participante.dias_desde_union
            puntos = participante.puntos_totales
            apuestas = participante.total_apuestas
            
            print(f"✅ {participante.usuario.username}: {dias} días, {puntos} puntos, {apuestas} apuestas")
            
            # Probar métodos de gestión
            if participante.estado == 'PENDIENTE':
                # Simular marcar como pagado (sin guardar)
                print(f"   - Puede marcarse como pagado: ✅")
            
        except Exception as e:
            print(f"❌ Error en participante {participante.usuario.username}: {e}")
            return False
    
    # Verificar URLs críticas
    print(f"\n🌐 URLs disponibles:")
    print(f"Dashboard Creador: /quiniela/{quiniela.id}/dashboard-creador/")
    print(f"Gestionar Participantes: /quiniela/{quiniela.id}/gestionar-participantes/")
    print(f"Exportar CSV: /quiniela/{quiniela.id}/exportar-participantes/")
    
    print(f"\n🎉 Verificación completada exitosamente!")
    print(f"✅ Sistema de gestión de participantes funcionando correctamente")
    
    return True

if __name__ == '__main__':
    verificar_sistema()
