"""
Handler para intenções desconhecidas
"""
from typing import Any, Dict

from src.models import IntentResult, IntentType
from src.handlers.base import BaseHandler


class UnknownHandler(BaseHandler):
    """Handler para intenções não reconhecidas"""
    
    intent_type = IntentType.UNKNOWN
    
    def execute(self, intent_result: IntentResult) -> Dict[str, Any]:
        """Retorna mensagem de intenção não reconhecida"""
        return {
            "success": False,
            "action": "unknown",
            "intent": intent_result.intent.value,
            "message": "Desculpe, não entendi o que você quer fazer.",
            "raw_text": intent_result.raw_text
        }
