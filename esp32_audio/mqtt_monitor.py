"""
Monitor MQTT - Testa recebimento de mensagens da ESP32

Mostra todas as mensagens recebidas dos tópicos da ESP32
"""
import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime
import struct

# Configurações
MQTT_BROKER = "localhost"
MQTT_PORT = 1883

# Tópicos para monitorar
TOPICS = [
    ("ralu/test", 0),      # Mensagens de teste
    ("ralu/mic/audio", 0), # Áudio do microfone
    ("ralu/status", 0),    # Status da ESP32
]

# Contador de mensagens
msg_count = {
    "ralu/test": 0,
    "ralu/mic/audio": 0,
    "ralu/status": 0
}

def on_connect(client, userdata, flags, rc):
    """Callback quando conecta ao broker"""
    if rc == 0:
        print("=" * 60)
        print("  MONITOR MQTT - Ralu ESP32 Test")
        print("=" * 60)
        print(f"✓ Conectado ao broker: {MQTT_BROKER}:{MQTT_PORT}")
        print(f"⏰ Início: {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 60)
        print("\nInscrevendo em tópicos:")
        
        for topic, qos in TOPICS:
            client.subscribe(topic, qos)
            print(f"  📡 {topic}")
        
        print("\n" + "=" * 60)
        print("Aguardando mensagens da ESP32...")
        print("=" * 60 + "\n")
    else:
        print(f"✗ Falha na conexão. Código: {rc}")

def on_message(client, userdata, msg):
    """Callback quando recebe mensagem"""
    topic = msg.topic
    msg_count[topic] = msg_count.get(topic, 0) + 1
    
    timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
    
    print(f"\n┌─ [{timestamp}] Tópico: {topic}")
    print(f"│  Mensagem #{msg_count[topic]}")
    
    # Trata mensagem de teste (JSON)
    if topic == "ralu/test":
        try:
            data = json.loads(msg.payload.decode())
            print(f"│  📊 TEST: {data.get('test')}")
            print(f"│  🔢 Counter: {data.get('counter')}")
            print(f"│  ⏱️  Uptime: {data.get('uptime')}s")
            print(f"│  📶 RSSI: {data.get('rssi')} dBm")
        except:
            print(f"│  Payload: {msg.payload.decode()}")
    
    # Trata status (JSON)
    elif topic == "ralu/status":
        try:
            data = json.loads(msg.payload.decode())
            print(f"│  Status: {data.get('status')}")
            print(f"│  IP: {data.get('ip')}")
        except:
            print(f"│  Payload: {msg.payload.decode()}")
    
    # Trata áudio (binário)
    elif topic == "ralu/mic/audio":
        size = len(msg.payload)
        print(f"│  🎤 Áudio capturado")
        print(f"│  📦 Tamanho: {size} bytes ({size/1024:.2f} KB)")
        
        # Calcula nível de áudio
        if size >= 2:
            try:
                samples = struct.unpack(f'{size//2}h', msg.payload)
                avg_level = sum(abs(s) for s in samples) / len(samples)
                max_level = max(abs(s) for s in samples)
                
                print(f"│  📊 Nível médio: {int(avg_level)}")
                print(f"│  📊 Nível máximo: {max_level}")
                
                # Barra visual de nível
                bar_len = int(avg_level / 1000)
                bar = "█" * min(bar_len, 40)
                print(f"│  🔊 {bar}")
            except:
                print(f"│  ⚠️  Erro ao processar samples")
    
    print("└" + "─" * 58)

def on_disconnect(client, userdata, rc):
    """Callback quando desconecta"""
    print(f"\n⚠️  Desconectado do broker (rc={rc})")
    if rc != 0:
        print("Tentando reconectar...")

def main():
    # Cria cliente
    client = mqtt.Client()
    
    # Define callbacks
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    
    try:
        # Conecta ao broker
        print(f"Conectando ao broker MQTT em {MQTT_BROKER}:{MQTT_PORT}...")
        client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
        
        # Loop infinito processando mensagens
        client.loop_forever()
        
    except KeyboardInterrupt:
        print("\n\n" + "=" * 60)
        print("ESTATÍSTICAS FINAIS")
        print("=" * 60)
        for topic, count in msg_count.items():
            print(f"  {topic}: {count} mensagens")
        print("=" * 60)
        print("\n👋 Encerrando monitor...")
        
    except Exception as e:
        print(f"\n✗ Erro: {e}")
        print("Verifique se o broker Mosquitto está rodando:")
        print("  Get-Service mosquitto")
    
    finally:
        client.disconnect()

if __name__ == "__main__":
    main()
