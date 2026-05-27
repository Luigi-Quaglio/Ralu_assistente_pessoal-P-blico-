"""
Utilitários para parsing de datas em linguagem natural
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple
import re


def parse_data_natural(texto: str) -> Optional[datetime]:
    """
    Converte texto em linguagem natural para datetime.
    
    Exemplos:
        - "hoje" -> data de hoje
        - "amanhã" -> data de amanhã
        - "segunda" -> próxima segunda-feira
        - "15/03" -> 15 de março
        - "15/03/2026" -> 15 de março de 2026
    """
    if not texto:
        return None
    
    texto = texto.lower().strip()
    agora = datetime.now()
    
    # Hoje
    if texto == "hoje":
        return agora.replace(hour=9, minute=0, second=0, microsecond=0)
    
    # Amanhã
    if texto in ["amanhã", "amanha"]:
        return (agora + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
    
    # Depois de amanhã
    if texto in ["depois de amanhã", "depois de amanha"]:
        return (agora + timedelta(days=2)).replace(hour=9, minute=0, second=0, microsecond=0)
    
    # Dias da semana
    dias_semana = {
        "segunda": 0, "segunda-feira": 0,
        "terça": 1, "terca": 1, "terça-feira": 1,
        "quarta": 2, "quarta-feira": 2,
        "quinta": 3, "quinta-feira": 3,
        "sexta": 4, "sexta-feira": 4,
        "sábado": 5, "sabado": 5,
        "domingo": 6
    }
    
    if texto in dias_semana:
        dia_alvo = dias_semana[texto]
        dia_atual = agora.weekday()
        dias_ate = (dia_alvo - dia_atual) % 7
        if dias_ate == 0:
            dias_ate = 7  # Próxima semana se for o mesmo dia
        return (agora + timedelta(days=dias_ate)).replace(hour=9, minute=0, second=0, microsecond=0)
    
    # Formato DD/MM ou DD/MM/YYYY
    match = re.match(r"(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?", texto)
    if match:
        dia = int(match.group(1))
        mes = int(match.group(2))
        ano = int(match.group(3)) if match.group(3) else agora.year
        if ano < 100:
            ano += 2000
        try:
            return datetime(ano, mes, dia, 9, 0, 0)
        except ValueError:
            pass
    
    # Formato "dia X" ou apenas "X" (número do dia)
    match = re.match(r"(?:dia\s+)?(\d{1,2})(?:\s+de\s+(\w+))?(?:\s+(?:de\s+)?(\d{4}))?$", texto)
    if match:
        dia = int(match.group(1))
        mes_texto = match.group(2)
        ano = int(match.group(3)) if match.group(3) else agora.year
        
        meses = {
            "janeiro": 1, "fevereiro": 2, "março": 3, "marco": 3,
            "abril": 4, "maio": 5, "junho": 6,
            "julho": 7, "agosto": 8, "setembro": 9,
            "outubro": 10, "novembro": 11, "dezembro": 12
        }
        
        if mes_texto and mes_texto.lower() in meses:
            mes = meses[mes_texto.lower()]
        else:
            # Se não especificou mês, usa o mês atual ou próximo
            mes = agora.month
            # Se o dia já passou neste mês, assume próximo mês
            if dia < agora.day:
                mes += 1
                if mes > 12:
                    mes = 1
                    ano += 1
        
        try:
            return datetime(ano, mes, dia, 9, 0, 0)
        except ValueError:
            pass
    
    # Formato "X de <mês>" sem "dia" no início
    match = re.match(r"(\d{1,2})\s+de\s+(\w+)(?:\s+(?:de\s+)?(\d{4}))?$", texto)
    if match:
        dia = int(match.group(1))
        mes_texto = match.group(2).lower()
        ano = int(match.group(3)) if match.group(3) else agora.year
        
        meses = {
            "janeiro": 1, "fevereiro": 2, "março": 3, "marco": 3,
            "abril": 4, "maio": 5, "junho": 6,
            "julho": 7, "agosto": 8, "setembro": 9,
            "outubro": 10, "novembro": 11, "dezembro": 12
        }
        
        if mes_texto in meses:
            mes = meses[mes_texto]
            try:
                return datetime(ano, mes, dia, 9, 0, 0)
            except ValueError:
                pass
    
    return None


def parse_hora_natural(texto: str) -> Optional[Tuple[int, int]]:
    """
    Converte texto de hora para tupla (hora, minuto).
    
    Exemplos:
        - "14h" -> (14, 0)
        - "14:30" -> (14, 30)
        - "2 da tarde" -> (14, 0)
        - "10 da manhã" -> (10, 0)
    """
    if not texto:
        return None
    
    texto = texto.lower().strip()
    
    # Formato HHh ou HHhMM
    match = re.match(r"(\d{1,2})h(\d{2})?", texto)
    if match:
        hora = int(match.group(1))
        minuto = int(match.group(2)) if match.group(2) else 0
        return (hora, minuto)
    
    # Formato HH:MM
    match = re.match(r"(\d{1,2}):(\d{2})", texto)
    if match:
        hora = int(match.group(1))
        minuto = int(match.group(2))
        return (hora, minuto)
    
    # "X da tarde/manhã/noite"
    match = re.match(r"(\d{1,2})\s*(da\s*)?(tarde|manhã|manha|noite)", texto)
    if match:
        hora = int(match.group(1))
        periodo = match.group(3)
        if periodo in ["tarde", "noite"] and hora < 12:
            hora += 12
        return (hora, 0)
    
    # Apenas número (assume hora)
    match = re.match(r"^(\d{1,2})$", texto)
    if match:
        hora = int(match.group(1))
        return (hora, 0)
    
    return None


def parse_date_range(texto: str) -> Optional[Tuple[str, str]]:
    """
    Detecta e separa ranges de datas como "9-20 de março" ou "9 a 20 de março".
    
    Returns:
        Tupla (data_inicio, data_fim) ou None se não for um range
    """
    if not texto:
        return None
    
    texto = texto.strip()
    
    # Padrão: "9-20 de março" ou "9 - 20 de março"
    match = re.match(r"(\d{1,2})\s*[-–—]\s*(\d{1,2})\s+de\s+(\w+)(?:\s+(?:de\s+)?(\d{4}))?$", texto, re.IGNORECASE)
    if match:
        dia_inicio = match.group(1)
        dia_fim = match.group(2)
        mes = match.group(3)
        ano = match.group(4) or ""
        ano_suffix = f" de {ano}" if ano else ""
        return (f"{dia_inicio} de {mes}{ano_suffix}", f"{dia_fim} de {mes}{ano_suffix}")
    
    # Padrão: "9 a 20 de março" ou "9 ao 20 de março"
    match = re.match(r"(\d{1,2})\s+(?:a|ao|até)\s+(\d{1,2})\s+de\s+(\w+)(?:\s+(?:de\s+)?(\d{4}))?$", texto, re.IGNORECASE)
    if match:
        dia_inicio = match.group(1)
        dia_fim = match.group(2)
        mes = match.group(3)
        ano = match.group(4) or ""
        ano_suffix = f" de {ano}" if ano else ""
        return (f"{dia_inicio} de {mes}{ano_suffix}", f"{dia_fim} de {mes}{ano_suffix}")
    
    # Padrão: "dia 9 ao dia 20 de março"
    match = re.match(r"dia\s+(\d{1,2})\s+(?:a|ao|até)\s+(?:dia\s+)?(\d{1,2})\s+de\s+(\w+)(?:\s+(?:de\s+)?(\d{4}))?$", texto, re.IGNORECASE)
    if match:
        dia_inicio = match.group(1)
        dia_fim = match.group(2)
        mes = match.group(3)
        ano = match.group(4) or ""
        ano_suffix = f" de {ano}" if ano else ""
        return (f"{dia_inicio} de {mes}{ano_suffix}", f"{dia_fim} de {mes}{ano_suffix}")
    
    return None


def parse_data_hora(data_texto: str, hora_texto: str = None) -> Optional[datetime]:
    """
    Combina parsing de data e hora.
    
    Args:
        data_texto: Texto da data (ex: "amanhã", "15/03")
        hora_texto: Texto da hora (ex: "14h", "10:30")
        
    Returns:
        datetime combinado ou None
    """
    data = parse_data_natural(data_texto)
    
    if not data:
        return None
    
    if hora_texto:
        hora = parse_hora_natural(hora_texto)
        if hora:
            data = data.replace(hour=hora[0], minute=hora[1])
    
    return data
