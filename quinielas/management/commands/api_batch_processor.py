"""
Sistema de cola de prioridades para requests a APIs externas
Agrupa múltiples requests en batches para optimizar tokens
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import asyncio
import aiohttp
import json
import logging
from collections import deque, defaultdict

logger = logging.getLogger(__name__)

class APIRequestBatcher:
    """Agrupa requests por prioridad y los ejecuta en lotes"""
    
    def __init__(self):
        self.request_queue = defaultdict(deque)  # Por prioridad
        self.batch_size = 10  # Requests por lote
        self.batch_interval = 300  # 5 minutos entre lotes
        
        # Prioridades de requests
        self.priorities = {
            'critical': 1,    # Partidos en vivo
            'high': 2,        # Próximos partidos (próximas 2 horas)
            'medium': 3,      # Estadísticas del día
            'low': 4,         # Datos históricos
            'background': 5   # Sync de datos no urgentes
        }
    
    def add_request(self, endpoint, params, priority='medium', callback=None):
        """Agrega request a la cola de prioridad"""
        request_item = {
            'endpoint': endpoint,
            'params': params,
            'priority': priority,
            'timestamp': timezone.now(),
            'callback': callback,
            'attempts': 0
        }
        
        self.request_queue[priority].append(request_item)
        logger.info(f"Request queued: {endpoint} (priority: {priority})")
    
    def get_next_batch(self):
        """Obtiene el próximo lote de requests por prioridad"""
        batch = []
        
        # Procesar por orden de prioridad
        for priority in sorted(self.priorities.keys(), key=lambda x: self.priorities[x]):
            queue = self.request_queue[priority]
            
            while queue and len(batch) < self.batch_size:
                batch.append(queue.popleft())
        
        return batch
    
    async def execute_batch(self, batch):
        """Ejecuta un lote de requests de forma asíncrona"""
        if not batch:
            return
        
        logger.info(f"Executing batch of {len(batch)} requests")
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            
            for request_item in batch:
                task = self.execute_single_request(session, request_item)
                tasks.append(task)
            
            # Ejecutar todos los requests del lote en paralelo
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Procesar resultados
            for request_item, result in zip(batch, results):
                if isinstance(result, Exception):
                    logger.error(f"Request failed: {request_item['endpoint']} - {str(result)}")
                    self.handle_failed_request(request_item)
                else:
                    logger.info(f"Request successful: {request_item['endpoint']}")
                    if request_item['callback']:
                        request_item['callback'](result)
    
    async def execute_single_request(self, session, request_item):
        """Ejecuta un request individual"""
        url = f"https://api.football-data.org/v4/{request_item['endpoint']}"
        headers = {'X-Auth-Token': 'YOUR_TOKEN'}
        
        async with session.get(url, headers=headers, params=request_item['params']) as response:
            return await response.json()
    
    def handle_failed_request(self, request_item):
        """Maneja requests fallidos con retry"""
        request_item['attempts'] += 1
        
        if request_item['attempts'] < 3:
            # Reintentarlo con menor prioridad
            lower_priority = self.get_lower_priority(request_item['priority'])
            self.request_queue[lower_priority].append(request_item)
            logger.info(f"Retrying request with lower priority: {lower_priority}")
        else:
            logger.error(f"Request permanently failed: {request_item['endpoint']}")
    
    def get_lower_priority(self, current_priority):
        """Obtiene una prioridad menor para reintentos"""
        priority_map = {
            'critical': 'high',
            'high': 'medium',
            'medium': 'low',
            'low': 'background',
            'background': 'background'
        }
        return priority_map.get(current_priority, 'background')


class SmartScheduler:
    """Programador inteligente que decide cuándo hacer requests"""
    
    def __init__(self):
        self.batcher = APIRequestBatcher()
        self.peak_hours = [17, 18, 19, 20, 21]  # Horas pico (5PM-9PM)
        self.off_peak_multiplier = 2  # Más requests en horas no pico
    
    def should_make_request_now(self, priority):
        """Decide si hacer request ahora basado en la hora y prioridad"""
        now = timezone.now()
        current_hour = now.hour
        
        # Requests críticos siempre se permiten
        if priority == 'critical':
            return True
        
        # En horas pico, ser más conservador
        if current_hour in self.peak_hours:
            return priority in ['critical', 'high']
        
        # En horas no pico, permitir más requests
        return True
    
    def schedule_periodic_updates(self):
        """Programa actualizaciones periódicas inteligentes"""
        updates = [
            # Críticos - cada 1 minuto durante partidos
            {'priority': 'critical', 'interval': 60, 'condition': 'has_live_matches'},
            
            # Altos - cada 5 minutos antes de partidos
            {'priority': 'high', 'interval': 300, 'condition': 'upcoming_matches'},
            
            # Medios - cada 15 minutos para estadísticas
            {'priority': 'medium', 'interval': 900, 'condition': 'always'},
            
            # Bajos - cada hora para datos históricos
            {'priority': 'low', 'interval': 3600, 'condition': 'off_peak'},
        ]
        
        return updates


# Comando de Django para ejecutar el sistema
class Command(BaseCommand):
    help = 'Ejecuta el sistema optimizado de requests a API externa'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--mode',
            choices=['batch', 'scheduled', 'emergency'],
            default='scheduled',
            help='Modo de ejecución'
        )
    
    def handle(self, *args, **options):
        mode = options['mode']
        
        if mode == 'batch':
            self.run_batch_mode()
        elif mode == 'scheduled':
            self.run_scheduled_mode()
        elif mode == 'emergency':
            self.run_emergency_mode()
    
    def run_batch_mode(self):
        """Ejecuta lotes de requests acumulados"""
        batcher = APIRequestBatcher()
        
        # Simular agregar requests
        batcher.add_request('matches', {'status': 'LIVE'}, 'critical')
        batcher.add_request('competitions/2014/standings', {}, 'medium')
        
        # Ejecutar lote
        batch = batcher.get_next_batch()
        asyncio.run(batcher.execute_batch(batch))
        
        self.stdout.write(self.style.SUCCESS('Batch execution completed'))
    
    def run_scheduled_mode(self):
        """Ejecuta modo programado continuo"""
        scheduler = SmartScheduler()
        
        self.stdout.write('Starting scheduled mode...')
        
        # Aquí iría el loop principal del scheduler
        # En producción, esto correría como un daemon
        
    def run_emergency_mode(self):
        """Modo de emergencia - solo requests críticos"""
        self.stdout.write(self.style.WARNING('Emergency mode - critical requests only'))
        
        # Solo permitir requests críticos
        # Deshabilitar cache para datos críticos obsoletos
