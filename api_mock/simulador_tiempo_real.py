#!/usr/bin/env python3
"""
Simulador de partidos en tiempo real para testing
Genera eventos aleatorios realistas durante un partido
"""

import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any

class SimuladorPartidoTiempoReal:
    def __init__(self):
        self.eventos_posibles = {
            'gol': {'probabilidad': 0.05, 'impacto': 'alto'},
            'tarjeta_amarilla': {'probabilidad': 0.08, 'impacto': 'medio'},
            'tarjeta_roja': {'probabilidad': 0.01, 'impacto': 'alto'},
            'cambio': {'probabilidad': 0.03, 'impacto': 'medio'},
            'corner': {'probabilidad': 0.12, 'impacto': 'bajo'},
            'falta': {'probabilidad': 0.15, 'impacto': 'bajo'},
            'fuera_juego': {'probabilidad': 0.10, 'impacto': 'bajo'},
            'tiro_libre': {'probabilidad': 0.06, 'impacto': 'medio'},
            'penal': {'probabilidad': 0.008, 'impacto': 'alto'}
        }
        
        self.jugadores_por_equipo = [
            "Portero Principal", "Defensa Central 1", "Defensa Central 2", 
            "Lateral Derecho", "Lateral Izquierdo", "Mediocentro Defensivo",
            "Mediocentro 1", "Mediocentro 2", "Extremo Derecho", 
            "Extremo Izquierdo", "Delantero Centro"
        ]
    
    def simular_minuto(self, minuto: int, estado_actual: Dict) -> Dict:
        """Simula eventos en un minuto específico"""
        eventos = []
        
        # Mayor probabilidad de eventos en minutos clave
        multiplicador = self._get_multiplicador_minuto(minuto)
        
        for evento, config in self.eventos_posibles.items():
            probabilidad = config['probabilidad'] * multiplicador
            
            if random.random() < probabilidad:
                evento_data = self._generar_evento(evento, minuto, estado_actual)
                if evento_data:
                    eventos.append(evento_data)
        
        return {
            'minuto': minuto,
            'eventos': eventos,
            'estado_actualizado': self._actualizar_estado(estado_actual, eventos)
        }
    
    def _get_multiplicador_minuto(self, minuto: int) -> float:
        """Ajusta probabilidades según el minuto del partido"""
        if 1 <= minuto <= 15:  # Inicio nervioso
            return 1.2
        elif 40 <= minuto <= 45:  # Final primer tiempo
            return 1.4
        elif 60 <= minuto <= 75:  # Cambios tácticos
            return 1.3
        elif 85 <= minuto <= 90:  # Final desesperado
            return 1.8
        elif minuto > 90:  # Tiempo adicional
            return 2.0
        else:
            return 1.0
    
    def _generar_evento(self, tipo: str, minuto: int, estado: Dict) -> Dict:
        """Genera un evento específico"""
        equipo = random.choice(['local', 'visitante'])
        jugador = random.choice(self.jugadores_por_equipo)
        
        eventos_especificos = {
            'gol': {
                'tipo': 'gol',
                'jugador': jugador,
                'equipo': equipo,
                'descripcion': random.choice([
                    "Disparo desde fuera del área",
                    "Cabezazo tras centro",
                    "Definición dentro del área",
                    "Tiro libre directo",
                    "Contraataque letal"
                ])
            },
            'tarjeta_amarilla': {
                'tipo': 'tarjeta_amarilla',
                'jugador': jugador,
                'equipo': equipo,
                'descripcion': random.choice([
                    "Entrada fuerte",
                    "Protesta al árbitro",
                    "Falta táctica",
                    "Pérdida de tiempo"
                ])
            },
            'penal': {
                'tipo': 'penal',
                'jugador': jugador,
                'equipo': equipo,
                'descripcion': "Penal señalado por el árbitro",
                'convertido': random.random() > 0.25  # 75% éxito
            }
        }
        
        base_evento = {
            'minuto': minuto,
            'timestamp': datetime.now().isoformat()
        }
        
        if tipo in eventos_especificos:
            base_evento.update(eventos_especificos[tipo])
        
        return base_evento
    
    def _actualizar_estado(self, estado: Dict, eventos: List[Dict]) -> Dict:
        """Actualiza el estado del partido con los nuevos eventos"""
        nuevo_estado = estado.copy()
        
        for evento in eventos:
            if evento['tipo'] == 'gol':
                if evento['equipo'] == 'local':
                    nuevo_estado['goles_local'] = nuevo_estado.get('goles_local', 0) + 1
                else:
                    nuevo_estado['goles_visitante'] = nuevo_estado.get('goles_visitante', 0) + 1
        
        return nuevo_estado
    
    def simular_partido_completo(self, partido_id: int) -> Dict:
        """Simula un partido completo minuto a minuto"""
        estado_inicial = {
            'partido_id': partido_id,
            'goles_local': 0,
            'goles_visitante': 0,
            'tarjetas_amarillas_local': 0,
            'tarjetas_amarillas_visitante': 0,
            'tarjetas_rojas_local': 0,
            'tarjetas_rojas_visitante': 0
        }
        
        minutos_simulados = []
        estado_actual = estado_inicial
        
        # Simular 90 minutos + tiempo adicional
        tiempo_adicional = random.randint(1, 6)
        total_minutos = 90 + tiempo_adicional
        
        for minuto in range(1, total_minutos + 1):
            simulacion_minuto = self.simular_minuto(minuto, estado_actual)
            minutos_simulados.append(simulacion_minuto)
            estado_actual = simulacion_minuto['estado_actualizado']
        
        return {
            'partido_id': partido_id,
            'estado_final': estado_actual,
            'simulacion_completa': minutos_simulados,
            'duracion_total': total_minutos,
            'eventos_destacados': self._extraer_eventos_destacados(minutos_simulados)
        }
    
    def _extraer_eventos_destacados(self, simulacion: List[Dict]) -> List[Dict]:
        """Extrae solo los eventos más importantes"""
        eventos_importantes = []
        
        for minuto_data in simulacion:
            for evento in minuto_data['eventos']:
                if evento['tipo'] in ['gol', 'tarjeta_roja', 'penal']:
                    eventos_importantes.append(evento)
        
        return eventos_importantes

# Función para generar datos de ejemplo
def generar_datos_ejemplo():
    simulador = SimuladorPartidoTiempoReal()
    
    # Simular 3 partidos
    simulaciones = {}
    for partido_id in [20, 21, 22]:
        simulaciones[f"partido_{partido_id}"] = simulador.simular_partido_completo(partido_id)
    
    return simulaciones

if __name__ == "__main__":
    datos = generar_datos_ejemplo()
    print(json.dumps(datos, indent=2, ensure_ascii=False))
