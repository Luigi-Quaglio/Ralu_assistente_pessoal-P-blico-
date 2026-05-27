#!/usr/bin/env python3
"""
Script de Teste - Capturar Áudio do Microfone ESP32

Este script recebe áudio do microfone ESP32 via MQTT
e visualiza os níveis de áudio em tempo real.
"""

import paho.mqtt.client as mqtt
import struct
import time
import wave
from collections import deque

# Configurações
MQTT_BROKER = "192.168.1.13"
MQTT_PORT = 1883
TOPIC_MIC = "ralu/mic/audio"
TOPIC_CONTROL = "ralu/audio/control"

# Parâmetros de áudio
SAMPLE_RATE = 16000
CHANNELS = 1
SAMPLE_WIDTH = 2  # 16-bit = 2 bytes

# Controle de gravação
recording = False
audio_data = bytearray()
max_samples = deque(maxlen=50)  # Últimos 50 chunks para visualização

def calculate_level(data):
    """Calcula nível de áudio (RMS)"""
    if len(data) < 2:
        return 0
    
    # Converte bytes para samples 16-bit
    samples = struct.unpack(f'<{len(data)//2}h', data)
    
    # Calcula RMS
    sum_squares = sum(s*s for s in samples)
    rms = (sum_squares / len(samples)) ** 0.5
    
    return int(rms)

def draw_level_bar(level, max_level=5000):
    """Desenha barra de nível de áudio"""
    bar_width = 50
    filled = int((level / max_level) * bar_width)
    filled = min(filled, bar_width)
    
    bar = "█" * filled + "░" * (bar_width - filled)
    
    # Cor baseada no nível
    if level < 500:
        color = "⚪"  # Muito baixo
    elif level < 1000:
        color = "🟢"  # Baixo
    elif level < 2000:
        color = "🟡"  # Médio
    elif level < 3000:
        color = "🟠"  # Alto
    else:
        color = "🔴"  # Muito alto
    
    return f"{color} [{bar}] {level:5d}"

def on_connect(client, userdata, flags, rc, properties=None):
    """Callback quando conecta ao MQTT"""
    if rc == 0:
        print("[OK] Conectado ao MQTT broker!")
        client.subscribe(TOPIC_MIC)
        print(f"[OK] Inscrito no tópico: {TOPIC_MIC}")
        print()
    else:
        print(f"[ERRO] Falha na conexão. Código: {rc}")

def on_message(client, userdata, msg):
    """Callback quando recebe mensagem"""
    global recording, audio_data
    
    if msg.topic == TOPIC_MIC:
        # Calcula nível de áudio
        level = calculate_level(msg.payload)
        max_samples.append(level)
        
        # Mostra barra de nível
        avg_level = sum(max_samples) / len(max_samples) if max_samples else 0
        print(f"\r{draw_level_bar(int(avg_level))}", end="", flush=True)
        
        # Se estiver gravando, adiciona ao buffer
        if recording:
            audio_data.extend(msg.payload)

def save_audio(filename="gravacao_mic.wav"):
    """Salva áudio gravado em arquivo WAV"""
    if len(audio_data) == 0:
        print("\n[AVISO] Nenhum dado para salvar")
        return
    
    try:
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(SAMPLE_WIDTH)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(bytes(audio_data))
        
        duration = len(audio_data) / (SAMPLE_RATE * CHANNELS * SAMPLE_WIDTH)
        print(f"\n[OK] Áudio salvo: {filename}")
        print(f"    Duração: {duration:.2f}s")
        print(f"    Tamanho: {len(audio_data)} bytes")
    except Exception as e:
        print(f"\n[ERRO] Não foi possível salvar: {e}")

def main():
    global recording, audio_data
    
    print("\n" + "="*70)
    print("  TESTE DE MICROFONE - ESP32")
    print("="*70)
    print(f"\nBroker: {MQTT_BROKER}:{MQTT_PORT}")
    print(f"Tópico: {TOPIC_MIC}")
    print("\nComandos:")
    print("  G = Gravar (iniciar gravação)")
    print("  S = Salvar (parar e salvar gravação)")
    print("  Q = Sair")
    print("\n" + "-"*70)
    
    # Conectar ao MQTT
    print("\n[1/2] Conectando ao MQTT...")
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
    
    print("\n[2/2] Monitorando microfone...")
    print("      Fale no microfone ESP32!\n")
    print("-"*70)
    
    # Loop principal
    try:
        import sys
        import select
        
        while True:
            # Verifica se há input do usuário (apenas em sistemas Unix-like)
            # No Windows, use msvcrt
            try:
                import msvcrt
                if msvcrt.kbhit():
                    key = msvcrt.getch().decode('utf-8').upper()
                    
                    if key == 'G':
                        recording = True
                        audio_data = bytearray()
                        print("\n\n🔴 GRAVANDO... (Pressione S para parar)")
                    
                    elif key == 'S':
                        if recording:
                            recording = False
                            save_audio()
                            print("\n\nMonitorando novamente...\n")
                        else:
                            print("\n\n[AVISO] Não está gravando")
                    
                    elif key == 'Q':
                        break
            except ImportError:
                # Sistema Unix-like
                pass
            
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n\n[INFO] Encerrando...")
    
    client.loop_stop()
    client.disconnect()
    
    print("\nTeste concluído! ✓")

if __name__ == "__main__":
    main()
