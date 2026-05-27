"""
Handler para consultar eventos na agenda
"""
import logging
from typing import Any, Dict, Optional, List

from src.models import IntentResult, IntentType
from src.handlers.base import BaseHandler
from src.database import EventoRepository, Evento, init_database
from src.utils import parse_data_natural

logger = logging.getLogger(__name__)


class QueryEventHandler(BaseHandler):
    """Handler para intenção de consultar eventos"""
    
    intent_type = IntentType.QUERY_EVENT
    
    def __init__(self):
        init_database()  # Garante que o banco existe
        self.repo = EventoRepository()
    
    def validate(self, intent_result: IntentResult) -> tuple[bool, Optional[str]]:
        """Consulta de eventos não requer validação específica"""
        return True, None
    
    def execute(self, intent_result: IntentResult) -> Dict[str, Any]:
        """
        Consulta eventos na agenda (SQLite).
        """
        entities = intent_result.entities
        data_texto = entities.get("date")
        event_name = entities.get("event_name")
        
        try:
            eventos: List[Evento] = []
            
            # Consulta por data
            if data_texto:
                data = parse_data_natural(data_texto)
                if data:
                    eventos = self.repo.buscar_por_data(data)
                    logger.info(f"Consultando eventos para {data.strftime('%d/%m/%Y')}")
                else:
                    # Se não conseguiu parsear a data, busca próximos 7 dias
                    eventos = self.repo.buscar_proximos(7)
            elif event_name:
                # Busca por nome do evento
                eventos = self.repo.buscar(event_name)
            else:
                # Sem filtros, retorna eventos de hoje e próximos dias
                eventos = self.repo.buscar_proximos(7)
            
            # Formata resultado
            eventos_formatados = []
            for e in eventos:
                eventos_formatados.append({
                    "id": e.id,
                    "nome": e.nome,
                    "data": e.data.strftime("%d/%m/%Y %H:%M") if e.data else None,
                    "local": e.local,
                    "participante": e.participante
                })
            
            if eventos:
                msg = f"Encontrei {len(eventos)} evento(s)"
            else:
                msg = "Nenhum evento encontrado"
            
            return {
                "success": True,
                "action": "query_event",
                "intent": intent_result.intent.value,
                "data": {
                    "count": len(eventos),
                    "eventos": eventos_formatados
                },
                "message": msg
            }
            
        except Exception as e:
            logger.error(f"Erro ao consultar eventos: {e}")
            return {
                "success": False,
                "action": "query_event",
                "intent": intent_result.intent.value,
                "error": str(e),
                "message": f"Erro ao consultar eventos: {e}"
            }
