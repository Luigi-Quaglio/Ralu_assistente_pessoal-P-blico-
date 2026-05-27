"""
Handlers para processamento de intenções
"""
from typing import Dict, Type

from src.models import IntentType, IntentResult
from src.handlers.base import BaseHandler
from src.handlers.email_handler import EmailHandler
from src.handlers.add_event_handler import AddEventHandler
from src.handlers.query_event_handler import QueryEventHandler
from src.handlers.unknown_handler import UnknownHandler


# Registro de handlers por tipo de intenção
HANDLER_REGISTRY: Dict[IntentType, Type[BaseHandler]] = {
    IntentType.SEND_EMAIL: EmailHandler,
    IntentType.ADD_EVENT: AddEventHandler,
    IntentType.QUERY_EVENT: QueryEventHandler,
    IntentType.UNKNOWN: UnknownHandler,
}


def get_handler(intent_type: IntentType) -> BaseHandler:
    """
    Obtém o handler correspondente ao tipo de intenção.
    
    Args:
        intent_type: Tipo da intenção
        
    Returns:
        Instância do handler apropriado
    """
    handler_class = HANDLER_REGISTRY.get(intent_type, UnknownHandler)
    return handler_class()


def process_intent(intent_result: IntentResult) -> Dict:
    """
    Processa uma intenção classificada.
    
    Args:
        intent_result: Resultado da classificação
        
    Returns:
        Resultado do processamento
    """
    handler = get_handler(intent_result.intent)
    return handler.handle(intent_result)
