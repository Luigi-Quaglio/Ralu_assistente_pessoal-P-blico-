"""
Módulo para enviar áudio para ESP32 via MQTT

Converte texto em áudio usando Piper TTS e transmite para ESP32
"""
import os
import time
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("Instale: pip install paho-mqtt")
    mqtt = None

logger = logging.getLogger(__name__)

# Configurações padrão
DEFAULT_MQTT_BROKER = "localhost"
DEFAULT_MQTT_PORT = 1883
TOPIC_AUDIO = "ralu/audio/stream"
TOPIC_CONTROL = "ralu/audio/control"
TOPIC_STATUS = "ralu/audio/status"

# Tamanho do chunk de áudio (bytes)
CHUNK_SIZE = 4096

# Delay entre chunks (segundos) - ajuste conforme necessário
CHUNK_DELAY = 0.05

# Configuração do Piper (ajuste os caminhos)
PIPER_EXE = Path(r"C:\piper\piper.exe")
PIPER_MODEL = Path(r"C:\piper\pt_BR-edresson-low.onnx")


class ESP32AudioSender:
    """
    Classe para enviar áudio para ESP32 via MQTT
    """
    
    def __init__(
        self,
        broker: str = DEFAULT_MQTT_BROKER,
        port: int = DEFAULT_MQTT_PORT,
        piper_exe: Path = PIPER_EXE,
        piper_model: Path = PIPER_MODEL
    ):
        if mqtt is None:
            raise ImportError("paho-mqtt não instalado")
        
        self.broker = broker
        self.port = port
        self.piper_exe = piper_exe
        self.piper_model = piper_model
        
        self.client = mqtt.Client()
        self.connected = False
        
        # Callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
    
    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info(f"Conectado ao broker MQTT: {self.broker}:{self.port}")
            self.connected = True
            # Inscreve no tópico de status
            client.subscribe(TOPIC_STATUS)
        else:
            logger.error(f"Falha na conexão MQTT. Código: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        logger.warning("Desconectado do broker MQTT")
        self.connected = False
    
    def _on_message(self, client, userdata, msg):
        logger.info(f"ESP32 Status: {msg.payload.decode()}")
    
    def connect(self) -> bool:
        """Conecta ao broker MQTT"""
        try:
            self.client.connect(self.broker, self.port, keepalive=60)
            self.client.loop_start()
            
            # Aguarda conexão
            timeout = 5
            while not self.connected and timeout > 0:
                time.sleep(0.1)
                timeout -= 0.1
            
            return self.connected
        except Exception as e:
            logger.error(f"Erro ao conectar MQTT: {e}")
            return False
    
    def disconnect(self):
        """Desconecta do broker"""
        self.client.loop_stop()
        self.client.disconnect()
        self.connected = False
    
    def send_raw_audio(self, audio_data: bytes) -> bool:
        """
        Envia dados de áudio PCM raw para ESP32
        
        Args:
            audio_data: Bytes PCM 16-bit mono 16kHz little-endian
        
        Returns:
            True se enviado com sucesso
        """
        if not self.connected:
            logger.error("Não conectado ao MQTT")
            return False
        
        try:
            total_chunks = (len(audio_data) + CHUNK_SIZE - 1) // CHUNK_SIZE
            logger.info(f"Enviando {len(audio_data)} bytes em {total_chunks} chunks")
            
            for i in range(0, len(audio_data), CHUNK_SIZE):
                chunk = audio_data[i:i + CHUNK_SIZE]
                self.client.publish(TOPIC_AUDIO, chunk)
                time.sleep(CHUNK_DELAY)
            
            logger.info("Áudio enviado com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao enviar áudio: {e}")
            return False
    
    def send_file(self, filepath: str) -> bool:
        """
        Envia arquivo de áudio PCM raw
        
        Args:
            filepath: Caminho para arquivo .raw PCM
        
        Returns:
            True se enviado com sucesso
        """
        try:
            with open(filepath, "rb") as f:
                audio_data = f.read()
            return self.send_raw_audio(audio_data)
        except Exception as e:
            logger.error(f"Erro ao ler arquivo: {e}")
            return False
    
    def text_to_speech_and_send(self, text: str) -> bool:
        """
        Converte texto em fala com Piper e envia para ESP32
        
        Args:
            text: Texto para converter
        
        Returns:
            True se enviado com sucesso
        """
        if not self.piper_exe.exists():
            logger.error(f"Piper não encontrado: {self.piper_exe}")
            return False
        
        if not self.piper_model.exists():
            logger.error(f"Modelo Piper não encontrado: {self.piper_model}")
            return False
        
        try:
            # Cria arquivo WAV temporário
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_wav:
                wav_path = tmp_wav.name
            
            with tempfile.NamedTemporaryFile(suffix=".raw", delete=False) as tmp_raw:
                raw_path = tmp_raw.name
            
            # Gera áudio com Piper
            logger.info(f"Gerando TTS: {text[:50]}...")
            
            result = subprocess.run(
                [
                    str(self.piper_exe),
                    "--model", str(self.piper_model),
                    "--output_file", wav_path
                ],
                input=text.encode("utf-8"),
                capture_output=True
            )
            
            if result.returncode != 0:
                logger.error(f"Erro no Piper: {result.stderr.decode()}")
                return False
            
            # Converte WAV para PCM raw 16kHz mono
            # O Piper gera 22050Hz, precisamos converter para 16000Hz
            ffmpeg_cmd = [
                "ffmpeg", "-y", "-i", wav_path,
                "-ar", "16000",  # Sample rate
                "-ac", "1",      # Mono
                "-f", "s16le",   # PCM 16-bit little-endian
                raw_path
            ]
            
            result = subprocess.run(ffmpeg_cmd, capture_output=True)
            
            if result.returncode != 0:
                logger.error(f"Erro no ffmpeg: {result.stderr.decode()}")
                return False
            
            # Envia o áudio
            success = self.send_file(raw_path)
            
            return success
            
        except Exception as e:
            logger.error(f"Erro no TTS: {e}")
            return False
            
        finally:
            # Limpa arquivos temporários
            for path in [wav_path, raw_path]:
                try:
                    if os.path.exists(path):
                        os.unlink(path)
                except:
                    pass
    
    def stop(self):
        """Envia comando de parar para ESP32"""
        if self.connected:
            self.client.publish(TOPIC_CONTROL, "stop")
            logger.info("Comando 'stop' enviado")
    
    def get_status(self):
        """Solicita status do ESP32"""
        if self.connected:
            self.client.publish(TOPIC_CONTROL, "status")
            logger.info("Comando 'status' enviado")


# ============================================
# FUNÇÕES UTILITÁRIAS
# ============================================

def send_text_to_esp32(
    text: str,
    broker: str = DEFAULT_MQTT_BROKER,
    port: int = DEFAULT_MQTT_PORT
) -> bool:
    """
    Função helper para enviar texto como áudio para ESP32
    
    Args:
        text: Texto para falar
        broker: Endereço do broker MQTT
        port: Porta do broker
    
    Returns:
        True se enviado com sucesso
    """
    sender = ESP32AudioSender(broker=broker, port=port)
    
    try:
        if not sender.connect():
            return False
        
        return sender.text_to_speech_and_send(text)
        
    finally:
        sender.disconnect()


def send_raw_to_esp32(
    audio_data: bytes,
    broker: str = DEFAULT_MQTT_BROKER,
    port: int = DEFAULT_MQTT_PORT
) -> bool:
    """
    Função helper para enviar áudio raw para ESP32
    
    Args:
        audio_data: Bytes PCM 16-bit mono 16kHz
        broker: Endereço do broker MQTT
        port: Porta do broker
    
    Returns:
        True se enviado com sucesso
    """
    sender = ESP32AudioSender(broker=broker, port=port)
    
    try:
        if not sender.connect():
            return False
        
        return sender.send_raw_audio(audio_data)
        
    finally:
        sender.disconnect()


# ============================================
# EXEMPLO DE USO
# ============================================

if __name__ == "__main__":
    import argparse
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    
    parser = argparse.ArgumentParser(description="Envia áudio para ESP32 via MQTT")
    parser.add_argument("--broker", default="localhost", help="Endereço do broker MQTT")
    parser.add_argument("--port", type=int, default=1883, help="Porta MQTT")
    parser.add_argument("--text", help="Texto para converter em fala")
    parser.add_argument("--file", help="Arquivo PCM raw para enviar")
    parser.add_argument("--stop", action="store_true", help="Envia comando de parar")
    
    args = parser.parse_args()
    
    sender = ESP32AudioSender(broker=args.broker, port=args.port)
    
    if not sender.connect():
        print("Falha ao conectar ao MQTT")
        exit(1)
    
    try:
        if args.stop:
            sender.stop()
        elif args.text:
            sender.text_to_speech_and_send(args.text)
        elif args.file:
            sender.send_file(args.file)
        else:
            # Demo interativo
            print("Modo interativo. Digite texto para falar (Ctrl+C para sair):")
            while True:
                text = input("> ").strip()
                if text:
                    sender.text_to_speech_and_send(text)
    
    except KeyboardInterrupt:
        print("\nEncerrando...")
    
    finally:
        sender.disconnect()
