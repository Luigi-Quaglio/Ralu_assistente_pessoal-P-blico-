"""
API Web do Ralu - Visualizador de Agenda
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime, timedelta
from pathlib import Path
import json

from src.database import init_database, EventoRepository, ContatoRepository, Evento, Contato
from src.ralu import Ralu
from src.handlers import AddEventHandler, EmailHandler

# Inicializa
init_database()
app = FastAPI(title="Ralu - Agenda Inteligente")

# Templates
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

# Repositórios
eventos_repo = EventoRepository()
contatos_repo = ContatoRepository()

# Estado de sessão para follow-ups (em memória - para produção usar Redis/DB)
pending_events = {}  # session_id -> pending_event


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Página inicial - Calendário"""
    hoje = datetime.now()
    eventos_semana = eventos_repo.buscar_proximos(7)
    eventos_hoje = eventos_repo.buscar_hoje()
    
    return templates.TemplateResponse(request, "index.html", {
        "hoje": hoje,
        "eventos_semana": eventos_semana,
        "eventos_hoje": eventos_hoje
    })


@app.get("/agenda", response_class=HTMLResponse)
async def agenda(request: Request, dias: int = 7):
    """Visualização de agenda"""
    hoje = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Gera lista de dias
    dias_lista = []
    for i in range(dias):
        data = hoje + timedelta(days=i)
        eventos_dia = eventos_repo.buscar_por_data(data)
        dias_lista.append({
            "data": data,
            "eventos": eventos_dia,
            "is_hoje": i == 0
        })
    
    return templates.TemplateResponse(request, "agenda.html", {
        "dias": dias_lista,
        "hoje": hoje
    })


@app.get("/calendario", response_class=HTMLResponse)
async def calendario(request: Request, mes: int = None, ano: int = None):
    """Visualização mensal"""
    hoje = datetime.now()
    mes = mes or hoje.month
    ano = ano or hoje.year
    
    # Primeiro e último dia do mês
    primeiro_dia = datetime(ano, mes, 1)
    if mes == 12:
        ultimo_dia = datetime(ano + 1, 1, 1) - timedelta(days=1)
    else:
        ultimo_dia = datetime(ano, mes + 1, 1) - timedelta(days=1)
    
    # Eventos do mês
    eventos_mes = eventos_repo.buscar_por_periodo(primeiro_dia, ultimo_dia)
    
    # Agrupa por dia (expandindo eventos de múltiplos dias)
    eventos_por_dia = {}
    for e in eventos_mes:
        if e.data:
            data_inicio = e.data.date()
            data_fim = e.data_fim.date() if e.data_fim else data_inicio
            
            # Itera por todos os dias do evento
            dia_atual = data_inicio
            while dia_atual <= data_fim:
                # Só adiciona se o dia está no mês atual
                if dia_atual.month == mes and dia_atual.year == ano:
                    dia_num = dia_atual.day
                    if dia_num not in eventos_por_dia:
                        eventos_por_dia[dia_num] = []
                    
                    # Cria um objeto wrapper com info de posição no evento
                    evento_info = {
                        "evento": e,
                        "is_inicio": dia_atual == data_inicio,
                        "is_fim": dia_atual == data_fim,
                        "is_multi_dia": data_fim != data_inicio,
                        "duracao_dias": (data_fim - data_inicio).days + 1
                    }
                    eventos_por_dia[dia_num].append(evento_info)
                
                dia_atual += timedelta(days=1)
    
    # Meses para navegação
    mes_anterior = (mes - 2) % 12 + 1
    ano_anterior = ano if mes > 1 else ano - 1
    mes_proximo = mes % 12 + 1
    ano_proximo = ano if mes < 12 else ano + 1
    
    nomes_meses = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                   "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    
    return templates.TemplateResponse(request, "calendario.html", {
        "mes": mes,
        "ano": ano,
        "nome_mes": nomes_meses[mes],
        "primeiro_dia": primeiro_dia,
        "ultimo_dia": ultimo_dia,
        "eventos_por_dia": eventos_por_dia,
        "hoje": hoje,
        "mes_anterior": mes_anterior,
        "ano_anterior": ano_anterior,
        "mes_proximo": mes_proximo,
        "ano_proximo": ano_proximo
    })


@app.get("/contatos", response_class=HTMLResponse)
async def contatos(request: Request):
    """Lista de contatos"""
    lista = contatos_repo.listar_todos()
    return templates.TemplateResponse(request, "contatos.html", {
        "contatos": lista
    })


# === API REST ===

@app.get("/api/eventos")
async def api_eventos(dias: int = 7):
    """Lista eventos dos próximos N dias"""
    eventos = eventos_repo.buscar_proximos(dias)
    return {"eventos": [e.to_dict() for e in eventos]}


@app.get("/api/eventos/{evento_id}")
async def api_evento(evento_id: int):
    """Busca evento por ID"""
    evento = eventos_repo.buscar_por_id(evento_id)
    if not evento:
        raise HTTPException(status_code=404, detail="Evento não encontrado")
    return evento.to_dict()


@app.post("/api/eventos")
async def api_criar_evento(request: Request):
    """Cria novo evento"""
    data = await request.json()
    
    evento = Evento(
        nome=data.get("nome"),
        data=datetime.fromisoformat(data["data"]) if data.get("data") else None,
        descricao=data.get("descricao"),
        participante=data.get("participante"),
        lembrete=datetime.fromisoformat(data["lembrete"]) if data.get("lembrete") else None,
        local=data.get("local")
    )
    
    evento = eventos_repo.criar(evento)
    return {"success": True, "evento": evento.to_dict()}


@app.delete("/api/eventos/{evento_id}")
async def api_deletar_evento(evento_id: int):
    """Remove evento"""
    if eventos_repo.deletar(evento_id):
        return {"success": True}
    raise HTTPException(status_code=404, detail="Evento não encontrado")


@app.put("/api/eventos/{evento_id}")
async def api_atualizar_evento(evento_id: int, request: Request):
    """Atualiza evento existente"""
    data = await request.json()
    
    evento = eventos_repo.buscar_por_id(evento_id)
    if not evento:
        raise HTTPException(status_code=404, detail="Evento não encontrado")
    
    # Atualiza campos
    evento.nome = data.get("nome", evento.nome)
    if data.get("data"):
        evento.data = datetime.fromisoformat(data["data"])
    if "data_fim" in data:
        evento.data_fim = datetime.fromisoformat(data["data_fim"]) if data["data_fim"] else None
    evento.descricao = data.get("descricao", evento.descricao)
    evento.participante = data.get("participante", evento.participante)
    evento.local = data.get("local", evento.local)
    if "cor" in data:
        evento.cor = data["cor"] if data["cor"] else None
    if data.get("lembrete"):
        evento.lembrete = datetime.fromisoformat(data["lembrete"])
    
    if eventos_repo.atualizar(evento):
        return {"success": True, "evento": evento.to_dict()}
    raise HTTPException(status_code=500, detail="Erro ao atualizar evento")


@app.get("/api/contatos")
async def api_contatos():
    """Lista todos os contatos"""
    contatos = contatos_repo.listar_todos()
    return {"contatos": [c.to_dict() for c in contatos]}


@app.post("/api/contatos")
async def api_criar_contato(request: Request):
    """Cria novo contato"""
    data = await request.json()
    
    contato = Contato(
        nome=data.get("nome"),
        email=data.get("email"),
        telefone=data.get("telefone")
    )
    
    contato = contatos_repo.criar(contato)
    return {"success": True, "contato": contato.to_dict()}


@app.post("/api/chat")
async def api_chat(request: Request):
    """Processa mensagem via Ralu (classificação + ação)

    Aceita JSON em UTF-8 (padrão) e tenta decodificar automaticamente
    payloads em UTF-16/UTF-16-LE/UTF-16-BE/latin-1 quando necessário.
    """
    try:
        data = await request.json()
    except Exception:
        # Fallback: tentar decodificar o corpo com outras encodings
        body = await request.body()
        import json as _json
        data = None
        for _enc in ("utf-8", "utf-16", "utf-16-le", "utf-16-be", "latin-1"):
            try:
                decoded = body.decode(_enc)
                data = _json.loads(decoded)
                break
            except Exception:
                data = None

        if data is None:
            raise HTTPException(status_code=400, detail="Corpo JSON com encoding inválido ou formato inválido")

    texto = data.get("texto", "")
    session_id = data.get("session_id", "default")
    
    if not texto:
        raise HTTPException(status_code=400, detail="Texto não fornecido")
    
    try:
        # Verifica se há follow-up pendente
        if session_id in pending_events:
            pending = pending_events[session_id]
            followup_type = pending.get("followup_type")
            
            # Follow-up de seleção de contato para email
            if followup_type == "select_contact":
                # Usuário respondeu com nome do contato
                handler = EmailHandler()
                action_result = handler.execute_with_contact(
                    texto.strip(),
                    pending.get("pending_email", {})
                )
                
                # Remove pendência
                del pending_events[session_id]
                
                return {
                    "classification": {"intent": "send_email", "confidence": 1.0, "entities": {}},
                    "result": action_result
                }
            
            # Follow-up de data/hora para evento
            elif followup_type == "datetime":
                # Usa Ollama para extrair data/hora da resposta
                ralu = Ralu()
                result = ralu.classify(f"Agende para {texto}")
                
                data_texto = result.entities.get("date")
                hora_texto = result.entities.get("time")
                
                if data_texto or hora_texto:
                    handler = AddEventHandler()
                    action_result = handler.execute_with_datetime(
                        pending["pending_event"],
                        data_texto,
                        hora_texto
                    )
                    
                    del pending_events[session_id]
                    
                    return {
                        "classification": result.to_dict(),
                        "result": action_result
                    }
                else:
                    return {
                        "classification": {"intent": "followup", "confidence": 1.0},
                        "result": {
                            "success": False,
                            "needs_followup": True,
                            "followup_type": "datetime",
                            "message": "Não entendi. Qual a data e horário? (ex: amanhã às 10h)"
                        }
                    }
        
        # Processa normalmente
        ralu = Ralu()
        resultado = ralu.process(texto)
        
        # Se precisa de follow-up, guarda estado
        if resultado.get("result", {}).get("needs_followup"):
            pending_events[session_id] = resultado["result"]
        
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
