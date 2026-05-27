"""
Ralu - Classificador de Intenções

Exemplo de uso:
    from src import Ralu
    
    ralu = Ralu()
    result = ralu.process("Manda um email pro João")
"""
import logging
from typing import Dict, Any

from src.client import OllamaClient
from src.classifier import IntentClassifier
from src.models import IntentResult, IntentType
from src.handlers import process_intent, get_handler
from src.config import settings
from src.utils.response_formatter import format_result
from src.utils import tts
import os


# Configura logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class Ralu:
    """
    Classe principal do Ralu.
    
    Combina classificação de intenção com execução de handlers.
    """
    
    def __init__(self, ollama_url: str = None, model: str = None):
        self.client = OllamaClient(base_url=ollama_url, model=model)
        self.classifier = IntentClassifier(client=self.client)
    
    def classify(self, text: str) -> IntentResult:
        """Classifica a intenção do texto"""
        return self.classifier.classify(text)
    
    def process(self, text: str) -> Dict[str, Any]:
        """
        Classifica e processa o texto.
        
        Args:
            text: Texto do usuário
            
        Returns:
            Resultado do processamento com classificação e ação
        """
        # Classifica
        intent_result = self.classify(text)
        
        # Processa
        action_result = process_intent(intent_result)

        # Formata uma mensagem legível para exibição/voz
        try:
            readable = format_result(action_result)
        except Exception:
            readable = action_result.get("message") or "Pronto."

        # Se habilitado, tenta falar a resposta localmente
        try:
            if settings.ralu_tts:
                tts.speak(readable)
        except Exception:
            logging.getLogger(__name__).debug("TTS falhou ao tentar falar a resposta")

        # Se configurado, escreva também em uma outbox para um watcher externo
        try:
            outdir = settings.ralu_tts_outbox
            if outdir:
                # garantir caminho absoluto quando executando fora do container
                tts.write_outbox(readable, outdir)
        except Exception:
            logging.getLogger(__name__).debug("Falha ao escrever mensagem na outbox TTS")

        return {
            "classification": intent_result.to_dict(),
            "result": action_result,
            "readable_message": readable
        }
    
    def is_ready(self) -> bool:
        """Verifica se o sistema está pronto"""
        return self.client.is_healthy() and self.client.model_exists()


# Exports
__all__ = [
    "Ralu",
    "IntentClassifier",
    "IntentResult",
    "IntentType",
    "OllamaClient",
    "process_intent",
    "get_handler",
    "settings",
]
