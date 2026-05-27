/**
 * Arquivo de Configuração - ESP32 Audio Player
 * 
 * Edite este arquivo com suas credenciais WiFi e configurações MQTT
 */

#ifndef CONFIG_H
#define CONFIG_H

// ============================================
// CONFIGURAÇÕES WIFI
// ============================================
#define WIFI_SSID       "INTERNET."
#define WIFI_PASSWORD   "" //   Você não veio aqui para roubar minha senha, né? Deixe em branco ou coloque a senha da sua rede WiFi.

// ============================================
// CONFIGURAÇÕES MQTT
// ============================================
// Endereço do broker MQTT (IP local ou hostname)
#define MQTT_BROKER     "192.168.1.13"
#define MQTT_PORT       1883

// Tópicos MQTT
// O Python/Ralu vai publicar áudio neste tópico
#define MQTT_TOPIC_AUDIO    "ralu/audio/stream"

// Tópico para comandos de controle (stop, status, etc)
#define MQTT_TOPIC_CONTROL  "ralu/audio/control"

// Tópico onde ESP32 publica seu status
#define MQTT_TOPIC_STATUS   "ralu/audio/status"

// Tópico onde ESP32 publica áudio do microfone
#define MQTT_TOPIC_MIC      "ralu/mic/audio"

// ============================================
// CONFIGURAÇÕES OPCIONAIS
// ============================================

// Descomente para habilitar debug detalhado
// #define DEBUG_AUDIO

// Volume inicial (0.0 a 1.0) - ajuste de software
#define INITIAL_VOLUME  1.0

#endif // CONFIG_H
