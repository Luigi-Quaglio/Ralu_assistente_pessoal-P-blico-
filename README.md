# Ralu — Assistente de Voz com NLU 100% Local

> Trabalho de Conclusão de Curso · Python · Ollama · Llama 3.2 · FastAPI · SQLite · ESP32

**Ralu** é um assistente pessoal inteligente que interpreta comandos em linguagem natural (português brasileiro) e executa ações como criar eventos na agenda, consultar compromissos e enviar e-mails — tudo rodando **100% local**, sem dependência de APIs externas de IA.

---

## Sumário

1. [Sobre o Projeto](#sobre-o-projeto)
2. [Arquitetura](#arquitetura)
3. [Funcionalidades](#funcionalidades)
4. [Tecnologias](#tecnologias)
5. [Pré-requisitos](#pré-requisitos)
6. [Instalação](#instalação)
7. [Como Executar](#como-executar)
8. [Benchmarks e Resultados](#benchmarks-e-resultados)
9. [Integração ESP32](#integração-esp32)
10. [Docker](#docker)
11. [Estrutura do Projeto](#estrutura-do-projeto)
12. [Licença](#licença)

---

## Sobre o Projeto

O projeto nasceu da necessidade de avaliar a viabilidade de um assistente de voz executado localmente em hardware de consumo, comparando desempenho, latência e consumo de memória frente a soluções baseadas em nuvem.

O pipeline completo envolve:

- Captura de áudio (ESP32 via MQTT) ou entrada de texto
- Classificação de intenção via LLM local (Ollama + Llama 3.2 customizado)
- Execução do handler adequado (agenda, e-mail, consulta)
- Síntese de voz (TTS) em português usando voz nativa do Windows (SAPI)
- Interface web para visualização da agenda

---

## Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                        USUÁRIO                              │
│              Texto via CLI / Web / ESP32 (MQTT)             │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                     Ralu  (src/ralu.py)                     │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐    │
│  │ OllamaClient│─▶│IntentClassif.│─▶│    Handlers     │    │
│  │  (llama3.2) │  │   (ralu:mod) │  │ add/query/email │    │
│  └─────────────┘  └──────────────┘  └────────┬────────┘    │
└───────────────────────────────────────────────┼────────────┘
                          │                     │
              ┌───────────┼─────────────┐       │
              ▼           ▼             ▼       ▼
        ┌──────────┐ ┌─────────┐ ┌──────────┐ ┌───────────┐
        │  SQLite  │ │ FastAPI │ │ TTS Piper│ │  Outbox   │
        │ Database │ │  Web UI │ │ (SAPI)   │ │  Watcher  │
        └──────────┘ └─────────┘ └──────────┘ └───────────┘
```

### Modelo LLM Customizado

O modelo `ralu` é derivado do Llama 3.2 com um system prompt especializado que força saída JSON puro com campos `intent`, `confidence` e `entities`. Definido em `ollama/Modelfile`.

---

## Funcionalidades

| Intenção      | Exemplo de entrada                                | Ação executada                  |
|---------------|---------------------------------------------------|---------------------------------|
| `add_event`   | "Agenda reunião com Maria sexta às 14h"           | Cria evento no SQLite           |
| `query_event` | "O que tenho para amanhã?"                        | Consulta e lista eventos        |
| `send_email`  | "Manda um e-mail pro João sobre a reunião"        | Prepara e envia e-mail          |
| `unknown`     | "Qual a capital da França?"                       | Resposta padrão de fallback     |

**Interface Web** (FastAPI + Jinja2):
- `/` — Dashboard principal
- `/agenda` — Visualização de eventos
- `/calendario` — Calendário mensal
- `/contatos` — Gerenciamento de contatos

**TTS Interativo**:
- `falar.py` — modo interativo: você digita, a Ralu fala usando a voz **Microsoft Maria (PT-BR)**

---

## Tecnologias

| Tecnologia         | Versão          | Finalidade                          |
|--------------------|-----------------|-------------------------------------|
| Python             | 3.11+           | Linguagem principal                 |
| Ollama             | 0.24+           | Servidor de LLM local               |
| Llama 3.2          | —               | Modelo de linguagem base            |
| FastAPI            | 0.100+          | Framework web / API REST            |
| Uvicorn            | 0.22+           | Servidor ASGI                       |
| SQLite             | 3               | Persistência de dados               |
| Jinja2             | 3.1+            | Renderização de templates HTML      |
| pyttsx3            | 2.90+           | TTS via Windows SAPI (voz Maria PT-BR) |
| Docker / Compose   | latest          | Containerização (opcional)          |
| ESP32 / PlatformIO | —               | Captura de áudio por hardware       |
| MQTT               | —               | Comunicação ESP32 ↔ servidor        |

---

## Pré-requisitos

- **Python 3.11+** — [python.org](https://www.python.org/)
- **Ollama** — [ollama.com](https://ollama.com/) (Windows/macOS/Linux)
- **Git** — [git-scm.com](https://git-scm.com/)
- *(Opcional)* Docker Desktop para execução containerizada

---

## Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/<seu-usuario>/ralu.git
cd ralu
```

### 2. Crie e ative um ambiente virtual

```bash
# Windows
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux / macOS
python -m venv .venv
source .venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
pip install pyttsx3   # TTS nativo do sistema
```

### 4. Instale e configure o Ollama

```bash
# Baixe em https://ollama.com e instale
# Em seguida, crie o modelo customizado Ralu:
ollama create ralu -f ollama/Modelfile
```

Verifique se está rodando:

```bash
ollama list   # deve mostrar ralu:latest e llama3.2:latest
```

### 5. Inicialize o banco de dados

```bash
python -c "from src.database.init_db import init_db; init_db()"
```

---

## Como Executar

> Em todos os comandos abaixo, defina o `PYTHONPATH` para a raiz do projeto.

```powershell
# Windows PowerShell
$env:PYTHONPATH = $PWD
```

```bash
# Linux / macOS
export PYTHONPATH=$(pwd)
```

### Modo CLI interativo

```bash
python src/main.py
```

### Servidor Web (agenda + contatos)

```bash
uvicorn src.web.app:app --host 0.0.0.0 --port 8001 --reload
# Acesse: http://localhost:8001
```

### TTS interativo (digita → Ralu fala)

```bash
python falar.py
```

### Watcher de TTS (monitora pasta outbox)

```bash
python tts_watcher.py --dir tts_outbox
```

---

## Benchmarks e Resultados

Os scripts de avaliação estão em `tests/`. Os resultados gerados ficam em `data/benchmarks/`.

### Executar benchmarks

```bash
# Classificador (acurácia, precisão, recall, F1)
python tests/benchmark_classifier.py

# Latência do pipeline
python tests/benchmark_latency.py

# Consumo de memória
python tests/benchmark_memory.py

# Todos de uma vez
python tests/run_all_benchmarks.py
```

### Resultados obtidos (19/05/2026)

#### Latência do Pipeline

| Etapa         | Média (s) | Desvio Padrão (s) | Mín (s) | Máx (s) |
|---------------|-----------|-------------------|---------|---------|
| Classificação | 11.230    | 23.574            | 2.676   | 85.893  |
| Handler       | 0.009     | 0.010             | 0.000   | 0.032   |
| TTS           | 0.000     | 0.000             | 0.000   | 0.000   |
| **Total**     | **11.239**| 23.578            | 2.676   | 85.914  |

> A latência dominante é o LLM local (~11 s em média). O primeiro uso é mais lento pois o modelo precisa ser carregado na memória.

#### Desempenho do Classificador — Acurácia Geral: **82,22%**

| Intenção      | Precisão | Recall   | F1-Score | Suporte |
|---------------|----------|----------|----------|---------|
| `add_event`   | 91,67 %  | 91,67 %  | 91,67 %  | 12      |
| `query_event` | 73,33 %  | 100,00 % | 84,62 %  | 11      |
| `send_email`  | 78,57 %  | 100,00 % | 88,00 %  | 11      |
| `unknown`     | 100,00 % | 36,36 %  | 53,33 %  | 11      |

#### Matriz de Confusão

| Verdadeiro \ Previsto | add_event | query_event | send_email | unknown |
|----------------------:|----------:|------------:|-----------:|--------:|
| add_event             | **11**    | 1           | 0          | 0       |
| query_event           | 0         | **11**      | 0          | 0       |
| send_email            | 0         | 0           | **11**     | 0       |
| unknown               | 1         | 3           | 3          | **4**   |

> A classe `unknown` apresentou o maior desafio (F1 = 53 %), pois o modelo tende a classificar entradas ambíguas como uma intenção conhecida. As demais classes alcançaram F1 acima de 84 %.

#### Consumo de Memória

| Processo | RAM Média (MB) |
|----------|----------------|
| Python   | 43,3 MB        |
| Ralu (Docker + modelo carregado) | ~3 075 MB |

> O consumo elevado no Docker reflete o modelo Llama 3.2 (2 GB) carregado na RAM. Em execução nativa, o modelo é mantido pelo processo Ollama separadamente.

---

## Integração ESP32

O diretório `esp32_audio/` contém o firmware e os scripts Python para captura de áudio via microfone e envio por MQTT ao servidor Ralu.

```
esp32_audio/
├── esp32_audio.ino      # Sketch Arduino/PlatformIO
├── platformio.ini       # Configuração de build
├── config.h             # SSID, broker MQTT, tópicos
├── mqtt_audio_sender.py # Recebe áudio do ESP32 via MQTT
├── mqtt_monitor.py      # Monitor de tópicos MQTT
├── test_audio.py        # Testa captura de áudio
└── test_mic.py          # Testa o microfone
```

**Fluxo de hardware**:

```
Microfone → ESP32 → Wi-Fi → Broker MQTT → mqtt_audio_sender.py → Ralu
```

Consulte `esp32_audio/README.md` para instruções detalhadas de upload do firmware.

---

## Docker

Para executar o sistema completo em contêineres:

```bash
cd docker
docker-compose up --build
```

Serviços iniciados:
- **ralu** — aplicação Python na porta `8001`
- **ollama** — servidor LLM na porta `11434`

Volumes persistentes: `ollama_data` (modelos), `../data` (banco), `../tts_outbox` (fila TTS).

---

## Estrutura do Projeto

```
ralu/
├── src/                          # Código-fonte principal
│   ├── main.py                   # Ponto de entrada CLI
│   ├── ralu.py                   # Orquestrador principal
│   ├── classifier/               # IntentClassifier
│   ├── client/                   # OllamaClient (HTTP)
│   ├── config/                   # Configurações e variáveis de ambiente
│   ├── database/                 # Modelos, repositórios e init do SQLite
│   ├── handlers/                 # Handlers por intenção
│   ├── models/                   # Tipos e dataclasses
│   ├── utils/                    # date_parser, tts, response_formatter
│   └── web/                      # FastAPI app + templates HTML
│       └── templates/            # agenda, calendario, contatos, index
├── tests/                        # Benchmarks e testes unitários
│   ├── benchmark_classifier.py   # Avalia classificador (45 exemplos)
│   ├── benchmark_latency.py      # Mede latência do pipeline
│   ├── benchmark_memory.py       # Mede consumo de RAM
│   ├── run_all_benchmarks.py     # Executa todos os benchmarks
│   └── test_dataset.py           # Dataset anotado para avaliação
├── data/
│   └── benchmarks/               # Resultados em CSV/JSON gerados pelos benchmarks
├── ollama/
│   └── Modelfile                 # Definição do modelo ralu (FROM llama3.2 + system prompt)
├── esp32_audio/                  # Firmware e scripts de integração ESP32
├── docker/                       # Dockerfile + docker-compose.yml
├── docs/                         # Documentação adicional
├── tts_piper.py                  # Módulo TTS (Microsoft Maria PT-BR via pyttsx3)
├── tts_watcher.py                # Monitora tts_outbox/ e reproduz mensagens
├── falar.py                      # CLI interativo: digita → Ralu fala
├── requirements.txt              # Dependências Python
└── .gitignore
```

---

## Variáveis de Ambiente

| Variável          | Padrão                    | Descrição                              |
|-------------------|---------------------------|----------------------------------------|
| `OLLAMA_HOST`     | `http://localhost:11434`  | URL do servidor Ollama                 |
| `OLLAMA_MODEL`    | `ralu`                    | Nome do modelo a usar                  |
| `RALU_TTS`        | `true`                    | Habilita TTS por áudio (`false` = só outbox) |
| `RALU_TTS_OUTBOX` | `tts_outbox`              | Pasta da fila de mensagens TTS         |
| `REQUEST_TIMEOUT` | `120`                     | Timeout em segundos para o LLM         |
| `DATABASE_PATH`   | `data/ralu.db`            | Caminho do banco SQLite                |

---

## Licença

Este projeto está licenciado sob a [MIT License](LICENSE).

---

*Desenvolvido como Trabalho de Conclusão de Curso — 2026*
