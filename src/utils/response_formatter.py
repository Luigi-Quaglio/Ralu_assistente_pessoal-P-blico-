"""Formatador simples para transformar resultados de ação em mensagens humanas.

Centraliza as mensagens amigáveis que a IA retorna ao usuário e facilita
a leitura em voz alta.
"""
from datetime import datetime
from typing import Dict, Any, Optional


def _fmt_datetime(dt: Optional[datetime]) -> str:
    """Formata datetime para português legível.

    Exemplos:
      - 2026-03-04 10:00 -> "4 de março às 10h"
      - 2026-03-04 10:30 -> "4 de março às 10:30"
      - se o ano for diferente do atual, inclui o ano: "4 de março de 2027 às 10h"
    """
    if not dt:
        return ""
    try:
        meses = [
            "janeiro", "fevereiro", "março", "abril", "maio", "junho",
            "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"
        ]
        dia = dt.day
        mes = meses[dt.month - 1]
        ano = dt.year
        hora = dt.hour
        minuto = dt.minute

        # Formatar hora
        if minuto == 0:
            hora_str = f"{hora}h"
        else:
            hora_str = f"{hora}:{minuto:02d}"

        # Incluir ano somente se diferente do ano atual
        agora = datetime.now()
        if ano != agora.year:
            return f"{dia} de {mes} de {ano} às {hora_str}"
        return f"{dia} de {mes} às {hora_str}"
    except Exception:
        return str(dt)


def format_result(result: Dict[str, Any]) -> str:
    """Gera uma mensagem legível a partir do dicionário de resultado.

    Exemplos simples para ações comuns (add_event, send_email, query_event).
    """
    action = result.get("action")
    success = result.get("success", False)

    if action == "add_event":
        if not success:
            return result.get("message") or result.get("error") or "Não foi possível criar o evento."

        data = result.get("data") or {}
        nome = data.get("nome") or data.get("event_name") or "evento"
        inicio = _fmt_datetime(data.get("data"))
        fim = _fmt_datetime(data.get("data_fim"))
        local = data.get("local")

        # Mensagem mais humana e séria
        if inicio and fim:
            msg = f"Agendei o evento '{nome}' de {inicio} até {fim}."
        elif inicio:
            msg = f"Agendei o evento '{nome}' para {inicio}."
        else:
            msg = f"O evento '{nome}' foi criado com sucesso." 

        if local:
            msg += f" Local: {local}."

        return msg

    if action == "send_email":
        if success:
            return result.get("message") or "Email enviado com sucesso."
        return result.get("message") or result.get("error") or "Falha ao enviar o email."

    if action == "query_event":
        eventos = result.get("result") or result.get("eventos") or []
        if not eventos:
            return "Não foram encontrados eventos para o período solicitado."
        # Mostrar resumo dos primeiros 3 com tom sério
        linhas = [f"Encontrei {len(eventos)} evento(s). Seguem os primeiros:"]
        for e in eventos[:3]:
            nome = e.get("nome") or e.get("event_name") or "evento"
            inicio = _fmt_datetime(e.get("data"))
            linhas.append(f"- {nome}: {inicio}")
        return "\n".join(linhas)

    # Fallback: se já houver uma mensagem textual, use-a
    if "message" in result:
        return result["message"]

    return "Pronto." 
