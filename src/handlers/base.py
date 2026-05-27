"""
Handler base para processamento de intenções
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from src.models import IntentResult, IntentType


class BaseHandler(ABC):
    """Classe base abstrata para handlers de intenção"""
    
    intent_type: IntentType = IntentType.UNKNOWN
    
    @abstractmethod
    def execute(self, intent_result: IntentResult) -> Dict[str, Any]:
        """
        Executa a ação correspondente à intenção.
        
        Args:
            intent_result: Resultado da classificação
            
        Returns:
            Resultado da execução
        """
        pass
    
    def validate(self, intent_result: IntentResult) -> tuple[bool, Optional[str]]:
        """
        Valida se o intent_result tem as entidades necessárias.
        
        Args:
            intent_result: Resultado da classificação
            
        Returns:
            Tupla (é_válido, mensagem_erro)
        """
        return True, None
    
    def handle(self, intent_result: IntentResult) -> Dict[str, Any]:
        """
        Processa a intenção (valida e executa).
        
        Args:
            intent_result: Resultado da classificação
            
        Returns:
            Resultado da execução ou erro de validação
        """
        is_valid, error = self.validate(intent_result)
        
        if not is_valid:
            return {
                "success": False,
                "error": error,
                "intent": intent_result.intent.value
            }
        
        return self.execute(intent_result)
