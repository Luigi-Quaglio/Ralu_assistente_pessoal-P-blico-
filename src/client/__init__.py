"""
Cliente para comunicação com Ollama
"""
import requests
import json
import re
import logging
from typing import Dict, Any, Optional

from src.config import settings

logger = logging.getLogger(__name__)


class OllamaClient:
    """Cliente HTTP para API do Ollama"""
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None
    ):
        self.base_url = base_url or settings.ollama_base_url
        self.model = model or settings.ollama_model
        self.timeout = timeout or settings.request_timeout
    
    def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Gera uma resposta do modelo.
        
        Args:
            prompt: Texto de entrada
            **kwargs: Parâmetros adicionais para a API
            
        Returns:
            Resposta da API do Ollama
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            **kwargs
        }
        
        logger.debug(f"Enviando request para Ollama: {prompt[:50]}...")
        
        response = requests.post(
            f"{self.base_url}/api/generate",
            json=payload,
            timeout=self.timeout
        )
        response.raise_for_status()
        
        return response.json()
    
    def generate_json(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Gera uma resposta e parseia como JSON.
        
        Args:
            prompt: Texto de entrada
            **kwargs: Parâmetros adicionais
            
        Returns:
            Resposta parseada como JSON
        """
        result = self.generate(prompt, format="json", **kwargs)
        response_text = result.get("response", "")
        
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Tenta extrair JSON da resposta
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            raise ValueError(f"Resposta inválida do modelo: {response_text}")
    
    def is_healthy(self) -> bool:
        """Verifica se o servidor Ollama está respondendo"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False
    
    def model_exists(self) -> bool:
        """Verifica se o modelo está disponível"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return any(m.get("name", "").startswith(self.model) for m in models)
            return False
        except requests.RequestException:
            return False
