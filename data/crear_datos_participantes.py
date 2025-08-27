#!/usr/bin/env python
"""
Script para crear datos de prueba del sistema de gestión de participantes
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

def crear_datos_prueba():
    print("🎯 Creando datos de prueba para gestión de participantes...")
    
    # Buscar o crear usuarios
    creador, created = User.objects.get_or_create(
        username='creador_test',
        defaults={
            'email': 'creador@test.com',
            'first_name': 'Juan',
            'last_name': 'Creador'
        }
    )
    if created:
        creador.set_password('password123')
        creador.save()
        print(f"✅ Creado usuario creador: {creador.username}")
    
    # Crear quiniela de prueba
    quiniela, created = Quiniela.objects.get_or_create(
        nombre='Liga Test Pagos',
        creador=creador,
        defaults={
            'descripcion': 'Quiniela para probar sistema de pagos',
            'fecha_limite': datetime.now() + timedelta(days=30),
            'activa': True
        }
    )
    if created:
        print(f"✅ Creada quiniela: {quiniela.nombre}")
    
    # Crear participantes con diferentes estados
    participantes_data = [
        {'username': 'pagado1', 'first_name': 'Ana', 'last_name': 'Pagada', 'estado': 'PAGADO', 'monto': '50.00'},
        {'username': 'pagado2', 'first_name': 'Carlos', 'last_name': 'Completo', 'estado': 'PAGADO', 'monto': '50.00'},
        {'username': 'pendiente1', 'first_name': 'María', 'last_name': 'Pendiente', 'estado': 'PENDIENTE', 'monto': None},
        {'username': 'pendiente2', 'first_name': 'Luis', 'last_name': 'Esperando', 'estado': 'PENDIENTE', 'monto': None},
        {'username': 'suspendido1', 'first_name': 'Pedro', 'last_name': 'Suspendido', 'estado': 'SUSPENDIDO', 'monto': None},
    ]
    
    for data in participantes_data:
        user, user_created = User.objects.get_or_create(
            username=data['username'],
            defaults={
                'email': f"{data['username']}@test.com",
                'first_name': data['first_name'],
                'last_name': data['last_name']
            }
        )
        if user_created:
            user.set_password('password123')
            user.save()
        
        # Crear o actualizar participante
        participante, part_created = Participante.objects.get_or_create(
            quiniela=quiniela,
            usuario=user,
            defaults={'fecha_union': datetime.now()}
        )
        
        # Actualizar estado y datos de pago
        participante.estado = data['estado']
        if data['monto']:
            participante.monto_pagado = Decimal(data['monto'])
            participante.metodo_pago = 'TRANSFERENCIA'
            participante.fecha_pago = datetime.now().date()
        participante.save()
        
        status = "✅ Creado" if part_created else "🔄 Actualizado"
        print(f"{status} participante: {user.get_full_name()} - {data['estado']}")
    
    print(f"\n🎉 Datos de prueba creados exitosamente!")
    print(f"📊 Quiniela: {quiniela.nombre} (ID: {quiniela.id})")
    print(f"👤 Creador: {creador.username}")
    print(f"👥 Participantes: {Participante.objects.filter(quiniela=quiniela).count()}")
    print(f"\n🌐 URLs de prueba:")
    print(f"Dashboard Creador: http://127.0.0.1:8000/quiniela/{quiniela.id}/dashboard-creador/")
    print(f"Gestionar Participantes: http://127.0.0.1:8000/quiniela/{quiniela.id}/gestionar-participantes/")
    print(f"\n🔐 Login como creador:")
    print(f"Usuario: {creador.username}")
    print(f"Contraseña: password123")

if __name__ == '__main__':
    crear_datos_prueba()
