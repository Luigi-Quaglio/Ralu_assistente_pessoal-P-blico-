"""
Dataset de teste para avaliação do classificador de intenções

Contém frases anotadas manualmente com a intenção esperada.
Usado para calcular precisão, recall e acurácia do classificador.
"""

from typing import List, Dict

# Dataset de teste: cada entrada tem "text" e "expected_intent"
TEST_DATASET: List[Dict[str, str]] = [
    # === ADD_EVENT ===
    {"text": "Adiciona um evento amanhã às 14 horas reunião com cliente", "expected_intent": "add_event"},
    {"text": "Me lembra de ligar pro dentista segunda feira às 9", "expected_intent": "add_event"},
    {"text": "Marca uma consulta dia 20 de maio às 15:30", "expected_intent": "add_event"},
    {"text": "Agendar reunião de equipe terça que vem as 10", "expected_intent": "add_event"},
    {"text": "Criar evento aniversário do João dia 15 de junho", "expected_intent": "add_event"},
    {"text": "Colocar no calendário almoço com a Maria sexta às 12", "expected_intent": "add_event"},
    {"text": "Adicione compromisso com advogado quinta 16 horas", "expected_intent": "add_event"},
    {"text": "Me avisa pra pagar a conta dia 25", "expected_intent": "add_event"},
    {"text": "Lembrete comprar presente semana que vem", "expected_intent": "add_event"},
    {"text": "Agendar consulta médico dia 30 às 14:30", "expected_intent": "add_event"},
    
    # === QUERY_EVENT ===
    {"text": "Que eventos eu tenho hoje?", "expected_intent": "query_event"},
    {"text": "O que tem marcado para amanhã?", "expected_intent": "query_event"},
    {"text": "Quais são meus compromissos da semana?", "expected_intent": "query_event"},
    {"text": "Tem alguma coisa agendada pra segunda?", "expected_intent": "query_event"},
    {"text": "Mostra minha agenda de hoje", "expected_intent": "query_event"},
    {"text": "O que eu tenho que fazer amanhã", "expected_intent": "query_event"},
    {"text": "Me fala os eventos de terça feira", "expected_intent": "query_event"},
    {"text": "Consultar agenda do dia 15", "expected_intent": "query_event"},
    {"text": "Quais eventos estão marcados essa semana", "expected_intent": "query_event"},
    {"text": "Tem algum compromisso hoje a tarde?", "expected_intent": "query_event"},
    
    # === SEND_EMAIL ===
    {"text": "Manda um email pro João dizendo que a reunião foi cancelada", "expected_intent": "send_email"},
    {"text": "Envia email para maria@exemplo.com com assunto urgente", "expected_intent": "send_email"},
    {"text": "Enviar mensagem por email para o cliente informando o atraso", "expected_intent": "send_email"},
    {"text": "Mande um email para pedro@empresa.com falando sobre o projeto", "expected_intent": "send_email"},
    {"text": "Escreve um email pro time de desenvolvimento", "expected_intent": "send_email"},
    {"text": "Preciso enviar email para fornecedor solicitando cotação", "expected_intent": "send_email"},
    {"text": "Dispara email para todos os participantes da reunião", "expected_intent": "send_email"},
    {"text": "Enviar e-mail para ana@email.com sobre o relatório", "expected_intent": "send_email"},
    {"text": "Manda email avisando que não vou poder ir", "expected_intent": "send_email"},
    {"text": "Envia uma mensagem por correio eletrônico pro chefe", "expected_intent": "send_email"},
    
    # === UNKNOWN (outros tipos de pedidos) ===
    {"text": "Como está o tempo hoje?", "expected_intent": "unknown"},
    {"text": "Conta uma piada", "expected_intent": "unknown"},
    {"text": "Qual é a capital da França?", "expected_intent": "unknown"},
    {"text": "Me diz quanto é 25 vezes 4", "expected_intent": "unknown"},
    {"text": "Toca uma música", "expected_intent": "unknown"},
    {"text": "Qual o significado da vida?", "expected_intent": "unknown"},
    {"text": "Quem ganhou o jogo ontem?", "expected_intent": "unknown"},
    {"text": "Como se faz um bolo de chocolate?", "expected_intent": "unknown"},
    {"text": "Me conta uma história", "expected_intent": "unknown"},
    {"text": "Abre o navegador", "expected_intent": "unknown"},
    
    # === CASOS LIMÍTROFES (testes mais difíceis) ===
    {"text": "Reunião amanhã", "expected_intent": "add_event"},
    {"text": "Hoje tem o que?", "expected_intent": "query_event"},
    {"text": "Email pro José", "expected_intent": "send_email"},
    {"text": "Me fala que dia é hoje", "expected_intent": "unknown"},
    {"text": "Adiciona lembrete ligar mãe", "expected_intent": "add_event"},
]


def get_dataset() -> List[Dict[str, str]]:
    """Retorna o dataset de teste"""
    return TEST_DATASET


def get_dataset_by_intent(intent: str) -> List[Dict[str, str]]:
    """Retorna apenas as frases de uma intenção específica"""
    return [item for item in TEST_DATASET if item["expected_intent"] == intent]


def get_intent_counts() -> Dict[str, int]:
    """Retorna contagem de exemplos por intenção"""
    counts = {}
    for item in TEST_DATASET:
        intent = item["expected_intent"]
        counts[intent] = counts.get(intent, 0) + 1
    return counts


if __name__ == "__main__":
    # Exibe estatísticas do dataset
    print("DATASET DE TESTE - Ralu")
    print("=" * 70)
    print(f"\nTotal de exemplos: {len(TEST_DATASET)}")
    print("\nDistribuição por intenção:")
    
    counts = get_intent_counts()
    for intent, count in sorted(counts.items()):
        print(f"  - {intent:15}: {count:2} exemplos")
    
    print("\n" + "=" * 70)
    print("\nExemplos:")
    for i, item in enumerate(TEST_DATASET[:5], 1):
        print(f"{i}. [{item['expected_intent']}] {item['text']}")
    print("...")
