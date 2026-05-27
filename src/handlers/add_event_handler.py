"""
Handler para adicionar eventos na agenda
"""
import logging
from typing import Any, Dict, Optional

from src.models import IntentResult, IntentType
from src.handlers.base import BaseHandler
from src.database import EventoRepository, Evento, init_database
from src.utils import parse_data_hora
from src.utils.date_parser import parse_date_range

logger = logging.getLogger(__name__)


class AddEventHandler(BaseHandler):
    """Handler para intenção de adicionar evento"""
    
    intent_type = IntentType.ADD_EVENT
    
    def __init__(self):
        init_database()  # Garante que o banco existe
        self.repo = EventoRepository()
    
    def validate(self, intent_result: IntentResult) -> tuple[bool, Optional[str]]:
        """Valida se tem informações mínimas do evento"""
        entities = intent_result.entities
        
        if not entities.get("event_name") and not entities.get("subject"):
            return False, "Nome do evento não especificado"
        
        return True, None
    
    def execute(self, intent_result: IntentResult) -> Dict[str, Any]:
        """
        Adiciona evento na agenda (SQLite).
        Se falta data/hora, retorna pending para follow-up.
        Suporta eventos com duração (data_fim).
        """
        entities = intent_result.entities
        
        event_name = entities.get("event_name") or entities.get("subject")
        data_texto = entities.get("date")
        hora_texto = entities.get("time")
        data_fim_texto = entities.get("date_end")
        hora_fim_texto = entities.get("time_end")
        participante = entities.get("participant") or entities.get("participants")
        local = entities.get("location") or entities.get("local")
        
        # Fallback: se data contém um range (ex: "9-20 de março"), separa em data e data_fim
        if data_texto and not data_fim_texto:
            date_range = parse_date_range(data_texto)
            if date_range:
                data_texto, data_fim_texto = date_range
                logger.info(f"Range de datas detectado: {data_texto} -> {data_fim_texto}")
        
        # Verifica se falta data/hora
        if not data_texto and not hora_texto:
            logger.info(f"Evento '{event_name}' sem data/hora - solicitando follow-up")
            return {
                "success": False,
                "action": "add_event",
                "intent": intent_result.intent.value,
                "needs_followup": True,
                "followup_type": "datetime",
                "pending_event": {
                    "event_name": event_name,
                    "participante": participante,
                    "local": local,
                    "raw_text": intent_result.raw_text
                },
                "message": "Quando?"
            }
        
        # Parse da data/hora de início
        data_evento = parse_data_hora(data_texto, hora_texto) if data_texto else None
        
        # Parse da data/hora de fim (se houver)
        data_evento_fim = None
        if data_fim_texto or hora_fim_texto:
            # Se só tiver hora_fim, usa a mesma data do início
            if hora_fim_texto and not data_fim_texto:
                data_evento_fim = parse_data_hora(data_texto, hora_fim_texto)
            else:
                data_evento_fim = parse_data_hora(data_fim_texto, hora_fim_texto)
        
        # Cria o evento no banco
        return self._criar_evento(event_name, data_evento, data_evento_fim, participante, local, intent_result.raw_text)
    
    def execute_with_datetime(self, pending_event: Dict, data_texto: str, hora_texto: str = None) -> Dict[str, Any]:
        """
        Completa a criação do evento com data/hora fornecida.
        """
        event_name = pending_event.get("event_name")
        participante = pending_event.get("participante")
        local = pending_event.get("local")
        raw_text = pending_event.get("raw_text", "")
        
        # Parse da data/hora
        data_evento = parse_data_hora(data_texto, hora_texto)
        
        return self._criar_evento(event_name, data_evento, None, participante, local, raw_text)
    
    def _criar_evento(self, event_name: str, data_evento, data_evento_fim, participante: str, local: str, raw_text: str) -> Dict[str, Any]:
        """Cria o evento no banco de dados"""
        try:
            evento = Evento(
                nome=event_name,
                data=data_evento,
                data_fim=data_evento_fim,
                descricao=raw_text,
                participante=participante,
                local=local
            )
            
            evento = self.repo.criar(evento)
            logger.info(f"Evento criado: {evento.nome} (ID: {evento.id})")
            
            # Mensagem personalizada para eventos com duração
            if data_evento_fim:
                duracao_msg = self._formatar_duracao(data_evento, data_evento_fim)
                msg = f"Evento '{event_name}' criado ({duracao_msg})!"
            else:
                msg = f"Evento '{event_name}' criado com sucesso! (ID: {evento.id})"
            
            return {
                "success": True,
                "action": "add_event",
                "intent": IntentType.ADD_EVENT.value,
                "data": evento.to_dict(),
                "message": msg
            }
            
        except Exception as e:
            logger.error(f"Erro ao criar evento: {e}")
            return {
                "success": False,
                "action": "add_event",
                "intent": IntentType.ADD_EVENT.value,
                "error": str(e),
                "message": f"Erro ao criar evento: {e}"
            }
    
    def _formatar_duracao(self, inicio, fim) -> str:
        """Formata a duração do evento de forma legível"""
        if not inicio or not fim:
            return ""
        
        # Mesmo dia
        if inicio.date() == fim.date():
            return f"{inicio.strftime('%d/%m')} das {inicio.strftime('%H:%M')} às {fim.strftime('%H:%M')}"
        
        # Dias diferentes
        return f"{inicio.strftime('%d/%m')} a {fim.strftime('%d/%m')}"
