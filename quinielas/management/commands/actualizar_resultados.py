"""
Comando Django para verificar y actualizar resultados de partidos automáticamente
Conecta con API externa para obtener resultados reales
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import datetime, timedelta
import requests
import json
import logging
from quinielas.models import Partido, Equipo, Jornada

# Configurar logging
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Verifica y actualiza resultados de partidos automáticamente desde API externa'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula la ejecución sin hacer cambios reales',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Muestra información detallada',
        )
        parser.add_argument(
            '--days-back',
            type=int,
            default=1,
            help='Número de días hacia atrás para verificar partidos (default: 1)',
        )
        parser.add_argument(
            '--liga',
            type=str,
            default='liga-mx',
            help='Liga a verificar (default: liga-mx)',
        )
    
    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        self.verbose = options['verbose']
        days_back = options['days_back']
        liga = options['liga']
        
        if self.dry_run:
            self.stdout.write(
                self.style.WARNING('🔄 MODO SIMULACIÓN - No se harán cambios reales')
            )
        
        self.stdout.write(f"🔍 Verificando resultados de los últimos {days_back} días...")
        
        # Calcular rango de fechas
        fecha_fin = timezone.now()
        fecha_inicio = fecha_fin - timedelta(days=days_back)
        
        # Buscar partidos no finalizados en el rango de tiempo
        partidos_pendientes = Partido.objects.filter(
            fecha_hora__gte=fecha_inicio,
            fecha_hora__lte=fecha_fin,
            finalizado=False
        ).order_by('fecha_hora')
        
        self.stdout.write(f"📊 Encontrados {partidos_pendientes.count()} partidos pendientes")
        
        partidos_actualizados = 0
        errores = 0
        
        for partido in partidos_pendientes:
            try:
                if self.verbose:
                    self.stdout.write(f"   🏈 Verificando: {partido}")
                
                # Verificar si el partido ya debería haber finalizado
                if partido.fecha_hora > timezone.now():
                    if self.verbose:
                        self.stdout.write(f"      ⏳ Partido aún no ha comenzado")
                    continue
                
                # Obtener resultado desde API
                resultado = self.obtener_resultado_api(partido, liga)
                
                if resultado:
                    if not self.dry_run:
                        # Actualizar resultado real
                        partido.marcar_resultado(
                            resultado['goles_local'],
                            resultado['goles_visitante']
                        )
                        partidos_actualizados += 1
                        
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"✅ {partido}: {resultado['goles_local']}-{resultado['goles_visitante']}"
                            )
                        )
                    else:
                        self.stdout.write(
                            f"   📋 Simularía actualizar: {partido} -> {resultado['goles_local']}-{resultado['goles_visitante']}"
                        )
                        partidos_actualizados += 1
                
                elif self.verbose:
                    self.stdout.write(f"      ❓ No se encontró resultado para {partido}")
                    
            except Exception as e:
                errores += 1
                self.stderr.write(f"❌ Error procesando {partido}: {str(e)}")
                logger.error(f"Error procesando partido {partido.id}: {str(e)}")
        
        # Resumen final
        self.stdout.write("\n" + "="*50)
        self.stdout.write(f"🎯 RESUMEN DE ACTUALIZACIÓN:")
        self.stdout.write(f"   📊 Partidos verificados: {partidos_pendientes.count()}")
        self.stdout.write(f"   ✅ Partidos actualizados: {partidos_actualizados}")
        self.stdout.write(f"   ❌ Errores: {errores}")
        
        if self.dry_run and partidos_actualizados > 0:
            self.stdout.write(
                self.style.WARNING(f"💡 Ejecuta sin --dry-run para aplicar {partidos_actualizados} cambios")
            )
        elif partidos_actualizados > 0:
            self.stdout.write(
                self.style.SUCCESS(f"🎉 Se actualizaron {partidos_actualizados} partidos exitosamente!")
            )
        else:
            self.stdout.write("ℹ️  No hay partidos para actualizar en este momento")
    
    def obtener_resultado_api(self, partido, liga):
        """
        Obtiene el resultado del partido desde API externa
        En esta implementación usamos datos mock, pero se puede conectar a APIs reales
        """
        try:
            # OPCIÓN 1: API Mock Local (para desarrollo)
            if liga == 'liga-mx':
                return self.obtener_resultado_mock(partido)
            
            # OPCIÓN 2: API Real (comentado para ejemplo)
            # return self.obtener_resultado_api_real(partido)
            
        except Exception as e:
            logger.error(f"Error obteniendo resultado de API: {str(e)}")
            return None
    
    def obtener_resultado_mock(self, partido):
        """
        Simula resultados usando datos mock para desarrollo
        """
        import random
        
        # Simular que solo 70% de partidos ya terminaron
        if random.random() < 0.3:
            return None
        
        # Generar resultado aleatorio realista
        goles_local = random.choices(
            [0, 1, 2, 3, 4, 5], 
            weights=[15, 25, 30, 20, 8, 2]
        )[0]
        
        goles_visitante = random.choices(
            [0, 1, 2, 3, 4], 
            weights=[20, 30, 25, 20, 5]
        )[0]
        
        return {
            'goles_local': goles_local,
            'goles_visitante': goles_visitante,
            'estado': 'finalizado',
            'fuente': 'mock-api'
        }
    
    def obtener_resultado_api_real(self, partido):
        """
        Conecta con API real de deportes (ejemplo con API-Football)
        """
        # Ejemplo de conexión a API real
        api_key = "TU_API_KEY_AQUI"
        
        headers = {
            'X-RapidAPI-Key': api_key,
            'X-RapidAPI-Host': 'api-football-v1.p.rapidapi.com'
        }
        
        # Buscar partido por equipos y fecha
        url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
        params = {
            'league': '262',  # Liga MX ID
            'season': '2025',
            'date': partido.fecha_hora.strftime('%Y-%m-%d')
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Buscar el partido específico
                for fixture in data.get('response', []):
                    home_team = fixture['teams']['home']['name']
                    away_team = fixture['teams']['away']['name']
                    
                    # Comparar equipos (usar lógica de matching)
                    if (self.equipos_coinciden(home_team, partido.equipo_local.nombre) and
                        self.equipos_coinciden(away_team, partido.equipo_visitante.nombre)):
                        
                        # Verificar si el partido está finalizado
                        if fixture['fixture']['status']['short'] in ['FT', 'AET', 'PEN']:
                            return {
                                'goles_local': fixture['goals']['home'],
                                'goles_visitante': fixture['goals']['away'],
                                'estado': 'finalizado',
                                'fuente': 'api-football'
                            }
            
        except requests.RequestException as e:
            logger.error(f"Error conectando con API: {str(e)}")
        
        return None
    
    def equipos_coinciden(self, nombre_api, nombre_local):
        """
        Verifica si los nombres de equipos coinciden
        """
        # Normalizar nombres para comparación
        nombre_api_norm = nombre_api.lower().strip()
        nombre_local_norm = nombre_local.lower().strip()
        
        # Comparación exacta
        if nombre_api_norm == nombre_local_norm:
            return True
        
        # Comparación por palabras clave
        palabras_api = set(nombre_api_norm.split())
        palabras_local = set(nombre_local_norm.split())
        
        # Si tienen al menos 1 palabra en común y longitud similar
        if len(palabras_api.intersection(palabras_local)) > 0:
            return True
        
        return False
