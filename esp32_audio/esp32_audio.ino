/**
 * ESP32 Audio Player via MQTT
 * 
 * Recebe áudio PCM 16-bit mono 16kHz via MQTT e reproduz via I2S (MAX98357)
 * Suporta captura de áudio via microfone I2S (INMP441)
 * 
 * Hardware:
 *   - ESP32 WROOM-32
 *   - MAX98357 I2S Amplifier (Speaker)
 *   - Microfone I2S (INMP441 ou similar)
 *   - Speaker 3W 4 ohm
 * 
 * Pinos I2S Speaker:
 *   - BCLK: GPIO 26 (compartilhado)
 *   - LRC:  GPIO 25 (compartilhado)
 *   - DIN:  GPIO 32
 * 
 * Pinos I2S Microfone:
 *   - SCK:  GPIO 26 (compartilhado com BCLK)
 *   - WS:   GPIO 25 (compartilhado com LRC)
 *   - SD:   GPIO 33
 * 
 * Autor: Ralu Project
 * Data: Maio 2026
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <driver/i2s.h>
#include "config.h"

// ============================================
// DEFINIÇÕES I2S
// ============================================
// I2S para saída de áudio (MAX98357 - Speaker)
#define I2S_SPEAKER_NUM     I2S_NUM_0
#define I2S_SPEAKER_BCLK    26
#define I2S_SPEAKER_LRC     25
#define I2S_SPEAKER_DIN     32

// I2S para entrada de áudio (Microfone)
#define I2S_MIC_NUM         I2S_NUM_1
#define I2S_MIC_SCK         26
#define I2S_MIC_WS          25
#define I2S_MIC_SD          33

// Configurações de áudio
#define SAMPLE_RATE     16000
#define BITS_PER_SAMPLE I2S_BITS_PER_SAMPLE_16BIT
#define CHANNEL_FORMAT  I2S_CHANNEL_FMT_ONLY_LEFT
#define DMA_BUF_COUNT   8
#define DMA_BUF_LEN     1024

// ============================================
// BUFFER DE ÁUDIO (Ring Buffer)
// ============================================
#define AUDIO_BUFFER_SIZE (32 * 1024)  // 32KB buffer circular

volatile uint8_t audioBuffer[AUDIO_BUFFER_SIZE];
volatile size_t bufferWritePos = 0;
volatile size_t bufferReadPos = 0;
volatile size_t bufferAvailable = 0;

// Mutex para proteção do buffer
portMUX_TYPE bufferMux = portMUX_INITIALIZER_UNLOCKED;

// ============================================
// OBJETOS GLOBAIS
// ============================================
WiFiClient espClient;
PubSubClient mqttClient(espClient);

// Task handles
TaskHandle_t audioTaskHandle = NULL;
TaskHandle_t micTaskHandle = NULL;

// Flags de status
volatile bool isPlaying = false;
volatile bool micEnabled = true;  // Microfone ativo por padrão

// ============================================
// PROTÓTIPOS DE FUNÇÕES
// ============================================
void setupWiFi();
void setupI2S();
void setupMQTT();
void reconnectMQTT();
void mqttCallback(char* topic, byte* payload, unsigned int length);
void audioPlayTask(void* parameter);
void micCaptureTask(void* parameter);
size_t writeToBuffer(const uint8_t* data, size_t len);
size_t readFromBuffer(uint8_t* data, size_t len);
size_t getBufferAvailable();

// ============================================
// SETUP
// ============================================
void setup() {
    Serial.begin(115200);
    delay(1000);
    
    Serial.println();
    Serial.println("========================================");
    Serial.println("  ESP32 Audio Player via MQTT");
    Serial.println("  Ralu Project - Abril 2026");
    Serial.println("========================================");
    Serial.println();
    
    // Inicializa WiFi
    setupWiFi();
    
    // Inicializa I2S
    setupI2S();
    
    // Inicializa MQTT
    setupMQTT();
    
    // Cria task de reprodução de áudio no Core 1
    xTaskCreatePinnedToCore(
        audioPlayTask,      // Função da task
        "AudioTask",        // Nome
        4096,               // Stack size
        NULL,               // Parâmetro
        1,                  // Prioridade
        &audioTaskHandle,   // Handle
        1                   // Core (1 = segundo core)
    );    
    // Cria task de captura do microfone no Core 0
    xTaskCreatePinnedToCore(
        micCaptureTask,     // Função da task
        "MicTask",          // Nome
        4096,               // Stack size
        NULL,               // Parâmetro
        1,                  // Prioridade
        &micTaskHandle,     // Handle
        0                   // Core 0
    );    
    Serial.println("[SETUP] Sistema inicializado com sucesso!");
    Serial.println();
}

// ============================================
// LOOP PRINCIPAL
// ============================================
void loop() {
    // Verifica conexão WiFi
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("[WIFI] Conexão perdida, reconectando...");
        setupWiFi();
    }
    
    // Verifica conexão MQTT
    if (!mqttClient.connected()) {
        reconnectMQTT();
    }
    
    // Processa mensagens MQTT
    mqttClient.loop();
    
    // Pequeno delay para evitar watchdog
    delay(10);
}

// ============================================
// CONFIGURAÇÃO DO WIFI
// ============================================
void setupWiFi() {
    Serial.print("[WIFI] Conectando a ");
    Serial.println(WIFI_SSID);
    
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    
    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 30) {
        delay(500);
        Serial.print(".");
        attempts++;
    }
    
    if (WiFi.status() == WL_CONNECTED) {
        Serial.println();
        Serial.println("[WIFI] Conectado!");
        Serial.print("[WIFI] IP: ");
        Serial.println(WiFi.localIP());
    } else {
        Serial.println();
        Serial.println("[WIFI] Falha na conexão. Reiniciando...");
        ESP.restart();
    }
}

// ============================================
// CONFIGURAÇÃO DO I2S (MAX98357 + Microfone)
// ============================================
void setupI2S() {
    Serial.println("[I2S] Configurando drivers I2S...");
    
    // ========== Configuração I2S SPEAKER (Saída) ==========
    i2s_config_t speaker_config = {
        .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX),
        .sample_rate = SAMPLE_RATE,
        .bits_per_sample = BITS_PER_SAMPLE,
        .channel_format = CHANNEL_FORMAT,
        .communication_format = I2S_COMM_FORMAT_STAND_I2S,
        .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
        .dma_buf_count = DMA_BUF_COUNT,
        .dma_buf_len = DMA_BUF_LEN,
        .use_apll = false,
        .tx_desc_auto_clear = true,
        .fixed_mclk = 0
    };
    
    i2s_pin_config_t speaker_pins = {
        .bck_io_num = I2S_SPEAKER_BCLK,
        .ws_io_num = I2S_SPEAKER_LRC,
        .data_out_num = I2S_SPEAKER_DIN,
        .data_in_num = I2S_PIN_NO_CHANGE
    };
    
    esp_err_t err = i2s_driver_install(I2S_SPEAKER_NUM, &speaker_config, 0, NULL);
    if (err != ESP_OK) {
        Serial.printf("[I2S] Erro ao instalar driver speaker: %d\n", err);
        return;
    }
    
    err = i2s_set_pin(I2S_SPEAKER_NUM, &speaker_pins);
    if (err != ESP_OK) {
        Serial.printf("[I2S] Erro ao configurar pinos speaker: %d\n", err);
        return;
    }
    
    i2s_zero_dma_buffer(I2S_SPEAKER_NUM);
    
    Serial.println("[I2S] Speaker configurado:");
    Serial.printf("  BCLK: GPIO%d | LRC: GPIO%d | DIN: GPIO%d\n", 
                  I2S_SPEAKER_BCLK, I2S_SPEAKER_LRC, I2S_SPEAKER_DIN);
    
    // ========== Configuração I2S MICROFONE (Entrada) ==========
    i2s_config_t mic_config = {
        .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
        .sample_rate = SAMPLE_RATE,
        .bits_per_sample = BITS_PER_SAMPLE,
        .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,  // INMP441 usa LEFT channel
        .communication_format = I2S_COMM_FORMAT_I2S,
        .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
        .dma_buf_count = 8,  // Mais buffers para estabilidade
        .dma_buf_len = 256,  // Buffers menores para latencia baixa
        .use_apll = false,
        .tx_desc_auto_clear = false,
        .fixed_mclk = 0
    };
    
    i2s_pin_config_t mic_pins = {
        .bck_io_num = I2S_MIC_SCK,
        .ws_io_num = I2S_MIC_WS,
        .data_out_num = I2S_PIN_NO_CHANGE,
        .data_in_num = I2S_MIC_SD
    };
    
    err = i2s_driver_install(I2S_MIC_NUM, &mic_config, 0, NULL);
    if (err != ESP_OK) {
        Serial.printf("[I2S] Erro ao instalar driver microfone: %d\n", err);
        return;
    }
    
    err = i2s_set_pin(I2S_MIC_NUM, &mic_pins);
    if (err != ESP_OK) {
        Serial.printf("[I2S] Erro ao configurar pinos microfone: %d\n", err);
        return;
    }
    
    i2s_zero_dma_buffer(I2S_MIC_NUM);
    
    Serial.println("[I2S] Microfone configurado:");
    Serial.printf("  SCK: GPIO%d | WS: GPIO%d | SD: GPIO%d\n", 
                  I2S_MIC_SCK, I2S_MIC_WS, I2S_MIC_SD);
    Serial.println("[I2S] Filtro de ruido ativado");
    
    Serial.println("[I2S] Todos os drivers configurados!");
    Serial.printf("[I2S] Sample Rate: %d Hz | Bits: %d\n", SAMPLE_RATE, BITS_PER_SAMPLE);
}

// ============================================
// CONFIGURAÇÃO DO MQTT
// ============================================
void setupMQTT() {
    Serial.print("[MQTT] Configurando broker: ");
    Serial.print(MQTT_BROKER);
    Serial.print(":");
    Serial.println(MQTT_PORT);
    
    mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
    mqttClient.setCallback(mqttCallback);
    
    // Define tamanho máximo do buffer MQTT (16KB para chunks de áudio)
    mqttClient.setBufferSize(16384);
    
    reconnectMQTT();
}

// ============================================
// RECONEXÃO MQTT
// ============================================
void reconnectMQTT() {
    int attempts = 0;
    
    while (!mqttClient.connected() && attempts < 5) {
        Serial.print("[MQTT] Tentando conexão...");
        
        // Gera client ID único
        String clientId = "ESP32Audio-";
        clientId += String(random(0xffff), HEX);
        
        if (mqttClient.connect(clientId.c_str())) {
            Serial.println(" conectado!");
            
            // Inscreve no tópico de áudio
            mqttClient.subscribe(MQTT_TOPIC_AUDIO);
            Serial.print("[MQTT] Inscrito em: ");
            Serial.println(MQTT_TOPIC_AUDIO);
            
            // Inscreve no tópico de controle
            mqttClient.subscribe(MQTT_TOPIC_CONTROL);
            Serial.print("[MQTT] Inscrito em: ");
            Serial.println(MQTT_TOPIC_CONTROL);
            
            // Publica status online
            mqttClient.publish(MQTT_TOPIC_STATUS, "online");
            
        } else {
            Serial.print(" falhou (rc=");
            Serial.print(mqttClient.state());
            Serial.println("). Tentando novamente em 2s...");
            delay(2000);
            attempts++;
        }
    }
}

// ============================================
// CALLBACK MQTT - RECEBE DADOS
// ============================================
void mqttCallback(char* topic, byte* payload, unsigned int length) {
    // Tópico de áudio - dados binários PCM
    if (strcmp(topic, MQTT_TOPIC_AUDIO) == 0) {
        // Escreve no buffer circular
        size_t written = writeToBuffer(payload, length);
        
        if (written < length) {
            Serial.println("[AUDIO] Buffer overflow! Alguns dados perdidos.");
        }
        
        // Inicia reprodução se não estiver tocando
        if (!isPlaying && getBufferAvailable() > DMA_BUF_LEN * 4) {
            isPlaying = true;
        }
        
        return;
    }
    
    // Tópico de controle - comandos texto
    if (strcmp(topic, MQTT_TOPIC_CONTROL) == 0) {
        // Converte para string
        char cmd[64];
        size_t cmdLen = min((unsigned int)63, length);
        memcpy(cmd, payload, cmdLen);
        cmd[cmdLen] = '\0';
        
        Serial.print("[CTRL] Comando recebido: ");
        Serial.println(cmd);
        
        // Processa comandos
        if (strcmp(cmd, "stop") == 0) {
            isPlaying = false;
            // Limpa buffer
            portENTER_CRITICAL(&bufferMux);
            bufferWritePos = 0;
            bufferReadPos = 0;
            bufferAvailable = 0;
            portEXIT_CRITICAL(&bufferMux);
            i2s_zero_dma_buffer(I2S_SPEAKER_NUM);
            Serial.println("[CTRL] Reprodução parada, buffer limpo.");
            
        } else if (strcmp(cmd, "status") == 0) {
            char statusMsg[128];
            snprintf(statusMsg, sizeof(statusMsg), 
                     "{\"playing\":%s,\"buffer\":%d,\"wifi\":\"%s\"}",
                     isPlaying ? "true" : "false",
                     getBufferAvailable(),
                     WiFi.localIP().toString().c_str());
            mqttClient.publish(MQTT_TOPIC_STATUS, statusMsg);
        }
        
        return;
    }
}

// ============================================
// TASK DE REPRODUÇÃO DE ÁUDIO (Core 1)
// ============================================
void audioPlayTask(void* parameter) {
    uint8_t audioChunk[DMA_BUF_LEN];
    size_t bytesWritten;
    
    Serial.println("[AUDIO] Task de reprodução iniciada no Core 1");
    
    while (true) {
        if (isPlaying) {
            // Lê dados do buffer circular
            size_t available = getBufferAvailable();
            
            if (available >= DMA_BUF_LEN) {
                // Lê um chunk do buffer
                size_t bytesRead = readFromBuffer(audioChunk, DMA_BUF_LEN);
                
                if (bytesRead > 0) {
                    // Envia para I2S Speaker
                    i2s_write(I2S_SPEAKER_NUM, audioChunk, bytesRead, &bytesWritten, portMAX_DELAY);
                }
            } else if (available == 0) {
                // Buffer vazio, para de tocar
                isPlaying = false;
                Serial.println("[AUDIO] Buffer vazio, aguardando dados...");
            } else {
                // Dados insuficientes, aguarda um pouco
                vTaskDelay(pdMS_TO_TICKS(5));
            }
        } else {
            // Não está tocando, aguarda
            vTaskDelay(pdMS_TO_TICKS(10));
        }
    }
}

// ============================================
// TASK DE CAPTURA DO MICROFONE (Core 0)
// ============================================
void micCaptureTask(void* parameter) {
    const size_t BUFFER_SIZE = 512;
    int32_t micBuffer[BUFFER_SIZE / 4];  // Buffer para samples 32-bit
    int16_t processedBuffer[BUFFER_SIZE / 4];  // Buffer para samples 16-bit processados
    size_t bytesRead;
    
    // ========== FILTROS PARA VOZ HUMANA (300-3400 Hz) ==========
    
    // Filtro passa-alta (corta abaixo de ~300 Hz - remove ruído de baixa freq)
    float hp_alpha = 0.98;  // Coeficiente mais agressivo
    float hp_lastInput = 0;
    float hp_lastOutput = 0;
    
    // Filtro passa-baixa (corta acima de ~3400 Hz - remove ruído de alta freq)
    float lp_alpha = 0.3;   // Coeficiente do filtro passa-baixa
    float lp_lastOutput = 0;
    
    // Média móvel para suavizar (reduz picos de ruído)
    const int MA_SIZE = 3;
    float movingAvg[MA_SIZE] = {0, 0, 0};
    int maIndex = 0;
    
    // Noise gate agressivo
    const int16_t NOISE_THRESHOLD = 500;  // Limiar bem alto para voz
    
    // Limitador de ganho automático (AGC)
    const float TARGET_LEVEL = 8000.0;
    float currentGain = 1.0;
    
    Serial.println("[MIC] Task de captura iniciada no Core 0");
    Serial.println("[MIC] Filtros ativos:");
    Serial.println("      - Passa-banda: 300-3400 Hz (frequências de voz)");
    Serial.println("      - Noise gate: 500 (supressão de ruído)");
    Serial.println("      - Média móvel: 3 samples (suavização)");
    
    vTaskDelay(pdMS_TO_TICKS(2000));  // Aguarda 2s para MQTT conectar
    
    while (true) {
        if (micEnabled && mqttClient.connected()) {
            // Lê áudio do microfone via I2S (32-bit)
            esp_err_t result = i2s_read(I2S_MIC_NUM, micBuffer, BUFFER_SIZE, &bytesRead, portMAX_DELAY);
            
            if (result == ESP_OK && bytesRead > 0) {
                size_t samplesRead = bytesRead / 4;  // 4 bytes por sample (32-bit)
                
                float maxLevel = 0;
                
                // Processa cada sample
                for (size_t i = 0; i < samplesRead; i++) {
                    // Converte 32-bit para 16-bit (pega os 16 bits mais significativos)
                    int16_t sample = (int16_t)(micBuffer[i] >> 16);
                    
                    // === ETAPA 1: Filtro Passa-Alta (remove DC e ruído <300Hz) ===
                    float input = (float)sample;
                    float hp_output = hp_alpha * (hp_lastOutput + input - hp_lastInput);
                    hp_lastInput = input;
                    hp_lastOutput = hp_output;
                    
                    // === ETAPA 2: Filtro Passa-Baixa (remove ruído >3400Hz) ===
                    lp_lastOutput = lp_alpha * hp_output + (1.0 - lp_alpha) * lp_lastOutput;
                    
                    // === ETAPA 3: Média Móvel (suavização) ===
                    movingAvg[maIndex] = lp_lastOutput;
                    maIndex = (maIndex + 1) % MA_SIZE;
                    float smoothed = 0;
                    for (int j = 0; j < MA_SIZE; j++) {
                        smoothed += movingAvg[j];
                    }
                    smoothed /= MA_SIZE;
                    
                    // === ETAPA 4: Noise Gate (silencia ruído baixo) ===
                    int16_t filtered = (int16_t)smoothed;
                    if (abs(filtered) < NOISE_THRESHOLD) {
                        filtered = 0;
                    }
                    
                    // === ETAPA 5: AGC simples (ajusta ganho) ===
                    filtered = (int16_t)(filtered * currentGain);
                    
                    // Limita para não saturar
                    if (filtered > 16000) filtered = 16000;
                    if (filtered < -16000) filtered = -16000;
                    
                    processedBuffer[i] = filtered;
                    
                    // Calcula nível máximo para AGC
                    float absVal = abs(filtered);
                    if (absVal > maxLevel) maxLevel = absVal;
                }
                
                // Ajusta ganho automaticamente (AGC lento)
                if (maxLevel > 0) {
                    float idealGain = TARGET_LEVEL / maxLevel;
                    currentGain = 0.95 * currentGain + 0.05 * idealGain;  // Suaviza ajuste
                    // Limita ganho
                    if (currentGain > 4.0) currentGain = 4.0;
                    if (currentGain < 0.5) currentGain = 0.5;
                }
                
                // Publica áudio processado via MQTT
                mqttClient.publish(MQTT_TOPIC_MIC, (uint8_t*)processedBuffer, samplesRead * 2);
            }
            
            // Pequeno delay para não sobrecarregar
            vTaskDelay(pdMS_TO_TICKS(5));
        } else {
            // Microfone desabilitado ou MQTT desconectado
            vTaskDelay(pdMS_TO_TICKS(100));
        }
    }
}

// ============================================
// FUNÇÕES DO BUFFER CIRCULAR
// ============================================

/**
 * Escreve dados no buffer circular
 * Retorna quantidade de bytes escritos
 */
size_t writeToBuffer(const uint8_t* data, size_t len) {
    size_t written = 0;
    
    portENTER_CRITICAL(&bufferMux);
    
    while (written < len && bufferAvailable < AUDIO_BUFFER_SIZE) {
        audioBuffer[bufferWritePos] = data[written];
        bufferWritePos = (bufferWritePos + 1) % AUDIO_BUFFER_SIZE;
        bufferAvailable++;
        written++;
    }
    
    portEXIT_CRITICAL(&bufferMux);
    
    return written;
}

/**
 * Lê dados do buffer circular
 * Retorna quantidade de bytes lidos
 */
size_t readFromBuffer(uint8_t* data, size_t len) {
    size_t bytesRead = 0;
    
    portENTER_CRITICAL(&bufferMux);
    
    while (bytesRead < len && bufferAvailable > 0) {
        data[bytesRead] = audioBuffer[bufferReadPos];
        bufferReadPos = (bufferReadPos + 1) % AUDIO_BUFFER_SIZE;
        bufferAvailable--;
        bytesRead++;
    }
    
    portEXIT_CRITICAL(&bufferMux);
    
    return bytesRead;
}

/**
 * Retorna quantidade de bytes disponíveis no buffer
 */
size_t getBufferAvailable() {
    size_t available;
    
    portENTER_CRITICAL(&bufferMux);
    available = bufferAvailable;
    portEXIT_CRITICAL(&bufferMux);
    
    return available;
}
