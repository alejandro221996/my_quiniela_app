"""
Comando para limpiar el cache del sistema de quinielas
"""
from django.core.management.base import BaseCommand
from django.core.cache import cache


class Command(BaseCommand):
    help = 'Limpia todas las cachés del sistema de quinielas'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            help='Tipo específico de cache a limpiar (stats, ranking, partidos, all)',
            default='all'
        )
    
    def handle(self, *args, **options):
        cache_type = options['type']
        
        if cache_type == 'all':
            cache.clear()
            self.stdout.write(
                self.style.SUCCESS('✅ Todas las cachés han sido limpiadas')
            )
        else:
            # Limpiar cachés específicas por tipo
            keys_to_delete = []
            
            if cache_type == 'stats':
                # Limpiar estadísticas de usuarios (necesitaríamos enumerar usuarios)
                self.stdout.write('🔧 Limpieza de estadísticas específicas requiere implementación adicional')
            elif cache_type == 'ranking':
                keys_to_delete.append('ranking_global')
            elif cache_type == 'partidos':
                keys_to_delete.extend([
                    'proximos_partidos:10',
                    'proximos_partidos:20',
                    'jornadas_activas'
                ])
            
            for key in keys_to_delete:
                cache.delete(key)
                self.stdout.write(f'🗑️  Eliminada cache: {key}')
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Cachés de tipo "{cache_type}" limpiadas')
            )
