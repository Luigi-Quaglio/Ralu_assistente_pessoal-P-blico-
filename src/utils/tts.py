"""
Wrapper simples para TTS. Tenta reutilizar o `tts_piper.py` na raiz do projeto
se disponível. A função `speak` falha silenciosamente se TTS não estiver
configurado ou não for suportado no ambiente (ex: dentro do container).
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def speak(text: str) -> bool:
    """Tenta falar o texto usando o módulo externo `tts_piper`.

    Retorna True se áudio foi reproduzido com sucesso, False caso contrário.
    """
    if not text:
        return False

    try:
        # Importa o módulo de TTS que existe fora do pacote `src` (na raiz)
        import tts_piper

        # tts_piper.falar_com_piper devolve bool
        return tts_piper.falar_com_piper(text)
    except Exception as e:
        logger.debug(f"TTS não disponível ou falhou: {e}")
        return False


def write_outbox(text: str, outdir: str) -> bool:
    """Escreve o texto em um arquivo na pasta `outdir` para um watcher externo ler.

    Gera um arquivo com timestamp e retorna True se escrito com sucesso.
    """
    try:
        import os
        from datetime import datetime
        from uuid import uuid4

        if not outdir:
            return False

        os.makedirs(outdir, exist_ok=True)
        ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        filename = f"ralu_{ts}_{uuid4().hex}.txt"
        path = os.path.join(outdir, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        logger.info(f"Escrito arquivo TTS outbox: {path}")
        return True
    except Exception as e:
        logger.debug(f"Falha ao escrever outbox: {e}")
        return False
