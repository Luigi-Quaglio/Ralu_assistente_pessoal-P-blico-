"""
Módulo de TTS usando pyttsx3 (Windows SAPI).
Interface compatível com o restante do projeto Ralu.
Voz padrão: Microsoft Maria Desktop - Portuguese (Brazil)
"""
import logging

logger = logging.getLogger(__name__)

# ID da voz Microsoft Maria Desktop - Portuguese (Brazil)
VOICE_MARIA = (
    r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens"
    r"\TTS_MS_PT-BR_MARIA_11.0"
)


def falar_com_piper(text: str) -> bool:
    """Fala o texto usando a voz Microsoft Maria (PT-BR) via pyttsx3.

    Retorna True se o áudio foi reproduzido com sucesso.
    """
    if not text:
        return False
    try:
        import pyttsx3

        engine = pyttsx3.init()
        engine.setProperty("voice", VOICE_MARIA)
        engine.setProperty("rate", 160)   # velocidade (palavras/min)
        engine.setProperty("volume", 1.0)

        engine.say(text)
        engine.runAndWait()
        engine.stop()
        return True
    except Exception as e:
        logger.debug(f"TTS falhou: {e}")
        return False
