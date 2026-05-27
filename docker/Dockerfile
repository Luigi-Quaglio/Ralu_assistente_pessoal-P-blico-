FROM ollama/ollama:latest

# Instalar Python para inicializar o banco
RUN apt-get update && apt-get install -y python3 python3-pip && \
    rm -rf /var/lib/apt/lists/*

# Copiar código fonte
COPY src /app/src
COPY requirements.txt /app/requirements.txt

# Instalar dependências Python
RUN pip3 install --break-system-packages -r /app/requirements.txt

# Copiar o Modelfile
COPY ollama/Modelfile /app/Modelfile

# Script de inicialização
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Criar diretório de dados
RUN mkdir -p /app/data

WORKDIR /app

EXPOSE 11434
EXPOSE 8001

ENTRYPOINT ["/entrypoint.sh"]
