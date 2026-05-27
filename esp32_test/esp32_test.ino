/**
 * ESP32 MQTT Test Firmware
 * 
 * Testa envio de dados via MQTT:
 * - Envia valor "1" a cada 10 segundos
 * - Captura áudio do microfone e envia via MQTT
 * 
 * Pinos Microfone I2S:
 *   - SCK: GPIO 26
 *   - WS:  GPIO 25
 *   - SD:  GPIO 33
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <driver/i2s.h>

// ============================================
// CONFIGURAÇÕES - EDITE AQUI
// ============================================
const char* WIFI_SSID = "INTERNET.";
const char* WIFI_PASSWORD = "";//Não vai descobrir minha senha aqui, desista!
const char* MQTT_BROKER = "192.168.1.13";  // IP do seu PC
const int MQTT_PORT = 1883;

// Tópicos MQTT
const char* TOPIC_TEST = "ralu/test";
const char* TOPIC_AUDIO = "ralu/mic/audio";
const char* TOPIC_STATUS = "ralu/status";

// ============================================
// I2S - MICROFONE
// ============================================
#define I2S_MIC_NUM         I2S_NUM_0
#define I2S_MIC_SCK         26
#define I2S_MIC_WS          25
#define I2S_MIC_SD          33
#define SAMPLE_RATE         16000
#define I2S_READ_LEN        (4 * 1024)  // 4KB por leitura

// ============================================
// GLOBAIS
// ============================================
WiFiClient espClient;
PubSubClient mqttClient(espClient);

unsigned long lastTestMsg = 0;
unsigned long lastAudioCapture = 0;
int testCounter = 0;

// ============================================
// PROTÓTIPOS
// ============================================
void setupWiFi();
void setupI2SMic();
void setupMQTT();
void reconnectMQTT();
void sendTestMessage();
void captureAndSendAudio();

// ============================================
// SETUP
// ============================================
void setup() {
    Serial.begin(115200);
    delay(1000);
    
    Serial.println("\n========================================");
    Serial.println("  ESP32 MQTT Test - Ralu Project");
    Serial.println("========================================\n");
    
    setupWiFi();
    setupI2SMic();
    setupMQTT();
    
    Serial.println("[SETUP] Pronto! Iniciando testes...\n");
}

// ============================================
// LOOP
// ============================================
void loop() {
    // Reconecta WiFi se necessário
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("[WIFI] Reconectando...");
        setupWiFi();
    }
    
    // Reconecta MQTT se necessário
    if (!mqttClient.connected()) {
        reconnectMQTT();
    }
    
    mqttClient.loop();
    
    // Envia mensagem de teste a cada 10 segundos
    if (millis() - lastTestMsg >= 10000) {
        sendTestMessage();
        lastTestMsg = millis();
    }
    
    // Captura áudio a cada 2 segundos
    if (millis() - lastAudioCapture >= 2000) {
        captureAndSendAudio();
        lastAudioCapture = millis();
    }
    
    delay(10);
}

// ============================================
// CONFIGURAÇÃO WIFI
// ============================================
void setupWiFi() {
    Serial.print("[WIFI] Conectando a: ");
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
        Serial.println("\n[WIFI] Conectado!");
        Serial.print("[WIFI] IP: ");
        Serial.println(WiFi.localIP());
        Serial.print("[WIFI] RSSI: ");
        Serial.print(WiFi.RSSI());
        Serial.println(" dBm\n");
    } else {
        Serial.println("\n[WIFI] FALHA! Verifique credenciais.");
        Serial.println("[WIFI] Reiniciando em 5s...");
        delay(5000);
        ESP.restart();
    }
}

// ============================================
// CONFIGURAÇÃO I2S MICROFONE
// ============================================
void setupI2SMic() {
    Serial.println("[I2S] Configurando microfone...");
    
    i2s_config_t i2s_config = {
        .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
        .sample_rate = SAMPLE_RATE,
        .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
        .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
        .communication_format = I2S_COMM_FORMAT_I2S,
        .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
        .dma_buf_count = 4,
        .dma_buf_len = 1024,
        .use_apll = false,
        .tx_desc_auto_clear = false,
        .fixed_mclk = 0
    };
    
    i2s_pin_config_t pin_config = {
        .bck_io_num = I2S_MIC_SCK,
        .ws_io_num = I2S_MIC_WS,
        .data_out_num = I2S_PIN_NO_CHANGE,
        .data_in_num = I2S_MIC_SD
    };
    
    esp_err_t err = i2s_driver_install(I2S_MIC_NUM, &i2s_config, 0, NULL);
    if (err != ESP_OK) {
        Serial.printf("[I2S] ERRO ao instalar driver: %d\n", err);
        return;
    }
    
    err = i2s_set_pin(I2S_MIC_NUM, &pin_config);
    if (err != ESP_OK) {
        Serial.printf("[I2S] ERRO ao configurar pinos: %d\n", err);
        return;
    }
    
    Serial.println("[I2S] Microfone configurado!");
    Serial.printf("[I2S] SCK: GPIO%d | WS: GPIO%d | SD: GPIO%d\n", 
                  I2S_MIC_SCK, I2S_MIC_WS, I2S_MIC_SD);
    Serial.printf("[I2S] Sample Rate: %d Hz\n\n", SAMPLE_RATE);
}

// ============================================
// CONFIGURAÇÃO MQTT
// ============================================
void setupMQTT() {
    Serial.print("[MQTT] Configurando broker: ");
    Serial.print(MQTT_BROKER);
    Serial.print(":");
    Serial.println(MQTT_PORT);
    
    mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
    mqttClient.setBufferSize(16384);  // 16KB para áudio
    
    reconnectMQTT();
}

// ============================================
// RECONEXÃO MQTT
// ============================================
void reconnectMQTT() {
    int attempts = 0;
    
    while (!mqttClient.connected() && attempts < 5) {
        Serial.print("[MQTT] Conectando...");
        
        String clientId = "ESP32Test-";
        clientId += String(random(0xffff), HEX);
        
        if (mqttClient.connect(clientId.c_str())) {
            Serial.println(" OK!");
            
            // Publica status de online
            String status = "{\"status\":\"online\",\"ip\":\"" + WiFi.localIP().toString() + "\"}";
            mqttClient.publish(TOPIC_STATUS, status.c_str());
            
            Serial.println("[MQTT] Conectado ao broker!\n");
        } else {
            Serial.print(" FALHA (rc=");
            Serial.print(mqttClient.state());
            Serial.println(")");
            delay(2000);
            attempts++;
        }
    }
    
    if (!mqttClient.connected()) {
        Serial.println("[MQTT] Não foi possível conectar. Verifique o broker.");
    }
}

// ============================================
// ENVIA MENSAGEM DE TESTE
// ============================================
void sendTestMessage() {
    if (!mqttClient.connected()) return;
    
    testCounter++;
    
    // Monta JSON de teste
    char msg[128];
    snprintf(msg, sizeof(msg), 
             "{\"test\":1,\"counter\":%d,\"uptime\":%lu,\"rssi\":%d}",
             testCounter, millis() / 1000, WiFi.RSSI());
    
    // Publica
    bool success = mqttClient.publish(TOPIC_TEST, msg);
    
    Serial.println("─────────────────────────────────────");
    Serial.printf("[TEST] Mensagem #%d enviada\n", testCounter);
    Serial.printf("[TEST] Payload: %s\n", msg);
    Serial.printf("[TEST] Status: %s\n", success ? "✓ OK" : "✗ FALHA");
    Serial.println("─────────────────────────────────────\n");
}

// ============================================
// CAPTURA E ENVIA ÁUDIO DO MICROFONE
// ============================================
void captureAndSendAudio() {
    if (!mqttClient.connected()) return;
    
    // Buffer para áudio
    uint8_t i2sData[I2S_READ_LEN];
    size_t bytesRead = 0;
    
    // Lê do microfone
    esp_err_t result = i2s_read(I2S_MIC_NUM, &i2sData, I2S_READ_LEN, &bytesRead, portMAX_DELAY);
    
    if (result == ESP_OK && bytesRead > 0) {
        // Calcula nível de áudio (RMS aproximado)
        int32_t sum = 0;
        int16_t* samples = (int16_t*)i2sData;
        int sampleCount = bytesRead / 2;
        
        for (int i = 0; i < sampleCount; i++) {
            sum += abs(samples[i]);
        }
        int avgLevel = sum / sampleCount;
        
        // Envia áudio via MQTT
        bool success = mqttClient.publish(TOPIC_AUDIO, i2sData, bytesRead);
        
        Serial.println("─────────────────────────────────────");
        Serial.printf("[MIC] Capturado: %d bytes\n", bytesRead);
        Serial.printf("[MIC] Nível médio: %d\n", avgLevel);
        Serial.printf("[MIC] MQTT: %s\n", success ? "✓ Enviado" : "✗ Falha");
        Serial.println("─────────────────────────────────────\n");
    } else {
        Serial.printf("[MIC] Erro ao ler: %d\n", result);
    }
}
