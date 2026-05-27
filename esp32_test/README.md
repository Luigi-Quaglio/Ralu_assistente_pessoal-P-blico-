# ESP32 MQTT Test Firmware

## 🎯 Objetivo

Firmware simplificado para testar comunicação MQTT da ESP32.

## ⚙️ O que faz:

- ✅ Conecta no WiFi
- ✅ Conecta no broker MQTT
- ✅ Envia mensagem de teste a cada **10 segundos**
- ✅ Captura áudio do microfone a cada **2 segundos**

## 📝 Configuração Rápida

**1. Edite este arquivo (`esp32_test.ino`) linhas 20-23:**

```cpp
const char* WIFI_SSID = "SUA_REDE_WIFI";        // ← Coloque seu WiFi
const char* WIFI_PASSWORD = "SUA_SENHA_WIFI";   // ← Coloque sua senha
const char* MQTT_BROKER = "192.168.1.13";       // ← Já configurado com o IP do seu PC!
```

**2. Conecte a ESP32 e faça Upload**

**3. Abra o Serial Monitor (115200 baud)**

## 📡 Tópicos MQTT

| Tópico | Conteúdo | Frequência |
|--------|----------|------------|
| `ralu/test` | `{"test":1,"counter":X,"uptime":Y,"rssi":Z}` | 10s |
| `ralu/mic/audio` | Dados PCM 16-bit (4KB) | 2s |
| `ralu/status` | `{"status":"online","ip":"192.168.1.X"}` | Ao conectar |

## 🧪 Como Testar

### No PC, rode o monitor:

```powershell
cd esp32_audio
python mqtt_monitor.py
```

Você verá as mensagens chegando! 📊

## 🔌 Pinos do Microfone

| Microfone | ESP32 |
|-----------|-------|
| VDD | 3V3 |
| GND | GND |
| SCK | GPIO 26 |
| WS | GPIO 25 |
| SD | GPIO 33 |
| L/R | GND |

## ✅ Sucesso!

Se no Serial Monitor você ver:

```
[WIFI] Conectado!
[MQTT] Conectado ao broker!
[TEST] Mensagem #1 enviada
[MIC] Capturado: 4096 bytes
```

