"""
Script para inicializar e testar o banco de dados
"""
from datetime import datetime, timedelta

from src.database import (
    init_database,
    ContatoRepository,
    EventoRepository,
    Contato,
    Evento
)


def main():
    # Inicializa o banco
    print("=" * 60)
    print("Inicializando banco de dados...")
    init_database()
    
    # Repositórios
    contatos = ContatoRepository()
    eventos = EventoRepository()
    
    # Dados de exemplo
    print("\n" + "=" * 60)
    print("Inserindo dados de exemplo...")
    
    # Contatos
    contatos_exemplo = [
        Contato(nome="João Silva", email="joao@email.com", telefone="11999999999"),
        Contato(nome="Maria Santos", email="maria@email.com", telefone="11988888888"),
        Contato(nome="Pedro Costa", email="pedro@email.com", telefone="11977777777"),
    ]
    
    for contato in contatos_exemplo:
        if not contatos.existe(contato.nome):
            contatos.criar(contato)
            print(f"  Contato criado: {contato.nome}")
        else:
            print(f"  Contato já existe: {contato.nome}")
    
    # Eventos
    agora = datetime.now()
    eventos_exemplo = [
        Evento(
            nome="Reunião de projeto",
            data=agora + timedelta(hours=2),
            descricao="Discussão sobre o roadmap",
            participante="João Silva",
            lembrete=agora + timedelta(hours=1),
            local="Sala de reuniões"
        ),
        Evento(
            nome="Almoço com cliente",
            data=agora + timedelta(days=1, hours=4),
            descricao="Apresentação de proposta",
            participante="Maria Santos",
            local="Restaurante Central"
        ),
        Evento(
            nome="Call semanal",
            data=agora + timedelta(days=7),
            descricao="Sync semanal da equipe",
            participante="Pedro Costa",
            lembrete=agora + timedelta(days=6, hours=23),
            local="Google Meet"
        ),
    ]
    
    for evento in eventos_exemplo:
        eventos.criar(evento)
        print(f"  Evento criado: {evento.nome} (ID: {evento.id})")
    
    # Listar dados
    print("\n" + "=" * 60)
    print("CONTATOS:")
    for c in contatos.listar_todos():
        print(f"  - {c.nome} | {c.email} | {c.telefone}")
    
    print("\n" + "=" * 60)
    print("EVENTOS:")
    for e in eventos.listar_todos():
        data_str = e.data.strftime("%d/%m/%Y %H:%M") if e.data else "N/A"
        print(f"  - [{e.id}] {e.nome} | {data_str} | {e.local}")
    
    print("\n" + "=" * 60)
    print("Próximos 7 dias:")
    for e in eventos.buscar_proximos(7):
        data_str = e.data.strftime("%d/%m/%Y %H:%M") if e.data else "N/A"
        print(f"  - {e.nome} | {data_str}")
    
    print("\n" + "=" * 60)
    print("Banco de dados configurado com sucesso!")


if __name__ == "__main__":
    main()
