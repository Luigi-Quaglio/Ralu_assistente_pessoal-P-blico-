"""
Modelos de dados para intenções
"""
from dataclasses import dataclass, field
from typing import Dict, Optional, Any
from enum import Enum


class IntentType(str, Enum):
    """Tipos de intenções suportadas"""
    SEND_EMAIL = "send_email"
    ADD_EVENT = "add_event"
    QUERY_EVENT = "query_event"
    UNKNOWN = "unknown"


@dataclass
class IntentResult:
    """Resultado da classificação de intenção"""
    intent: IntentType
    confidence: float
    entities: Dict[str, Any] = field(default_factory=dict)
    raw_text: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            "intent": self.intent.value,
            "confidence": self.confidence,
            "entities": self.entities
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], raw_text: Optional[str] = None) -> "IntentResult":
        """Cria instância a partir de dicionário"""
        intent_str = data.get("intent", "unknown")
        try:
            intent = IntentType(intent_str)
        except ValueError:
            intent = IntentType.UNKNOWN
            
        return cls(
            intent=intent,
            confidence=data.get("confidence", 0.0),
            entities=data.get("entities", {}),
            raw_text=raw_text
        )
    
    @property
    def is_known(self) -> bool:
        """Verifica se a intenção é conhecida"""
        return self.intent != IntentType.UNKNOWN
    
    @property
    def is_confident(self, threshold: float = 0.7) -> bool:
        """Verifica se a confiança está acima do threshold"""
        return self.confidence >= threshold
