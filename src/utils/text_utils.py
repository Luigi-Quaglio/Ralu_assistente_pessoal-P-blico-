"""
Utilitários de texto
"""
import unicodedata
from typing import Optional


def normalizar_texto(texto: Optional[str]) -> str:
    """
    Normaliza texto removendo acentos e convertendo para minúsculo.
    
    Exemplos:
        "João" -> "joao"
        "CAFÉ" -> "cafe"
        "São Paulo" -> "sao paulo"
    """
    if not texto:
        return ""
    
    # Normaliza para forma NFD (decompõe caracteres acentuados)
    # Ex: "é" vira "e" + acento combinante
    texto_normalizado = unicodedata.normalize('NFD', texto)
    
    # Remove os caracteres combinantes (acentos)
    texto_sem_acento = ''.join(
        char for char in texto_normalizado
        if unicodedata.category(char) != 'Mn'  # Mn = Mark, Nonspacing (acentos)
    )
    
    # Converte para minúsculo
    return texto_sem_acento.lower()


def textos_similares(texto1: Optional[str], texto2: Optional[str]) -> bool:
    """
    Verifica se dois textos são iguais ignorando acentos e case.
    
    Exemplos:
        "João" == "joao" -> True
        "CAFÉ" == "cafe" -> True
    """
    return normalizar_texto(texto1) == normalizar_texto(texto2)


def texto_contem(texto: Optional[str], termo: Optional[str]) -> bool:
    """
    Verifica se texto contém termo, ignorando acentos e case.
    
    Exemplos:
        "João da Silva" contém "joao" -> True
        "CAFÉ" contém "cafe" -> True
    """
    return normalizar_texto(termo) in normalizar_texto(texto)
