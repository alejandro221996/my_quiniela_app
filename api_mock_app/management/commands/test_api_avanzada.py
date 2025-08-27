#!/usr/bin/env python3
"""
Comando para probar todas las funcionalidades avanzadas de la API Mock
"""

from django.core.management.base import BaseCommand
from django.test import Client
from django.contrib.auth.models import User
import json
import time

class Command(BaseCommand):
    help = 'Prueba todas las funcionalidades avanzadas de la API Mock'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            default='testuser',
            help='Usuario para las pruebas (default: testuser)'
        )
        parser.add_argument(
            '--partido-id',
            type=int,
            default=6,
            help='ID del partido para pruebas (default: 6)'
        )

    def handle(self, *args, **options):
        username = options['user']
        partido_id = options['partido_id']
        
        self.stdout.write(self.style.SUCCESS(f'🚀 Iniciando pruebas de API Mock avanzada'))
        self.stdout.write(f'Usuario: {username}')
        self.stdout.write(f'Partido ID: {partido_id}')
        self.stdout.write('-' * 60)
        
        # Configurar cliente de prueba
        client = Client()
        
        try:
            user = User.objects.get(username=username)
            client.force_login(user)
            self.stdout.write(self.style.SUCCESS(f'✅ Login exitoso como {username}'))
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ Usuario {username} no existe'))
            return
        
        # Lista de pruebas a ejecutar
        tests = [
            ('Status API', f'/api/status/'),
            ('Partidos Básicos', f'/api/partidos/'),
            ('Tiempo Real', f'/api/partido/{partido_id}/tiempo-real/'),
            ('Mercado Apuestas', f'/api/partido/{partido_id}/mercado-apuestas/'),
            ('Analytics Avanzados', f'/api/partido/{partido_id}/analytics-avanzados/'),
            ('Estadísticas Usuario', f'/api/usuario/estadisticas/'),
        ]
        
        results = {}
        
        for test_name, endpoint in tests:
            self.stdout.write(f'\\n🔍 Probando: {test_name}')
            self.stdout.write(f'   Endpoint: {endpoint}')
            
            try:
                response = client.get(endpoint)
                
                if response.status_code == 200:
                    data = response.json()
                    results[test_name] = {
                        'status': 'SUCCESS',
                        'response_size': len(str(data)),
                        'keys': list(data.keys())[:5]  # Primeras 5 claves
                    }
                    self.stdout.write(self.style.SUCCESS(f'   ✅ SUCCESS (Status: {response.status_code})'))
                    self.stdout.write(f'   📊 Tamaño respuesta: {len(str(data))} chars')
                    self.stdout.write(f'   🔑 Claves principales: {", ".join(list(data.keys())[:3])}')
                    
                elif response.status_code in [408, 429, 206]:  # Errores simulados
                    data = response.json()
                    results[test_name] = {
                        'status': 'SIMULATED_ERROR',
                        'error_type': data.get('code', 'unknown'),
                        'message': data.get('message', 'Sin mensaje')
                    }
                    self.stdout.write(self.style.WARNING(f'   ⚠️ ERROR SIMULADO (Status: {response.status_code})'))
                    self.stdout.write(f'   💬 Mensaje: {data.get("message", "N/A")}')
                    
                else:
                    results[test_name] = {
                        'status': 'ERROR',
                        'status_code': response.status_code
                    }
                    self.stdout.write(self.style.ERROR(f'   ❌ ERROR (Status: {response.status_code})'))
                    
            except Exception as e:
                results[test_name] = {
                    'status': 'EXCEPTION',
                    'error': str(e)
                }
                self.stdout.write(self.style.ERROR(f'   💥 EXCEPCIÓN: {str(e)}'))
            
            time.sleep(0.1)  # Pequeña pausa entre requests
        
        # Prueba especial: Simulación completa de partido
        self.stdout.write(f'\\n🎮 Probando: Simulación Completa de Partido')
        try:
            response = client.post(f'/api/partido/{partido_id}/simular-completo/')
            if response.status_code == 200:
                data = response.json()
                if 'simulacion' in data:
                    sim = data['simulacion']
                    self.stdout.write(self.style.SUCCESS(f'   ✅ Simulación completada'))
                    self.stdout.write(f'   ⚽ Resultado: {sim["estado_final"]["goles_local"]}-{sim["estado_final"]["goles_visitante"]}')
                    self.stdout.write(f'   ⏱️ Duración: {sim["duracion_total"]} minutos')
                    self.stdout.write(f'   🎯 Eventos destacados: {len(sim["eventos_destacados"])}')
                else:
                    self.stdout.write(self.style.WARNING(f'   ⚠️ Simulación básica (simulador no disponible)'))
            else:
                self.stdout.write(self.style.ERROR(f'   ❌ Error en simulación (Status: {response.status_code})'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   💥 Error en simulación: {str(e)}'))
        
        # Resumen final
        self.stdout.write('\\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('📊 RESUMEN DE PRUEBAS'))
        self.stdout.write('=' * 60)
        
        successful = sum(1 for r in results.values() if r['status'] == 'SUCCESS')
        simulated_errors = sum(1 for r in results.values() if r['status'] == 'SIMULATED_ERROR')
        real_errors = sum(1 for r in results.values() if r['status'] in ['ERROR', 'EXCEPTION'])
        
        self.stdout.write(f'✅ Exitosas: {successful}/{len(tests)}')
        self.stdout.write(f'⚠️ Errores simulados: {simulated_errors}/{len(tests)}')
        self.stdout.write(f'❌ Errores reales: {real_errors}/{len(tests)}')
        
        if real_errors == 0:
            self.stdout.write(self.style.SUCCESS('\\n🎉 ¡Todas las APIs funcionan correctamente!'))
        else:
            self.stdout.write(self.style.WARNING(f'\\n⚠️ Hay {real_errors} APIs con problemas'))
        
        # Sugerencias para testing
        self.stdout.write('\\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('💡 SUGERENCIAS PARA TESTING'))
        self.stdout.write('=' * 60)
        
        suggestions = [
            "🔄 Ejecuta este comando varias veces para ver errores simulados diferentes",
            "📊 Usa los datos de mercado para simular cambios de cuotas en tiempo real",
            "🎯 Los analytics de IA pueden usarse para validar algoritmos de predicción",
            "⚡ El tiempo real permite testear actualizaciones en vivo del dashboard",
            "🎮 Las simulaciones completas son ideales para generar datos históricos",
            "🐛 Los errores simulados te ayudan a probar la robustez de tu frontend"
        ]
        
        for suggestion in suggestions:
            self.stdout.write(f'   {suggestion}')
        
        self.stdout.write(f'\\n🚀 Para probar con otros partidos: --partido-id=<ID>')
        self.stdout.write(f'👤 Para probar con otros usuarios: --user=<username>')
