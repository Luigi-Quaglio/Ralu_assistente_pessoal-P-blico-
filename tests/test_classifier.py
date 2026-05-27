"""
Testes para o classificador de intenções
"""
import pytest
from unittest.mock import Mock, patch

from src.models import IntentResult, IntentType
from src.classifier import IntentClassifier
from src.handlers import get_handler, process_intent
from src.handlers.email_handler import EmailHandler
from src.handlers.add_event_handler import AddEventHandler
from src.handlers.query_event_handler import QueryEventHandler


class TestIntentResult:
    """Testes para IntentResult"""
    
    def test_from_dict_send_email(self):
        data = {
            "intent": "send_email",
            "confidence": 0.95,
            "entities": {"recipient": "João"}
        }
        result = IntentResult.from_dict(data)
        
        assert result.intent == IntentType.SEND_EMAIL
        assert result.confidence == 0.95
        assert result.entities["recipient"] == "João"
    
    def test_from_dict_unknown_intent(self):
        data = {
            "intent": "invalid_intent",
            "confidence": 0.5,
            "entities": {}
        }
        result = IntentResult.from_dict(data)
        
        assert result.intent == IntentType.UNKNOWN
    
    def test_to_dict(self):
        result = IntentResult(
            intent=IntentType.ADD_EVENT,
            confidence=0.9,
            entities={"event_name": "Reunião"}
        )
        
        data = result.to_dict()
        assert data["intent"] == "add_event"
        assert data["confidence"] == 0.9


class TestHandlers:
    """Testes para handlers"""
    
    def test_get_handler_email(self):
        handler = get_handler(IntentType.SEND_EMAIL)
        assert isinstance(handler, EmailHandler)
    
    def test_get_handler_add_event(self):
        handler = get_handler(IntentType.ADD_EVENT)
        assert isinstance(handler, AddEventHandler)
    
    def test_get_handler_query_event(self):
        handler = get_handler(IntentType.QUERY_EVENT)
        assert isinstance(handler, QueryEventHandler)
    
    def test_email_handler_validate_missing_recipient(self):
        handler = EmailHandler()
        result = IntentResult(
            intent=IntentType.SEND_EMAIL,
            confidence=0.9,
            entities={}
        )
        
        is_valid, error = handler.validate(result)
        assert not is_valid
        assert "Destinatário" in error
    
    def test_email_handler_validate_with_recipient(self):
        handler = EmailHandler()
        result = IntentResult(
            intent=IntentType.SEND_EMAIL,
            confidence=0.9,
            entities={"recipient": "João"}
        )
        
        is_valid, error = handler.validate(result)
        assert is_valid
        assert error is None
    
    def test_email_handler_execute(self):
        handler = EmailHandler()
        result = IntentResult(
            intent=IntentType.SEND_EMAIL,
            confidence=0.9,
            entities={"recipient": "João", "subject": "Teste"}
        )
        
        response = handler.execute(result)
        assert response["success"] is True
        assert response["action"] == "send_email"
        assert response["data"]["recipient"] == "João"


class TestIntentClassifier:
    """Testes para o classificador"""
    
    @patch('src.classifier.OllamaClient')
    def test_classify_success(self, mock_client_class):
        mock_client = Mock()
        mock_client.generate_json.return_value = {
            "intent": "send_email",
            "confidence": 0.95,
            "entities": {"recipient": "João"}
        }
        
        classifier = IntentClassifier(client=mock_client)
        result = classifier.classify("Manda email pro João")
        
        assert result.intent == IntentType.SEND_EMAIL
        assert result.confidence == 0.95


# Exemplos de testes de integração (requer Ollama rodando)
class TestIntegration:
    """Testes de integração (requer servidor Ollama)"""
    
    @pytest.mark.integration
    def test_full_flow(self):
        """Teste completo do fluxo"""
        from src.ralu import Ralu
        
        ralu = Ralu()
        if not ralu.is_ready():
            pytest.skip("Ollama não disponível")
        
        result = ralu.process("Manda email pro João sobre a reunião")
        
        assert "classification" in result
        assert "result" in result
        assert result["classification"]["intent"] == "send_email"
