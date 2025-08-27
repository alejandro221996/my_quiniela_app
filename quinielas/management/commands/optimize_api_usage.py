"""
Management command para optimizar el uso de APIs externas
Ejemplo: python manage.py optimize_api_usage --api=football_data --sync-live
"""

from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
import json
import time
import logging

from quinielas.api_rate_limit_manager import APIRateLimitManager
from quinielas.api_optimization_config import (
    API_CONFIGURATIONS, 
    CACHE_STRATEGIES, 
    SMART_SCHEDULING
)

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Optimiza el uso de APIs externas con tokens limitados'

    def add_arguments(self, parser):
        parser.add_argument(
            '--api',
            type=str,
            choices=['football_data_org', 'sportradar', 'api_sports', 'all'],
            default='all',
            help='API específica a optimizar'
        )
        
        parser.add_argument(
            '--sync-live',
            action='store_true',
            help='Sincronizar partidos en vivo (alta prioridad)'
        )
        
        parser.add_argument(
            '--sync-upcoming',
            action='store_true', 
            help='Sincronizar partidos próximos (24 horas)'
        )
        
        parser.add_argument(
            '--sync-results',
            action='store_true',
            help='Sincronizar resultados recientes'
        )
        
        parser.add_argument(
            '--force-update',
            action='store_true',
            help='Forzar actualización ignorando cache'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simular operaciones sin hacer requests reales'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Iniciando optimización de APIs externas...')
        )
        
        # Configurar logging
        if options['verbosity'] >= 2:
            logging.basicConfig(level=logging.DEBUG)
        
        # Inicializar manager de rate limiting
        if options['api'] == 'all':
            apis_to_process = list(API_CONFIGURATIONS.keys())
        else:
            apis_to_process = [options['api']]
        
        for api_name in apis_to_process:
            self.stdout.write(f"\n📡 Procesando API: {api_name}")
            self.process_api(api_name, options)
        
        self.stdout.write(
            self.style.SUCCESS('\n✅ Optimización completada!')
        )

    def process_api(self, api_name, options):
        """Procesa una API específica con estrategias optimizadas"""
        
        api_config = API_CONFIGURATIONS[api_name]
        rate_manager = APIRateLimitManager(
            api_name=api_name,
            daily_limit=api_config['daily_limit'],
            per_minute_limit=api_config['per_minute_limit']
        )
        
        # Verificar límites actuales
        usage = rate_manager.get_current_usage()
        self.stdout.write(f"📊 Uso actual: {usage['daily_used']}/{usage['daily_limit']} diario")
        
        if usage['daily_used'] >= usage['daily_limit'] * 0.95:
            self.stdout.write(
                self.style.WARNING(f"⚠️  API {api_name} cerca del límite diario")
            )
            return
        
        # Estrategias por prioridad
        if options['sync_live']:
            self.sync_live_matches(rate_manager, api_name, options)
            
        if options['sync_upcoming']:
            self.sync_upcoming_matches(rate_manager, api_name, options)
            
        if options['sync_results']:
            self.sync_recent_results(rate_manager, api_name, options)

    def sync_live_matches(self, rate_manager, api_name, options):
        """Sincronizar partidos en vivo (máxima prioridad)"""
        self.stdout.write("🔴 Sincronizando partidos en vivo...")
        
        cache_key = f"live_matches_{api_name}"
        
        # Verificar cache primero
        if not options['force_update']:
            cached_data = cache.get(cache_key)
            if cached_data:
                age = timezone.now() - cached_data['timestamp']
                if age.seconds < CACHE_STRATEGIES['live_scores']['ttl']:
                    self.stdout.write("✅ Usando datos cacheados (frescos)")
                    return cached_data
        
        # Hacer request con rate limiting
        if options['dry_run']:
            self.stdout.write("🧪 [DRY RUN] Simulating live matches request")
            return
        
        try:
            with rate_manager.request_context('critical') as context:
                if context.can_proceed:
                    # Aquí iría la llamada real a la API
                    live_data = self.mock_api_call(api_name, 'live_matches')
                    
                    # Cachear resultado
                    cache.set(
                        cache_key,
                        {
                            'data': live_data,
                            'timestamp': timezone.now(),
                            'source': 'api'
                        },
                        timeout=CACHE_STRATEGIES['live_scores']['ttl']
                    )
                    
                    self.stdout.write(f"✅ {len(live_data)} partidos en vivo actualizados")
                else:
                    self.stdout.write("⏸️  Rate limit alcanzado - usando fallback")
                    
        except Exception as e:
            logger.error(f"Error sincronizando partidos en vivo: {e}")
            self.stdout.write(
                self.style.ERROR(f"❌ Error: {e}")
            )

    def sync_upcoming_matches(self, rate_manager, api_name, options):
        """Sincronizar partidos próximos (próximas 24 horas)"""
        self.stdout.write("🟡 Sincronizando partidos próximos...")
        
        cache_key = f"upcoming_matches_{api_name}"
        
        if not options['force_update']:
            cached_data = cache.get(cache_key)
            if cached_data:
                age = timezone.now() - cached_data['timestamp']
                if age.seconds < CACHE_STRATEGIES['upcoming_matches']['ttl']:
                    self.stdout.write("✅ Usando datos cacheados (próximos partidos)")
                    return cached_data
        
        if options['dry_run']:
            self.stdout.write("🧪 [DRY RUN] Simulating upcoming matches request")
            return
        
        try:
            with rate_manager.request_context('high') as context:
                if context.can_proceed:
                    upcoming_data = self.mock_api_call(api_name, 'upcoming_matches')
                    
                    cache.set(
                        cache_key,
                        {
                            'data': upcoming_data,
                            'timestamp': timezone.now(),
                            'source': 'api'
                        },
                        timeout=CACHE_STRATEGIES['upcoming_matches']['ttl']
                    )
                    
                    self.stdout.write(f"✅ {len(upcoming_data)} partidos próximos actualizados")
                else:
                    self.stdout.write("⏸️  Esperando rate limit para próximos partidos")
                    
        except Exception as e:
            logger.error(f"Error sincronizando partidos próximos: {e}")

    def sync_recent_results(self, rate_manager, api_name, options):
        """Sincronizar resultados recientes"""
        self.stdout.write("🟢 Sincronizando resultados recientes...")
        
        cache_key = f"recent_results_{api_name}"
        
        if not options['force_update']:
            cached_data = cache.get(cache_key)
            if cached_data:
                age = timezone.now() - cached_data['timestamp']
                if age.seconds < CACHE_STRATEGIES['match_results']['ttl']:
                    self.stdout.write("✅ Usando datos cacheados (resultados)")
                    return cached_data
        
        if options['dry_run']:
            self.stdout.write("🧪 [DRY RUN] Simulating recent results request")
            return
        
        try:
            with rate_manager.request_context('medium') as context:
                if context.can_proceed:
                    results_data = self.mock_api_call(api_name, 'recent_results')
                    
                    cache.set(
                        cache_key,
                        {
                            'data': results_data,
                            'timestamp': timezone.now(),
                            'source': 'api'
                        },
                        timeout=CACHE_STRATEGIES['match_results']['ttl']
                    )
                    
                    self.stdout.write(f"✅ {len(results_data)} resultados actualizados")
                else:
                    self.stdout.write("⏸️  Postergando resultados por rate limit")
                    
        except Exception as e:
            logger.error(f"Error sincronizando resultados: {e}")

    def mock_api_call(self, api_name, endpoint):
        """Simular llamada a API (reemplazar con implementación real)"""
        # Simular latencia de red
        time.sleep(0.5)
        
        # Datos mock basados en endpoint
        if endpoint == 'live_matches':
            return [
                {'id': 1, 'home': 'Real Madrid', 'away': 'Barcelona', 'status': 'live', 'minute': 67},
                {'id': 2, 'home': 'Liverpool', 'away': 'Arsenal', 'status': 'live', 'minute': 23}
            ]
        elif endpoint == 'upcoming_matches':
            return [
                {'id': 3, 'home': 'Chelsea', 'away': 'Manchester City', 'kickoff': '2024-01-17T20:00:00Z'},
                {'id': 4, 'home': 'PSG', 'away': 'Marseille', 'kickoff': '2024-01-17T21:00:00Z'}
            ]
        elif endpoint == 'recent_results':
            return [
                {'id': 5, 'home': 'Juventus', 'away': 'AC Milan', 'home_score': 2, 'away_score': 1, 'status': 'finished'},
                {'id': 6, 'home': 'Bayern', 'away': 'Dortmund', 'home_score': 0, 'away_score': 3, 'status': 'finished'}
            ]
        
        return []

    def get_smart_schedule_priority(self):
        """Determinar prioridad basada en hora actual"""
        current_hour = timezone.now().hour
        is_weekend = timezone.now().weekday() >= 5
        
        multiplier = SMART_SCHEDULING['weekend_multiplier'] if is_weekend else SMART_SCHEDULING['weekday_multiplier']
        
        if current_hour in SMART_SCHEDULING['peak_hours']:
            return 'high', multiplier * 1.5
        elif current_hour in SMART_SCHEDULING['off_peak_hours']:
            return 'low', multiplier * 0.5
        else:
            return 'medium', multiplier
