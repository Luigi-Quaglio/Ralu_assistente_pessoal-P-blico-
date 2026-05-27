"""
Classificador de intenções usando Ollama
"""
import logging
from typing import Optional

from src.client import OllamaClient
from src.models import IntentResult

logger = logging.getLogger(__name__)


class IntentClassifier:
    """Classificador de intenções usando modelo Ollama"""
    
    def __init__(self, client: Optional[OllamaClient] = None):
        self.client = client or OllamaClient()
    
    def classify(self, text: str) -> IntentResult:
        """
        Classifica a intenção de um texto.
        
        Args:
            text: Texto para classificar
            
        Returns:
            IntentResult com a intenção identificada
        """
        logger.info(f"Classificando: {text[:50]}...")
        
        try:
            response = self.client.generate_json(text)
            result = IntentResult.from_dict(response, raw_text=text)
            logger.info(f"Intenção: {result.intent.value} ({result.confidence:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"Erro ao classificar: {e}")
            from src.models import IntentType
            return IntentResult(
                intent=IntentType.UNKNOWN,
                confidence=0.0,
                raw_text=text
            )
    
    def classify_batch(self, texts: list[str]) -> list[IntentResult]:
        """
        Classifica múltiplos textos.
        
        Args:
            texts: Lista de textos para classificar
            
        Returns:
            Lista de IntentResult
        """
        return [self.classify(text) for text in texts]
