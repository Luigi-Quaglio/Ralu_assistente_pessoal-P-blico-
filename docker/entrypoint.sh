#!/bin/bash

# Inicializa o banco de dados SQLite
echo "Inicializando banco de dados..."
cd /app
PYTHONPATH=/app python3 -c "from src.database import init_database; init_database()"

# Inicia o servidor Ollama em background
ollama serve &
OLLAMA_PID=$!

# Aguarda o servidor iniciar
sleep 5

# Baixa o modelo base e cria o modelo Ralu (sÃ³ se nÃ£o existir)
if ! ollama list | grep -q "ralu"; then
    echo "Baixando modelo base llama3.2..."
    ollama pull llama3.2

    echo "Criando modelo Ralu..."
    ollama create ralu -f /app/Modelfile
    echo "Modelo Ralu criado com sucesso!"
else
    echo "Modelo Ralu jÃ¡ existe."
fi

echo "======================================"
echo "Banco de dados: /app/data/ralu.db"
echo "Ollama API: http://localhost:11434"
echo "Web UI: http://localhost:8001"
echo "======================================"

# Inicia o servidor web em background
echo "Iniciando servidor web..."
PYTHONPATH=/app python3 -m uvicorn src.web.app:app --host 0.0.0.0 --port 8001 &
WEB_PID=$!

# Aguarda qualquer processo terminar
wait -n $OLLAMA_PID $WEB_PID

# Se um processo morrer, mata o outro tambÃ©m
kill $OLLAMA_PID $WEB_PID 2>/dev/null
