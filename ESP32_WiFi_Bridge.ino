/*
 * ESP32 WiFi KÖPRÜ - KÜMES OTOMASYON
 * ===================================
 * 
 * Arduino Mega ile PWA/PyQt6 arası WiFi iletişimi
 * 
 * Özellikler:
 * - WebSocket Server (Port 81)
 * - Arduino Serial iletişimi
 * - WiFi bağlantısı
 * - JSON veri aktarımı
 * 
 * Bağlantılar:
 * - ESP32 RX (Pin 16) ← Arduino TX1
 * - ESP32 TX (Pin 17) → Arduino RX1
 * - GND → GND
 * 
 * Kütüphaneler (Arduino IDE):
 * - WebSockets by Markus Sattler
 */

// ==================== KÜTÜPHANELER ====================
#include <WiFi.h>
#include <WebSocketsServer.h>

// ==================== WiFi AYARLARI ====================
const char* WIFI_SSID = "WIFI_ADIN";          // ← DEĞİŞTİR!
const char* WIFI_PASSWORD = "WIFI_SIFREN";    // ← DEĞİŞTİR!

// ==================== SUNUCU AYARLARI ====================
WebSocketsServer webSocket(81);  // WebSocket Port 81

// ==================== SERİAL AYARLARI ====================
#define BAUDRATE 115200
#define ARDUINO_SERIAL Serial  // ESP32'nin TX/RX pini

// ==================== SETUP ====================
void setup() {
  // Serial başlat
  Serial.begin(BAUDRATE);
  delay(1000);
  
  Serial.println("\n\n=================================");
  Serial.println("ESP32 WiFi KÖPRÜ BAŞLATILIYOR...");
  Serial.println("=================================\n");
  
  // WiFi bağlan
  wifiBaglan();
  
  // WebSocket başlat
  webSocket.begin();
  webSocket.onEvent(webSocketEvent);
  
  Serial.println("\n=================================");
  Serial.println("ESP32 HAZIR!");
  Serial.print("IP Adresi: ");
  Serial.println(WiFi.localIP());
  Serial.print("WebSocket: ws://");
  Serial.print(WiFi.localIP());
  Serial.println(":81");
  Serial.println("=================================\n");
}

// ==================== LOOP ====================
void loop() {
  // WebSocket dinle
  webSocket.loop();
  
  // Arduino'dan veri oku
  if (ARDUINO_SERIAL.available()) {
    String data = ARDUINO_SERIAL.readStringUntil('\n');
    data.trim();
    
    if (data.startsWith("{")) {
      // JSON veri - Tüm clientlara gönder
      webSocket.broadcastTXT(data);
      Serial.println("Arduino → WebSocket:");
      Serial.println(data);
    }
    else if (data.startsWith("OK:") || data.startsWith("ERROR:")) {
      // Komut yanıtı
      webSocket.broadcastTXT(data);
      Serial.println("Arduino yanıt: " + data);
    }
  }
  
  delay(10);
}

// ==================== WiFi BAĞLANTI ====================
void wifiBaglan() {
  Serial.print("WiFi'ye bağlanıyor: ");
  Serial.println(WIFI_SSID);
  
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  
  int timeout = 0;
  while (WiFi.status() != WL_CONNECTED && timeout < 20) {
    delay(500);
    Serial.print(".");
    timeout++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✅ WiFi bağlandı!");
    Serial.print("IP Adresi: ");
    Serial.println(WiFi.localIP());
    Serial.print("Sinyal Gücü: ");
    Serial.print(WiFi.RSSI());
    Serial.println(" dBm");
  } else {
    Serial.println("\n❌ WiFi bağlanamadı!");
    Serial.println("Lütfen SSID ve Password'ü kontrol edin.");
  }
}

// ==================== WEBSOCKET EVENT ====================
void webSocketEvent(uint8_t num, WStype_t type, uint8_t * payload, size_t length) {
  switch (type) {
    case WStype_DISCONNECTED:
      Serial.printf("❌ [%u] Bağlantı kesildi\n", num);
      break;
    
    case WStype_CONNECTED: {
      IPAddress ip = webSocket.remoteIP(num);
      Serial.printf("✅ [%u] Bağlandı: %d.%d.%d.%d\n", 
                    num, ip[0], ip[1], ip[2], ip[3]);
      
      // İlk bağlantıda STATUS komutu gönder
      ARDUINO_SERIAL.println("STATUS");
      break;
    }
    
    case WStype_TEXT:
      Serial.printf("📥 [%u] Mesaj: %s\n", num, payload);
      
      // Komutu Arduino'ya ilet
      ARDUINO_SERIAL.println((char*)payload);
      break;
    
    case WStype_ERROR:
      Serial.printf("❌ [%u] Hata!\n", num);
      break;
  }
}

// ==================== SON ====================
