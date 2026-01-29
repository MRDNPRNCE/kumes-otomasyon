/*
 * ESP32 GELİŞMİŞ WiFi KÖPRÜ - KÜMES OTOMASYON
 * ============================================
 * 
 * Özellikler:
 * ✅ WiFi Manager (Dinamik WiFi değiştirme)
 * ✅ Access Control (Kullanıcı adı/şifre)
 * ✅ WebSocket Server
 * ✅ Web Panel
 * ✅ SPIFFS (Ayarlar kaydı)
 * 
 * İlk Kurulum:
 * 1. ESP32'yi aç
 * 2. "KumesAP" WiFi ağına bağlan
 * 3. Tarayıcıda: http://192.168.4.1
 * 4. WiFi ve şifre ayarla
 * 5. Admin kullanıcı oluştur
 * 
 * Kütüphaneler:
 * - WiFiManager by tzapu
 * - WebSockets by Markus Sattler
 * - ArduinoJson by Benoit Blanchon
 * - SPIFFS (built-in)
 */

// ==================== KÜTÜPHANELER ====================
#include <WiFi.h>
#include <WiFiManager.h>
#include <WebSocketsServer.h>
#include <WebServer.h>
#include <ArduinoJson.h>
#include <SPIFFS.h>
#include <Preferences.h>

// ==================== AYARLAR ====================
#define WEBSOCKET_PORT 81
#define WEB_PORT 80
#define BAUDRATE 115200

// Access Point ayarları (WiFi yoksa)
#define AP_SSID "KumesAP"
#define AP_PASSWORD "kumes1234"

// ==================== GLOBAL DEĞİŞKENLER ====================
WiFiManager wifiManager;
WebSocketsServer webSocket(WEBSOCKET_PORT);
WebServer server(WEB_PORT);
Preferences preferences;

// Kullanıcı bilgileri
struct User {
  String username;
  String password;
  String role;  // "admin" veya "user"
};

std::vector<User> users;
std::map<uint8_t, String> authenticatedClients; // WebSocket client ID → username

// ==================== SETUP ====================
void setup() {
  Serial.begin(BAUDRATE);
  delay(1000);
  
  Serial.println("\n\n=================================");
  Serial.println("ESP32 GELİŞMİŞ WiFi KÖPRÜ");
  Serial.println("=================================\n");
  
  // SPIFFS başlat
  if (!SPIFFS.begin(true)) {
    Serial.println("❌ SPIFFS başlatma hatası!");
    return;
  }
  Serial.println("✅ SPIFFS hazır");
  
  // Preferences başlat
  preferences.begin("kumes", false);
  
  // Kullanıcıları yükle
  loadUsers();
  
  // WiFi Manager başlat
  wifiManagerBaslat();
  
  // Web sunucu başlat
  webServerBaslat();
  
  // WebSocket başlat
  webSocket.begin();
  webSocket.onEvent(webSocketEvent);
  
  Serial.println("\n=================================");
  Serial.println("ESP32 HAZIR!");
  Serial.print("IP Adresi: ");
  Serial.println(WiFi.localIP());
  Serial.print("Web Panel: http://");
  Serial.println(WiFi.localIP());
  Serial.print("WebSocket: ws://");
  Serial.print(WiFi.localIP());
  Serial.print(":");
  Serial.println(WEBSOCKET_PORT);
  Serial.println("=================================\n");
}

// ==================== LOOP ====================
void loop() {
  server.handleClient();
  webSocket.loop();
  
  // Arduino'dan veri
  if (Serial.available()) {
    String data = Serial.readStringUntil('\n');
    data.trim();
    
    if (data.startsWith("{")) {
      // JSON veri - Sadece authenticated clientlara gönder
      for (auto& client : authenticatedClients) {
        webSocket.sendTXT(client.first, data);
      }
      Serial.println("Arduino → WebSocket:");
      Serial.println(data);
    }
  }
  
  delay(10);
}

// ==================== WiFi MANAGER ====================
void wifiManagerBaslat() {
  // Reset butonu (GPIO 0'a bas = WiFi sıfırla)
  pinMode(0, INPUT_PULLUP);
  
  // WiFi ayarlarını sıfırlama kontrolü
  if (digitalRead(0) == LOW) {
    Serial.println("⚠️ BOOT butonu basılı - WiFi sıfırlanıyor...");
    wifiManager.resetSettings();
    preferences.clear();
    delay(1000);
    ESP.restart();
  }
  
  // WiFi Manager callback
  wifiManager.setAPCallback([](WiFiManager *mgr) {
    Serial.println("\n=================================");
    Serial.println("📡 Access Point Modu");
    Serial.println("=================================");
    Serial.println("SSID: KumesAP");
    Serial.println("Şifre: kumes1234");
    Serial.println("IP: 192.168.4.1");
    Serial.println("Web Panel: http://192.168.4.1");
    Serial.println("=================================\n");
  });
  
  // Özel parametreler ekle
  WiFiManagerParameter custom_text("<p>Kümes Otomasyon Sistemi WiFi Ayarları</p>");
  wifiManager.addParameter(&custom_text);
  
  // WiFi'ye bağlan veya AP aç
  wifiManager.setConfigPortalTimeout(180); // 3 dakika timeout
  
  if (!wifiManager.autoConnect(AP_SSID, AP_PASSWORD)) {
    Serial.println("❌ WiFi bağlantı timeout!");
    delay(3000);
    ESP.restart();
  }
  
  Serial.println("✅ WiFi bağlandı!");
  Serial.print("IP Adresi: ");
  Serial.println(WiFi.localIP());
}

// ==================== KULLANICI YÖNETİMİ ====================
void loadUsers() {
  // SPIFFS'ten kullanıcıları yükle
  if (SPIFFS.exists("/users.json")) {
    File file = SPIFFS.open("/users.json", "r");
    if (file) {
      DynamicJsonDocument doc(2048);
      deserializeJson(doc, file);
      file.close();
      
      JsonArray usersArray = doc["users"];
      for (JsonObject userObj : usersArray) {
        User user;
        user.username = userObj["username"].as<String>();
        user.password = userObj["password"].as<String>();
        user.role = userObj["role"].as<String>();
        users.push_back(user);
      }
      
      Serial.printf("✅ %d kullanıcı yüklendi\n", users.size());
    }
  } else {
    // Varsayılan admin kullanıcı oluştur
    User admin;
    admin.username = "admin";
    admin.password = "admin123";
    admin.role = "admin";
    users.push_back(admin);
    
    User user;
    user.username = "user";
    user.password = "user123";
    user.role = "user";
    users.push_back(user);
    
    saveUsers();
    Serial.println("✅ Varsayılan kullanıcılar oluşturuldu");
    Serial.println("   admin / admin123 (Admin)");
    Serial.println("   user / user123 (User)");
  }
}

void saveUsers() {
  DynamicJsonDocument doc(2048);
  JsonArray usersArray = doc.createNestedArray("users");
  
  for (const User& user : users) {
    JsonObject userObj = usersArray.createNestedObject();
    userObj["username"] = user.username;
    userObj["password"] = user.password;
    userObj["role"] = user.role;
  }
  
  File file = SPIFFS.open("/users.json", "w");
  if (file) {
    serializeJson(doc, file);
    file.close();
    Serial.println("✅ Kullanıcılar kaydedildi");
  }
}

bool authenticateUser(String username, String password, String& role) {
  for (const User& user : users) {
    if (user.username == username && user.password == password) {
      role = user.role;
      return true;
    }
  }
  return false;
}

// ==================== WEB SUNUCU ====================
void webServerBaslat() {
  // Ana sayfa
  server.on("/", HTTP_GET, []() {
    String html = R"rawliteral(
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ESP32 Ayarlar</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 {
            color: #667eea;
            margin-bottom: 30px;
            text-align: center;
        }
        .card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .info-row {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #ddd;
        }
        .info-row:last-child { border-bottom: none; }
        .label { font-weight: bold; color: #555; }
        .value { color: #667eea; font-weight: bold; }
        button {
            width: 100%;
            padding: 15px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            margin-top: 10px;
        }
        button:hover { background: #5568d3; }
        button.danger { background: #f44336; }
        button.danger:hover { background: #da190b; }
        .status { 
            text-align: center; 
            padding: 10px;
            border-radius: 10px;
            margin-top: 10px;
        }
        .status.success { background: #d4edda; color: #155724; }
        .status.error { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🐔 ESP32 Ayarlar</h1>
        
        <div class="card">
            <h2 style="margin-bottom: 15px;">📡 WiFi Bilgileri</h2>
            <div class="info-row">
                <span class="label">SSID:</span>
                <span class="value" id="ssid">Yükleniyor...</span>
            </div>
            <div class="info-row">
                <span class="label">IP Adresi:</span>
                <span class="value" id="ip">Yükleniyor...</span>
            </div>
            <div class="info-row">
                <span class="label">Sinyal Gücü:</span>
                <span class="value" id="rssi">Yükleniyor...</span>
            </div>
        </div>
        
        <div class="card">
            <h2 style="margin-bottom: 15px;">👥 Kullanıcı Bilgileri</h2>
            <div class="info-row">
                <span class="label">Toplam Kullanıcı:</span>
                <span class="value" id="userCount">Yükleniyor...</span>
            </div>
            <div class="info-row">
                <span class="label">Bağlı Client:</span>
                <span class="value" id="clientCount">0</span>
            </div>
        </div>
        
        <div class="card">
            <h2 style="margin-bottom: 15px;">⚙️ İşlemler</h2>
            <button onclick="changeWiFi()">📡 WiFi Değiştir</button>
            <button onclick="location.href='/users'">👥 Kullanıcı Yönetimi</button>
            <button class="danger" onclick="resetWiFi()">🔄 WiFi Sıfırla</button>
        </div>
        
        <div id="status"></div>
    </div>
    
    <script>
        // Bilgileri yükle
        fetch('/api/info')
            .then(r => r.json())
            .then(data => {
                document.getElementById('ssid').textContent = data.ssid;
                document.getElementById('ip').textContent = data.ip;
                document.getElementById('rssi').textContent = data.rssi + ' dBm';
                document.getElementById('userCount').textContent = data.userCount;
            });
        
        function changeWiFi() {
            if (confirm('WiFi ayarlarını değiştirmek için ESP32 yeniden başlatılacak. Devam?')) {
                fetch('/api/change-wifi', {method: 'POST'})
                    .then(r => r.json())
                    .then(data => {
                        showStatus('ESP32 AP moduna geçiyor. "KumesAP" ağına bağlanın.', 'success');
                        setTimeout(() => location.reload(), 3000);
                    });
            }
        }
        
        function resetWiFi() {
            if (confirm('TÜM WiFi ayarları silinecek! Emin misiniz?')) {
                fetch('/api/reset-wifi', {method: 'POST'})
                    .then(r => r.json())
                    .then(data => {
                        showStatus('WiFi sıfırlandı. ESP32 yeniden başlatılıyor...', 'success');
                        setTimeout(() => location.reload(), 3000);
                    });
            }
        }
        
        function showStatus(msg, type) {
            const status = document.getElementById('status');
            status.className = 'status ' + type;
            status.textContent = msg;
        }
    </script>
</body>
</html>
    )rawliteral";
    
    server.send(200, "text/html", html);
  });
  
  // API: Sistem bilgisi
  server.on("/api/info", HTTP_GET, []() {
    DynamicJsonDocument doc(512);
    doc["ssid"] = WiFi.SSID();
    doc["ip"] = WiFi.localIP().toString();
    doc["rssi"] = WiFi.RSSI();
    doc["userCount"] = users.size();
    doc["clientCount"] = authenticatedClients.size();
    
    String response;
    serializeJson(doc, response);
    server.send(200, "application/json", response);
  });
  
  // API: WiFi değiştir
  server.on("/api/change-wifi", HTTP_POST, []() {
    server.send(200, "application/json", "{\"status\":\"ok\"}");
    delay(1000);
    wifiManager.resetSettings();
    ESP.restart();
  });
  
  // API: WiFi sıfırla
  server.on("/api/reset-wifi", HTTP_POST, []() {
    server.send(200, "application/json", "{\"status\":\"ok\"}");
    delay(1000);
    wifiManager.resetSettings();
    preferences.clear();
    ESP.restart();
  });
  
  // Kullanıcı yönetimi sayfası
  server.on("/users", HTTP_GET, handleUsersPage);
  server.on("/api/users", HTTP_GET, handleGetUsers);
  server.on("/api/users", HTTP_POST, handleAddUser);
  server.on("/api/users", HTTP_DELETE, handleDeleteUser);
  
  server.begin();
  Serial.println("✅ Web sunucu başlatıldı");
}

// ==================== KULLANICI YÖNETİMİ SAYFALARI ====================
void handleUsersPage() {
  String html = R"rawliteral(
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kullanıcı Yönetimi</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 30px;
        }
        h1 { color: #667eea; margin-bottom: 30px; }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 30px;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th { background: #667eea; color: white; }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        input, select {
            width: 100%;
            padding: 10px;
            border: 2px solid #ddd;
            border-radius: 5px;
        }
        button {
            padding: 10px 20px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            margin-right: 10px;
        }
        button:hover { background: #5568d3; }
        button.delete { background: #f44336; }
        button.delete:hover { background: #da190b; }
    </style>
</head>
<body>
    <div class="container">
        <h1>👥 Kullanıcı Yönetimi</h1>
        
        <h2>Mevcut Kullanıcılar</h2>
        <table id="usersTable">
            <thead>
                <tr>
                    <th>Kullanıcı Adı</th>
                    <th>Rol</th>
                    <th>İşlem</th>
                </tr>
            </thead>
            <tbody id="usersBody">
            </tbody>
        </table>
        
        <h2>Yeni Kullanıcı Ekle</h2>
        <div class="form-group">
            <label>Kullanıcı Adı:</label>
            <input type="text" id="username" placeholder="kullanici">
        </div>
        <div class="form-group">
            <label>Şifre:</label>
            <input type="password" id="password" placeholder="********">
        </div>
        <div class="form-group">
            <label>Rol:</label>
            <select id="role">
                <option value="user">User</option>
                <option value="admin">Admin</option>
            </select>
        </div>
        <button onclick="addUser()">➕ Kullanıcı Ekle</button>
        <button onclick="location.href='/'">🏠 Ana Sayfa</button>
    </div>
    
    <script>
        loadUsers();
        
        function loadUsers() {
            fetch('/api/users')
                .then(r => r.json())
                .then(data => {
                    const tbody = document.getElementById('usersBody');
                    tbody.innerHTML = '';
                    data.users.forEach(user => {
                        tbody.innerHTML += `
                            <tr>
                                <td>${user.username}</td>
                                <td>${user.role}</td>
                                <td>
                                    <button class="delete" onclick="deleteUser('${user.username}')">🗑️ Sil</button>
                                </td>
                            </tr>
                        `;
                    });
                });
        }
        
        function addUser() {
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const role = document.getElementById('role').value;
            
            if (!username || !password) {
                alert('Kullanıcı adı ve şifre gerekli!');
                return;
            }
            
            fetch('/api/users', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({username, password, role})
            })
            .then(r => r.json())
            .then(data => {
                alert('Kullanıcı eklendi!');
                loadUsers();
                document.getElementById('username').value = '';
                document.getElementById('password').value = '';
            });
        }
        
        function deleteUser(username) {
            if (confirm(`${username} kullanıcısını silmek istediğinize emin misiniz?`)) {
                fetch(`/api/users?username=${username}`, {method: 'DELETE'})
                    .then(r => r.json())
                    .then(data => {
                        alert('Kullanıcı silindi!');
                        loadUsers();
                    });
            }
        }
    </script>
</body>
</html>
  )rawliteral";
  
  server.send(200, "text/html", html);
}

void handleGetUsers() {
  DynamicJsonDocument doc(2048);
  JsonArray usersArray = doc.createNestedArray("users");
  
  for (const User& user : users) {
    JsonObject userObj = usersArray.createNestedObject();
    userObj["username"] = user.username;
    userObj["role"] = user.role;
    // Şifre gönderme!
  }
  
  String response;
  serializeJson(doc, response);
  server.send(200, "application/json", response);
}

void handleAddUser() {
  DynamicJsonDocument doc(512);
  deserializeJson(doc, server.arg("plain"));
  
  User newUser;
  newUser.username = doc["username"].as<String>();
  newUser.password = doc["password"].as<String>();
  newUser.role = doc["role"].as<String>();
  
  users.push_back(newUser);
  saveUsers();
  
  server.send(200, "application/json", "{\"status\":\"ok\"}");
}

void handleDeleteUser() {
  String username = server.arg("username");
  
  users.erase(
    std::remove_if(users.begin(), users.end(),
      [&username](const User& u) { return u.username == username; }),
    users.end()
  );
  
  saveUsers();
  server.send(200, "application/json", "{\"status\":\"ok\"}");
}

// ==================== WEBSOCKET ====================
void webSocketEvent(uint8_t num, WStype_t type, uint8_t * payload, size_t length) {
  switch (type) {
    case WStype_DISCONNECTED:
      Serial.printf("❌ [%u] Bağlantı kesildi\n", num);
      authenticatedClients.erase(num);
      break;
    
    case WStype_CONNECTED: {
      IPAddress ip = webSocket.remoteIP(num);
      Serial.printf("🔌 [%u] Bağlandı: %d.%d.%d.%d (Auth bekleniyor)\n", 
                    num, ip[0], ip[1], ip[2], ip[3]);
      
      // Auth istemi gönder
      DynamicJsonDocument doc(256);
      doc["type"] = "auth_required";
      doc["message"] = "Lütfen giriş yapın";
      
      String response;
      serializeJson(doc, response);
      webSocket.sendTXT(num, response);
      break;
    }
    
    case WStype_TEXT: {
      Serial.printf("📥 [%u] Mesaj: %s\n", num, payload);
      
      // JSON parse et
      DynamicJsonDocument doc(512);
      DeserializationError error = deserializeJson(doc, payload);
      
      if (!error) {
        String type = doc["type"];
        
        // AUTH mesajı
        if (type == "auth") {
          String username = doc["username"];
          String password = doc["password"];
          String role;
          
          if (authenticateUser(username, password, role)) {
            authenticatedClients[num] = username;
            
            // Başarılı auth yanıtı
            DynamicJsonDocument response(256);
            response["type"] = "auth_success";
            response["username"] = username;
            response["role"] = role;
            
            String responseStr;
            serializeJson(response, responseStr);
            webSocket.sendTXT(num, responseStr);
            
            Serial.printf("✅ [%u] Auth başarılı: %s (%s)\n", 
                          num, username.c_str(), role.c_str());
            
            // İlk veri gönder
            Serial.println("STATUS");
          } else {
            // Başarısız auth
            DynamicJsonDocument response(256);
            response["type"] = "auth_failed";
            response["message"] = "Kullanıcı adı veya şifre hatalı";
            
            String responseStr;
            serializeJson(response, responseStr);
            webSocket.sendTXT(num, responseStr);
            
            Serial.printf("❌ [%u] Auth başarısız: %s\n", num, username.c_str());
          }
        }
        // Diğer mesajlar (auth gerekli)
        else if (authenticatedClients.find(num) != authenticatedClients.end()) {
          String command = doc["command"];
          
          // Komutu Arduino'ya ilet
          Serial.println(command);
        } else {
          // Auth yok - reddet
          DynamicJsonDocument response(256);
          response["type"] = "error";
          response["message"] = "Önce giriş yapmalısınız";
          
          String responseStr;
          serializeJson(response, responseStr);
          webSocket.sendTXT(num, responseStr);
        }
      }
      break;
    }
  }
}

// ==================== SON ====================
