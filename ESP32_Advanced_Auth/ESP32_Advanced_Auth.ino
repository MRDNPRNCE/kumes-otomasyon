/*
 * ESP32 ADVANCED AUTH SYSTEM
 * ==========================
 * ✅ Session yönetimi
 * ✅ Admin mod kontrolü (active/watching)
 * ✅ Dinamik yetki yönetimi
 * ✅ Multi-client support
 * ✅ Broadcast notifications
 * ✅ WiFi bağlantı iyileştirmeleri
 */

#include <WiFi.h>
#include <WebSocketsServer.h>
#include <ArduinoJson.h>
#include <vector>

// ==================== WIFI AYARLARI ====================
const char* WIFI_SSID = "Taze Kenar";
const char* WIFI_PASSWORD = "Tehnoimpuls";

// ==================== WEBSOCKET SUNUCU ====================
WebSocketsServer webSocket = WebSocketsServer(81);

// ==================== KULLANICI TANIMI ====================
struct User {
  String username;
  String password;
  String role;  // "admin" veya "user"
};

User users[] = {
  {"admin", "admin123", "admin"},
  {"user", "user123", "user"},
  {"test", "test", "user"}
};

const int USER_COUNT = 3;

// ==================== SESSION TANIMI ====================
struct Session {
  uint8_t clientNum;
  String sessionId;
  String username;
  String role;
  String adminMode;      // "active" veya "watching" (sadece admin için)
  String clientType;     // "pwa" veya "desktop"
  bool canControl;       // Dinamik: Kontrol edebilir mi?
  unsigned long lastActivity;
};

std::vector<Session> activeSessions;
String currentAdminSessionId = "";

// ==================== ARDUINO SERİAL ====================
#define RXD2 16
#define TXD2 17

// ==================== SETUP ====================
void setup() {
  Serial.begin(115200);
  delay(1000);  // Stabilizasyon için bekle
  
  Serial.println("\n\n====================================");
  Serial.println("ESP32 KÜMES OTOMASYON BAŞLATILIYOR");
  Serial.println("====================================");
  
  // GPIO ayarlarını temizle (boot sorunlarını önle)
  pinMode(0, INPUT);
  pinMode(2, INPUT);
  
  // Serial2 başlat (Arduino iletişimi)
  Serial2.begin(115200, SERIAL_8N1, RXD2, TXD2);
  Serial.println("✅ Serial2 başlatıldı (Arduino bağlantısı)");
  
  // WiFi modunu ayarla
  WiFi.mode(WIFI_STA);
  WiFi.disconnect();
  delay(100);
  
  // Power save kapat (bağlantı stabilitesi için)
  WiFi.setSleep(false);
  
  // WiFi bağlantısı
  Serial.println("\n--- WiFi Bağlantısı ---");
  Serial.print("📡 SSID: ");
  Serial.println(WIFI_SSID);
  Serial.print("🔑 Şifre uzunluğu: ");
  Serial.println(strlen(WIFI_PASSWORD));
  Serial.print("📱 MAC Adresi: ");
  Serial.println(WiFi.macAddress());
  
  Serial.println("🔌 Bağlanıyor...");
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  
  int timeout = 0;
  while (WiFi.status() != WL_CONNECTED && timeout < 40) {  // 20 saniye timeout
    delay(500);
    Serial.print(".");
    timeout++;
    
    // Her 5 saniyede durum göster
    if (timeout % 10 == 0 && timeout > 0) {
      Serial.println();
      Serial.print("⏱️ ");
      Serial.print(timeout / 2);
      Serial.print(" saniye... Durum: ");
      Serial.println(WiFi.status());
    }
  }
  
  Serial.println();
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("✅ WiFi bağlandı!");
    Serial.print("📡 IP Adresi: ");
    Serial.println(WiFi.localIP());
    Serial.print("📡 Gateway: ");
    Serial.println(WiFi.gatewayIP());
    Serial.print("📊 Sinyal Gücü: ");
    Serial.print(WiFi.RSSI());
    Serial.println(" dBm");
    
    // WebSocket başlat
    webSocket.begin();
    webSocket.onEvent(webSocketEvent);
    
    Serial.println("🔌 WebSocket başlatıldı (Port 81)");
    Serial.println("🔐 Auth sistemi hazır!");
    Serial.println("====================================");
    Serial.println();
  } else {
    Serial.println("❌ WiFi bağlanamadı!");
    Serial.print("❌ Son Durum Kodu: ");
    Serial.println(WiFi.status());
    
    // Hata analizi
    Serial.println("\n--- Hata Analizi ---");
    switch (WiFi.status()) {
      case WL_NO_SSID_AVAIL:
        Serial.println("🔴 SSID BULUNAMADI!");
        Serial.println("   1. SSID doğru yazıldı mı?");
        Serial.println("   2. 2.4GHz WiFi mi? (5GHz çalışmaz!)");
        Serial.println("   3. Router açık mı?");
        Serial.println("   4. Router'a yakın mı?");
        break;
        
      case WL_CONNECT_FAILED:
        Serial.println("🔴 BAĞLANTI BAŞARISIZ!");
        Serial.println("   1. Şifre doğru mu?");
        Serial.println("   2. Büyük/küçük harf kontrol et");
        break;
        
      default:
        Serial.println("🔴 BİLİNMEYEN HATA!");
        Serial.println("   1. Router'ı yeniden başlat");
        Serial.println("   2. ESP32'yi yeniden başlat (EN butonu)");
    }
    
    // Ağ taraması yap
    Serial.println("\n--- Mevcut WiFi Ağları ---");
    int n = WiFi.scanNetworks();
    if (n == 0) {
      Serial.println("❌ Hiç ağ bulunamadı!");
      Serial.println("   - ESP32 anten sorunu olabilir");
      Serial.println("   - Router çok uzakta olabilir");
    } else {
      Serial.print("✅ ");
      Serial.print(n);
      Serial.println(" ağ bulundu:");
      
      for (int i = 0; i < n; i++) {
        Serial.print("  ");
        Serial.print(i + 1);
        Serial.print(". ");
        Serial.print(WiFi.SSID(i));
        Serial.print(" (");
        Serial.print(WiFi.RSSI(i));
        Serial.print(" dBm) ");
        Serial.println(WiFi.encryptionType(i) == WIFI_AUTH_OPEN ? "🔓" : "🔒");
        
        // Aranan SSID bulundu mu?
        if (WiFi.SSID(i) == WIFI_SSID) {
          Serial.println("     ✅ ARANAN SSID BULUNDU!");
          Serial.println("     ⚠️ Şifre yanlış olabilir!");
        }
      }
    }
    
    Serial.println("====================================");
    Serial.println("❌ SISTEM BAŞLATILAMADI!");
    Serial.println("Lütfen WiFi ayarlarını kontrol edin.");
    Serial.println("====================================");
    
    // Sonsuz döngüde bekle (restart gerekli)
    while(1) {
      delay(1000);
    }
  }
}

// ==================== LOOP ====================
void loop() {
  // WiFi bağlantı kontrolü
  static unsigned long lastWiFiCheck = 0;
  if (millis() - lastWiFiCheck > 10000) {  // Her 10 saniyede bir kontrol
    if (WiFi.status() != WL_CONNECTED) {
      Serial.println("⚠️ WiFi bağlantısı kesildi! Yeniden bağlanıyor...");
      WiFi.reconnect();
    }
    lastWiFiCheck = millis();
  }
  
  webSocket.loop();
  
  // Arduino'dan veri geldi mi?
  if (Serial2.available()) {
    String data = Serial2.readStringUntil('\n');
    data.trim();
    
    if (data.length() > 0) {
      Serial.print("📥 Arduino veri: ");
      Serial.println(data);
      
      // Tüm clientlara gönder
      broadcastToAll(data);
    }
  }
  
  // Session timeout kontrolü (5 dakika)
  static unsigned long lastCheck = 0;
  if (millis() - lastCheck > 60000) {  // Her dakika kontrol
    checkSessionTimeouts();
    lastCheck = millis();
  }
  
  // Heartbeat (her 30 saniye)
  static unsigned long lastHeartbeat = 0;
  if (millis() - lastHeartbeat > 30000) {
    Serial.print("❤️ Sistem çalışıyor... ");
    Serial.print("Aktif client: ");
    Serial.print(activeSessions.size());
    Serial.print(", Heap: ");
    Serial.print(ESP.getFreeHeap());
    Serial.println(" bytes");
    lastHeartbeat = millis();
  }
}

// ==================== WEBSOCKET EVENT ====================
void webSocketEvent(uint8_t num, WStype_t type, uint8_t * payload, size_t length) {
  switch(type) {
    case WStype_DISCONNECTED:
      handleDisconnect(num);
      break;
      
    case WStype_CONNECTED:
      handleConnect(num);
      break;
      
    case WStype_TEXT:
      handleMessage(num, (char*)payload);
      break;
  }
}

// ==================== BAĞLANTI YÖNETİMİ ====================
void handleConnect(uint8_t num) {
  Serial.printf("🔌 Yeni bağlantı: Client #%d\n", num);
  
  // Auth gerekli mesajı gönder
  StaticJsonDocument<200> doc;
  doc["type"] = "auth_required";
  doc["message"] = "Lütfen giriş yapın";
  
  String output;
  serializeJson(doc, output);
  webSocket.sendTXT(num, output);
}

void handleDisconnect(uint8_t num) {
  Serial.printf("⚠️ Bağlantı kesildi: Client #%d\n", num);
  
  // Session'ı bul ve sil
  for (auto it = activeSessions.begin(); it != activeSessions.end(); ++it) {
    if (it->clientNum == num) {
      String username = it->username;
      String role = it->role;
      
      Serial.printf("👋 %s (%s) ayrıldı\n", username.c_str(), role.c_str());
      
      // Admin ayrıldıysa
      if (role == "admin" && it->sessionId == currentAdminSessionId) {
        currentAdminSessionId = "";
        
        // Tüm user'lara kontrol verildi bildirimi
        notifyAdminLeft();
      }
      
      activeSessions.erase(it);
      updateControlPermissions();
      break;
    }
  }
}

// ==================== MESAJ İŞLEME ====================
void handleMessage(uint8_t num, char* payload) {
  StaticJsonDocument<512> doc;
  DeserializationError error = deserializeJson(doc, payload);
  
  if (error) {
    Serial.println("❌ JSON parse hatası!");
    return;
  }
  
  String type = doc["type"];
  
  // AUTH
  if (type == "auth") {
    handleAuth(num, doc);
  }
  // MOD DEĞİŞTİRME (sadece admin)
  else if (type == "change_mode") {
    handleModeChange(num, doc);
  }
  // KOMUT
  else if (type == "command") {
    handleCommand(num, doc);
  }
}

// ==================== AUTH İŞLEME ====================
void handleAuth(uint8_t num, JsonDocument& doc) {
  String username = doc["username"];
  String password = doc["password"];
  String clientType = doc["client_type"] | "unknown";
  
  Serial.printf("🔑 Login denemesi: %s (%s)\n", username.c_str(), clientType.c_str());
  
  // Kullanıcı kontrolü
  User* user = findUser(username, password);
  
  if (!user) {
    // Hatalı giriş
    StaticJsonDocument<200> response;
    response["type"] = "auth_failed";
    response["message"] = "Kullanıcı adı veya şifre hatalı";
    
    String output;
    serializeJson(response, output);
    webSocket.sendTXT(num, output);
    
    Serial.println("❌ Giriş başarısız!");
    return;
  }
  
  // Session oluştur
  Session session;
  session.clientNum = num;
  session.sessionId = generateSessionId();
  session.username = username;
  session.role = user->role;
  session.clientType = clientType;
  session.lastActivity = millis();
  session.canControl = true;  // Başlangıçta true
  
  if (user->role == "admin") {
    // Admin girişi
    session.adminMode = "active";
    
    // Önceki admin varsa override
    if (currentAdminSessionId != "") {
      notifyAdminOverride(currentAdminSessionId, clientType);
    }
    
    currentAdminSessionId = session.sessionId;
  } else {
    // User girişi
    session.adminMode = "";
  }
  
  activeSessions.push_back(session);
  
  // Yetkileri güncelle
  updateControlPermissions();
  
  // Başarılı yanıt
  StaticJsonDocument<300> response;
  response["type"] = "auth_success";
  response["username"] = username;
  response["role"] = user->role;
  response["session_id"] = session.sessionId;
  
  JsonObject perms = response.createNestedObject("permissions");
  perms["can_control"] = session.canControl;
  perms["can_change_settings"] = (user->role == "admin");
  perms["can_view"] = true;
  
  if (user->role == "admin") {
    response["admin_mode"] = session.adminMode;
  }
  
  String output;
  serializeJson(response, output);
  webSocket.sendTXT(num, output);
  
  Serial.printf("✅ %s (%s) giriş yaptı - Kontrol: %s\n", 
    username.c_str(), 
    user->role.c_str(),
    session.canControl ? "✅" : "❌"
  );
  
  // Diğer clientlara bildir
  notifyUserJoined(session);
}

// ==================== MOD DEĞİŞTİRME ====================
void handleModeChange(uint8_t num, JsonDocument& doc) {
  String sessionId = doc["session_id"];
  String newMode = doc["mode"];  // "active" veya "watching"
  
  // Session bul
  Session* session = findSessionByClient(num);
  if (!session) {
    sendError(num, "Oturum bulunamadı");
    return;
  }
  
  // Sadece admin mod değiştirebilir
  if (session->role != "admin") {
    sendError(num, "Sadece admin mod değiştirebilir");
    return;
  }
  
  // Mod değiştir
  String oldMode = session->adminMode;
  session->adminMode = newMode;
  
  Serial.printf("🔄 Admin modu: %s → %s\n", oldMode.c_str(), newMode.c_str());
  
  // Yetkileri güncelle
  updateControlPermissions();
  
  // Admin'e onay gönder
  StaticJsonDocument<200> response;
  response["type"] = "mode_changed";
  response["mode"] = newMode;
  
  String output;
  serializeJson(response, output);
  webSocket.sendTXT(num, output);
  
  // Tüm user'lara bildir
  if (newMode == "watching") {
    notifyControlAvailable();
  } else {
    notifyControlRevoked();
  }
}

// ==================== KOMUT İŞLEME ====================
void handleCommand(uint8_t num, JsonDocument& doc) {
  String sessionId = doc["session_id"];
  String command = doc["command"];
  
  // Session bul
  Session* session = findSessionByClient(num);
  if (!session) {
    sendError(num, "Oturum bulunamadı");
    return;
  }
  
  // Yetki kontrolü
  if (!session->canControl) {
    StaticJsonDocument<200> response;
    response["type"] = "permission_denied";
    response["message"] = "Bu işlem için kontrol yetkisi gerekli";
    
    if (currentAdminSessionId != "") {
      Session* admin = findSessionById(currentAdminSessionId);
      if (admin) {
        response["admin_username"] = admin->username;
        response["admin_mode"] = admin->adminMode;
      }
    }
    
    String output;
    serializeJson(response, output);
    webSocket.sendTXT(num, output);
    
    Serial.printf("❌ Komut reddedildi: %s (Yetki yok)\n", session->username.c_str());
    return;
  }
  
  // Ayar komutları sadece admin
  if (command.startsWith("AYAR") && session->role != "admin") {
    sendError(num, "Ayar değiştirmek için admin yetkisi gerekli");
    return;
  }
  
  // Komutu Arduino'ya gönder
  Serial2.println(command);
  Serial.printf("📤 Komut gönderildi: %s (by %s)\n", command.c_str(), session->username.c_str());
  
  // Session aktivitesini güncelle
  session->lastActivity = millis();
  
  // Onay gönder
  StaticJsonDocument<200> response;
  response["type"] = "command_sent";
  response["command"] = command;
  
  String output;
  serializeJson(response, output);
  webSocket.sendTXT(num, output);
}

// ==================== YETKİ YÖNETİMİ ====================
void updateControlPermissions() {
  bool adminActive = false;
  
  // Admin aktif mi kontrol et
  if (currentAdminSessionId != "") {
    Session* admin = findSessionById(currentAdminSessionId);
    if (admin) {
      adminActive = (admin->adminMode == "active");
    }
  }
  
  // Tüm session'ları güncelle
  for (Session& s : activeSessions) {
    if (s.role == "admin") {
      // Admin: Sadece active modda kontrol edebilir
      s.canControl = (s.adminMode == "active");
    } else {
      // User: Admin aktif değilse kontrol edebilir
      s.canControl = !adminActive;
    }
  }
  
  Serial.println("📊 Yetkiler güncellendi:");
  for (Session& s : activeSessions) {
    Serial.printf("  - %s (%s): Kontrol=%s\n", 
      s.username.c_str(), 
      s.role.c_str(),
      s.canControl ? "✅" : "❌"
    );
  }
}

// ==================== BİLDİRİMLER ====================
void notifyAdminOverride(String oldAdminSessionId, String newClientType) {
  Session* oldAdmin = findSessionById(oldAdminSessionId);
  if (!oldAdmin) return;
  
  StaticJsonDocument<300> msg;
  msg["type"] = "admin_override";
  msg["message"] = "Başka bir cihazdan admin girişi yapıldı";
  msg["new_admin_client"] = newClientType;
  
  String output;
  serializeJson(msg, output);
  webSocket.sendTXT(oldAdmin->clientNum, output);
  
  Serial.printf("⚠️ Admin override: %s\n", oldAdmin->username.c_str());
}

void notifyControlAvailable() {
  StaticJsonDocument<200> msg;
  msg["type"] = "control_available";
  msg["message"] = "Admin izleme moduna geçti. Artık kontrol edebilirsiniz!";
  msg["admin_mode"] = "watching";
  
  String output;
  serializeJson(msg, output);
  
  // Sadece user'lara gönder
  for (Session& s : activeSessions) {
    if (s.role == "user") {
      webSocket.sendTXT(s.clientNum, output);
    }
  }
  
  Serial.println("📢 User'lara: Kontrol edebilirsiniz!");
}

void notifyControlRevoked() {
  StaticJsonDocument<200> msg;
  msg["type"] = "control_revoked";
  msg["message"] = "Admin kontrolü aldı. Sadece izleyebilirsiniz.";
  msg["admin_mode"] = "active";
  
  String output;
  serializeJson(msg, output);
  
  // Sadece user'lara gönder
  for (Session& s : activeSessions) {
    if (s.role == "user") {
      webSocket.sendTXT(s.clientNum, output);
    }
  }
  
  Serial.println("📢 User'lara: Kontrol kaldırıldı!");
}

void notifyAdminLeft() {
  StaticJsonDocument<200> msg;
  msg["type"] = "admin_left";
  msg["message"] = "Admin ayrıldı. Artık kontrol edebilirsiniz!";
  
  String output;
  serializeJson(msg, output);
  
  // Sadece user'lara gönder
  for (Session& s : activeSessions) {
    if (s.role == "user") {
      webSocket.sendTXT(s.clientNum, output);
    }
  }
  
  Serial.println("📢 User'lara: Admin ayrıldı!");
}

void notifyUserJoined(Session& session) {
  StaticJsonDocument<200> msg;
  msg["type"] = "user_joined";
  msg["username"] = session.username;
  msg["role"] = session.role;
  msg["client_type"] = session.clientType;
  
  String output;
  serializeJson(msg, output);
  
  // Diğer clientlara gönder
  for (Session& s : activeSessions) {
    if (s.sessionId != session.sessionId) {
      webSocket.sendTXT(s.clientNum, output);
    }
  }
}

// ==================== YARDIMCI FONKSİYONLAR ====================
User* findUser(String username, String password) {
  for (int i = 0; i < USER_COUNT; i++) {
    if (users[i].username == username && users[i].password == password) {
      return &users[i];
    }
  }
  return nullptr;
}

Session* findSessionByClient(uint8_t num) {
  for (Session& s : activeSessions) {
    if (s.clientNum == num) {
      return &s;
    }
  }
  return nullptr;
}

Session* findSessionById(String sessionId) {
  for (Session& s : activeSessions) {
    if (s.sessionId == sessionId) {
      return &s;
    }
  }
  return nullptr;
}

String generateSessionId() {
  String id = "sess_";
  for (int i = 0; i < 8; i++) {
    id += String(random(0, 16), HEX);
  }
  return id;
}

void sendError(uint8_t num, String message) {
  StaticJsonDocument<200> response;
  response["type"] = "error";
  response["message"] = message;
  
  String output;
  serializeJson(response, output);
  webSocket.sendTXT(num, output);
}

void broadcastToAll(String message) {
  for (Session& s : activeSessions) {
    webSocket.sendTXT(s.clientNum, message);
  }
}

void checkSessionTimeouts() {
  unsigned long now = millis();
  
  for (auto it = activeSessions.begin(); it != activeSessions.end();) {
    if (now - it->lastActivity > 300000) {  // 5 dakika
      Serial.printf("⏰ Session timeout: %s\n", it->username.c_str());
      
      uint8_t clientNum = it->clientNum;
      it = activeSessions.erase(it);
      
      webSocket.disconnect(clientNum);
    } else {
      ++it;
    }
  }
}

void printSessionInfo() {
  Serial.println("\n========== AKTİF SESSION'LAR ==========");
  Serial.printf("Toplam: %d\n", activeSessions.size());
  
  for (Session& s : activeSessions) {
    Serial.printf("\n👤 %s (%s)\n", s.username.c_str(), s.role.c_str());
    Serial.printf("   Client: #%d (%s)\n", s.clientNum, s.clientType.c_str());
    Serial.printf("   Session: %s\n", s.sessionId.c_str());
    Serial.printf("   Kontrol: %s\n", s.canControl ? "✅" : "❌");
    if (s.role == "admin") {
      Serial.printf("   Mod: %s\n", s.adminMode.c_str());
    }
  }
  
  Serial.println("========================================\n");
}
