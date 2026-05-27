# ESP32 Audio Player via MQTT

Código para ESP32 que recebe áudio via MQTT e reproduz através de um amplificador I2S MAX98357.

## Hardware Necessário

| Componente | Descrição |
|------------|-----------|
| ESP32 | WROOM-32 ou similar |
| Microfone I2S | INMP441 ou similar |
| MAX98357 | Amplificador I2S |
| Speaker | 3W 4 ohm |
| Fios | Jumpers para conexão |

## Diagrama de Conexões

```
     Microfone I2S          ESP32                    MAX98357
    ┌──────────┐         ┌──────────┐            ┌──────────┐
    │      VDD ├─────────┤ 3V3      │            │          │
    │      GND ├─────────┤ GND      ├────────────┤ GND      │
    │      SCK ├─────────┤ GPIO26   ├────────────┤ BCLK     │
    │       WS ├─────────┤ GPIO25   ├────────────┤ LRC (WS) │
    │       SD ├─────────┤ GPIO33   │            │          │
    │        L ├──GND    │ GPIO32   ├────────────┤ DIN      │
    └──────────┘         │      3V3 ├────────────┤ VIN      │
                         └──────────┘            │      OUT+├───┐
                                                 │      OUT-├─┐ │
                                                 └──────────┘ │ │
                                                              │ │
                                                       Speaker │ │
                                                       ┌─────┐ │ │
                                                       │  +  ├─┘ │
                                                       │  -  ├───┘
                                                       └─────┘
```

### Pinos I2S

**Microfone (Entrada):**

| Sinal | GPIO ESP32 | Pino Microfone |
|-------|------------|----------------|
| SCK   | GPIO 26    | SCK (BCLK)     |
| WS    | GPIO 25    | WS (LRC)       |
| SD    | GPIO 33    | SD (DOUT)      |

**Amplificador MAX98357 (Saída):**

| Sinal | GPIO ESP32 | Pino MAX98357 |
|-------|------------|---------------|
| BCLK  | GPIO 26    | BCLK          |
| LRC   | GPIO 25    | LRC (WS)      |
| DIN   | GPIO 32    | DIN           |

**Nota:** GPIO26 e GPIO25 são compartilhados entre microfone e speaker (clock comum)

## Instalação

### 1. Arduino IDE

1. Instale o suporte para ESP32:
   - Vá em **Arquivo > Preferências**
   - Adicione a URL: `https://dl.espressif.com/dl/package_esp32_index.json`
   - Vá em **Ferramentas > Placa > Gerenciador de Placas**
   - Pesquise "esp32" e instale

2. Instale a biblioteca **PubSubClient**:
   - Vá em **Sketch > Incluir Biblioteca > Gerenciar Bibliotecas**
   - Pesquise "PubSubClient" e instale

### 2. Configuração

Edite o arquivo `config.h` com suas credenciais:

```cpp
#define WIFI_SSID       "SuaRedeWiFi"
#define WIFI_PASSWORD   "SuaSenhaWiFi"
#define MQTT_BROKER     "192.168.1.100"  // IP do seu broker
```

### 3. Upload

1. Conecte o ESP32 via USB
2. Selecione a placa: **ESP32 Dev Module**
3. Selecione a porta COM correta
4. Clique em **Upload**

## Protocolo de Comunicação

### Formato do Áudio

- **Formato:** PCM raw
- **Bits:** 16-bit signed
- **Canais:** Mono
- **Sample Rate:** 16000 Hz
- **Byte Order:** Little-endian

### Tópicos MQTT

| Tópico | Direção | Descrição |
|--------|---------|-----------|
| `ralu/audio/stream` | Ralu → ESP32 | Chunks de áudio PCM binário |
| `ralu/audio/control` | Ralu → ESP32 | Comandos: "stop", "status" |
| `ralu/audio/status` | ESP32 → Ralu | Status JSON |

### Comandos de Controle

| Comando | Descrição |
|---------|-----------|
| `stop` | Para reprodução e limpa buffer |
| `status` | Retorna status JSON |

### Resposta de Status

```json
{
  "playing": true,
  "buffer": 4096,
  "wifi": "192.168.1.50"
}
```

## Exemplo de Envio (Python)

```python
import paho.mqtt.client as mqtt

# Conectar ao broker
client = mqtt.Client()
client.connect("192.168.1.100", 1883)

# Ler arquivo de áudio PCM
with open("audio.raw", "rb") as f:
    audio_data = f.read()

# Enviar em chunks de 4KB
CHUNK_SIZE = 4096
for i in range(0, len(audio_data), CHUNK_SIZE):
    chunk = audio_data[i:i+CHUNK_SIZE]
    client.publish("ralu/audio/stream", chunk)
    time.sleep(0.1)  # Delay entre chunks

# Parar reprodução
# client.publish("ralu/audio/control", "stop")
```

## Conversão de Áudio

Converta qualquer áudio para o formato esperado usando ffmpeg:

```bash
ffmpeg -i input.mp3 -ar 16000 -ac 1 -f s16le output.raw
```

Parâmetros:
- `-ar 16000`: Sample rate 16kHz
- `-ac 1`: Mono
- `-f s16le`: PCM 16-bit little-endian

## Arquitetura do Código

```
┌─────────────────────────────────────────────────────────┐
│                      SETUP                               │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐                  │
│  │  WiFi   │  │   I2S   │  │  MQTT   │                  │
│  └─────────┘  └─────────┘  └─────────┘                  │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                     LOOP (Core 0)                        │
│  ┌────────────────────────────────────────────────────┐ │
│  │  WiFi Check → MQTT Reconnect → MQTT Loop           │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                          │
          MQTT Callback   │   Ring Buffer
                ▼         │        ▼
┌───────────────────┐    │    ┌───────────────────┐
│ Recebe PCM chunks │────┼───▶│ Armazena 32KB     │
└───────────────────┘    │    └───────────────────┘
                          │           │
                          │           ▼
┌─────────────────────────────────────────────────────────┐
│                 AUDIO TASK (Core 1)                      │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Lê do Buffer → Envia para I2S → MAX98357 → Som    │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## Características

- **Dual I2S:** Microfone (entrada) + Speaker (saída)
- **Clock compartilhado:** GPIO26 (BCLK) e GPIO25 (WS) compartilhados
- **Buffer Circular:** 32KB para absorver variações de rede
- **Dual Core:** MQTT no Core 0, áudio no Core 1
- **Thread-safe:** Mutex para acesso ao buffer
- **Reconexão Automática:** WiFi e MQTT
- **DMA:** Buffer de 8x1024 para I2S

## Troubleshooting

| Problema | Solução |
|----------|---------|
| Sem som | Verifique conexões, especialmente GND |
| Som cortado | Aumente `AUDIO_BUFFER_SIZE` ou `DMA_BUF_COUNT` |
| Ruído/estática | Verifique sample rate no envio (deve ser 16kHz) |
| WiFi não conecta | Verifique credenciais em config.h |
| MQTT não conecta | Verifique IP do broker e firewall |

## Monitor Serial

O código imprime logs na serial (115200 baud):

```
========================================
  ESP32 Audio Player via MQTT
  Ralu Project - Abril 2026
========================================

[WIFI] Conectando a MinhaRede
...
[WIFI] Conectado!
[WIFI] IP: 192.168.1.50
[I2S] Configurando driver I2S...
[I2S] Driver configurado com sucesso!
[MQTT] Configurando broker: 192.168.1.100:1883
[MQTT] Tentando conexão... conectado!
[MQTT] Inscrito em: ralu/audio/stream
[AUDIO] Task de reprodução iniciada no Core 1
[SETUP] Sistema inicializado com sucesso!
```

