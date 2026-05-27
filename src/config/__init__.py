"""
Configurações do projeto Ralu
"""
from dataclasses import dataclass
from typing import Optional
import os


@dataclass
class Settings:
    """Configurações da aplicação"""
    
    # Ollama
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "ralu")
    
    # Timeouts (aumentado para primeira execução que carrega modelo)
    request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "120"))
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    # Text-to-speech (ativa se RALU_TTS=true)
    ralu_tts: bool = False
    # Diretório outbox para TTS externo (container escreve arquivos aqui)
    ralu_tts_outbox: str | None = None
    
    @classmethod
    def from_env(cls) -> "Settings":
        """Carrega configurações do ambiente"""
        # Lê variável de ambiente para TTS
        ralu_tts_env = os.getenv("RALU_TTS", "false").lower() in ("1", "true", "yes")
        ralu_tts_outbox = os.getenv("RALU_TTS_OUTBOX_DIR") or None
        return cls(ralu_tts=ralu_tts_env, ralu_tts_outbox=ralu_tts_outbox)


# Instância global de configurações
settings = Settings.from_env()
