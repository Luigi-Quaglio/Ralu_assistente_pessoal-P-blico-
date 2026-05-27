#!/usr/bin/env python3
"""
Script de Teste - Enviar Áudio para ESP32

Este script envia áudio de teste via MQTT para a ESP32 reproduzir
no alto-falante MAX98357.
"""

import paho.mqtt.client as mqtt
import struct
import time
import math

# Configurações
MQTT_BROKER = "192.168.1.13"
MQTT_PORT = 1883
TOPIC_AUDIO = "ralu/audio/stream"
TOPIC_STATUS = "ralu/audio/status"

# Parâmetros de áudio
SAMPLE_RATE = 16000
DURATION = 3  # segundos

def generate_tone(frequency=440, duration=1.0, sample_rate=16000, amplitude=2000):
    """Gera um tom senoidal (beep)"""
    samples = int(sample_rate * duration)
    audio_data = bytearray()
    
    for i in range(samples):
        # Gerar onda senoidal
        t = i / sample_rate
        sample = int(amplitude * math.sin(2 * math.pi * frequency * t))
        
        # Converter para 16-bit PCM (little-endian)
        audio_data.extend(struct.pack('<h', sample))
    
    return bytes(audio_data)

def on_connect(client, userdata, flags, rc, properties=None):
    """Callback quando conecta ao MQTT"""
    if rc == 0:
        print(f"[OK] Conectado ao MQTT broker!")
        client.subscribe(TOPIC_STATUS)
    else:
        print(f"[ERRO] Falha na conexão. Código: {rc}")

def on_message(client, userdata, msg):
    """Callback quando recebe mensagem"""
    print(f"[STATUS ESP32] {msg.payload.decode('utf-8', errors='ignore')}")

def main():
    print("\n" + "="*50)
    print("  TESTE DE ÁUDIO - ESP32")
    print("="*50)
    print(f"\nBroker: {MQTT_BROKER}:{MQTT_PORT}")
    print(f"Tópico: {TOPIC_AUDIO}")
    
    # Conectar ao MQTT
    print("\n[1/4] Conectando ao MQTT...")
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        time.sleep(2)
    except Exception as e:
        print(f"[ERRO] Não foi possível conectar ao MQTT: {e}")
        return
    
    # Gerar tons de teste
    print("\n[2/4] Gerando tons de teste...")
    tones = [
        (440, 1.0, "Lá (440 Hz)"),    # Nota Lá
        (523, 1.0, "Dó (523 Hz)"),    # Nota Dó
        (659, 1.0, "Mi (659 Hz)"),    # Nota Mi
    ]
    
    # Enviar cada tom
    print("\n[3/4] Enviando áudio para ESP32...")
    print("      Você deve ouvir 3 tons diferentes!\n")
    
    for freq, dur, name in tones:
        print(f"  → Gerando {name}...")
        audio = generate_tone(freq, dur, SAMPLE_RATE, amplitude=50)  # Volume ultra baixo
        
        print(f"  → Enviando {len(audio)} bytes...")
        
        # Enviar em chunks de 512 bytes
        chunk_size = 512
        for i in range(0, len(audio), chunk_size):
            chunk = audio[i:i+chunk_size]
            client.publish(TOPIC_AUDIO, chunk)
            time.sleep(0.03)  # Delay maior para estabilidade
        
        print(f"  ✓ {name} enviado!")
        time.sleep(0.5)  # Pausa entre tons
    
    print("\n[4/4] Teste concluído!")
    print("\nSe você ouviu 3 tons (Lá, Dó, Mi), o sistema está funcionando! 🎵")
    
    # Manter conexão para ver status
    print("\nAguardando mensagens de status da ESP32...")
    print("Pressione Ctrl+C para sair\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n[INFO] Encerrando...")
    
    client.loop_stop()
    client.disconnect()

if __name__ == "__main__":
    main()
