/*
 * KÜMES OTOMASYON SİSTEMİ - ARDUINO MEGA 2560
 * ============================================
 * 
 * Özellikler:
 * - 3 Kümes desteği
 * - DHT22 sensörler (sıcaklık/nem)
 * - Otomatik kontrol (fan, ısıtıcı, LED)
 * - Alarm sistemi
 * - ESP32 ile iletişim (JSON)
 * - Manuel kontrol (komutlar)
 * 
 * Bağlantılar:
 * - Arduino TX1 → ESP32 RX (Pin 16)
 * - Arduino RX1 → ESP32 TX (Pin 17)
 * - GND → GND
 */

// ==================== KÜTÜPHANELER ====================
#include <DHT.h>
#include <Servo.h>

// ==================== YAPILANDIRMA ====================
#define MAX_KUMES 3                  // Kümes sayısı
#define BAUDRATE 115200              // Seri port hızı
#define VERI_GONDERME_ARALIK 5000    // 5 saniye
#define KONTROL_ARALIK 2000          // 2 saniye

// Eşik Değerleri
#define SICAKLIK_MIN 18.0
#define SICAKLIK_MAX 28.0
#define NEM_MIN 40.0
#define NEM_MAX 70.0
#define SU_SEVIYE_MIN 200

// ==================== PIN TANIMLARI ====================

// DHT22 Sensör Pinleri
const int DHT_PINS[MAX_KUMES] = {2, 3, 4};
#define DHTTYPE DHT22

// Analog Sensörler
#define SU_SENSOR_1 A0
#define SU_SENSOR_2 A1
#define LDR_1 A2
#define LDR_2 A3

// Röle Pinleri (LOW = AÇIK, HIGH = KAPALI)
#define ROLE_FAN_1 22
#define ROLE_FAN_2 23
#define ROLE_ISITICI 24
#define ROLE_POMPA 25
#define ROLE_YEM_MOTOR 26
#define ROLE_LED_1 27
#define ROLE_LED_2 28
#define ROLE_LED_3 29

// Servo Motor
#define SERVO_KAPI_PIN 9

// ESP32 İletişim
#define ESP32_SERIAL Serial1

// ==================== YAPILAR ====================
struct KumesData {
  int id;
  float sicaklik;
  float nem;
  int suSeviyesi;
  int isikSeviyesi;
  bool fanDurumu;
  bool ledDurumu;
  bool alarm;
  String alarmMesaj;
};

struct SistemData {
  int yemSeviyesi;
  bool pompaDurumu;
  unsigned long calismaSuresi;
};

// ==================== GLOBAL DEĞİŞKENLER ====================
DHT dhtSensors[MAX_KUMES] = {
  DHT(DHT_PINS[0], DHTTYPE),
  DHT(DHT_PINS[1], DHTTYPE),
  DHT(DHT_PINS[2], DHTTYPE)
};

Servo servoKapi;

KumesData kumesler[MAX_KUMES];
SistemData sistem;

unsigned long oncekiVeriZaman = 0;
unsigned long oncekiKontrolZaman = 0;
unsigned long baslangicZaman = 0;

bool otomatikMod = true;

// ==================== SETUP ====================
void setup() {
  // Seri portlar
  Serial.begin(BAUDRATE);
  ESP32_SERIAL.begin(BAUDRATE);
  
  Serial.println("=================================");
  Serial.println("KÜMES OTOMASYON BAŞLATILIYOR...");
  Serial.println("=================================");
  
  // DHT sensörler
  for (int i = 0; i < MAX_KUMES; i++) {
    dhtSensors[i].begin();
    kumesler[i].id = i + 1;
    kumesler[i].alarm = false;
    kumesler[i].alarmMesaj = "";
    Serial.print("Kümes #");
    Serial.print(i + 1);
    Serial.println(" DHT22 hazır");
  }
  
  // Analog pinler
  pinMode(SU_SENSOR_1, INPUT);
  pinMode(SU_SENSOR_2, INPUT);
  pinMode(LDR_1, INPUT);
  pinMode(LDR_2, INPUT);
  
  // Röle pinleri (Başlangıçta KAPALI)
  const int rolePinleri[] = {
    ROLE_FAN_1, ROLE_FAN_2, ROLE_ISITICI, ROLE_POMPA,
    ROLE_YEM_MOTOR, ROLE_LED_1, ROLE_LED_2, ROLE_LED_3
  };
  
  for (int i = 0; i < 8; i++) {
    pinMode(rolePinleri[i], OUTPUT);
    digitalWrite(rolePinleri[i], HIGH); // Röle LOW-active
  }
  Serial.println("Tüm röleler kapalı");
  
  // Servo motor
  servoKapi.attach(SERVO_KAPI_PIN);
  servoKapi.write(0); // Kapı kapalı
  Serial.println("Servo motor hazır");
  
  baslangicZaman = millis();
  
  Serial.println("=================================");
  Serial.println("SİSTEM HAZIR!");
  Serial.println("=================================\n");
  
  delay(2000);
}

// ==================== LOOP ====================
void loop() {
  unsigned long simdikiZaman = millis();
  
  // Periyodik kontrol (2 saniye)
  if (simdikiZaman - oncekiKontrolZaman >= KONTROL_ARALIK) {
    oncekiKontrolZaman = simdikiZaman;
    
    sensorleriOku();
    
    if (otomatikMod) {
      otomatikKontrol();
    }
  }
  
  // Periyodik veri gönderimi (5 saniye)
  if (simdikiZaman - oncekiVeriZaman >= VERI_GONDERME_ARALIK) {
    oncekiVeriZaman = simdikiZaman;
    veriGonder();
  }
  
  // ESP32'den komut kontrolü
  if (ESP32_SERIAL.available()) {
    komutIsle();
  }
  
  // Serial Monitor komut kontrolü (test için)
  if (Serial.available()) {
    String komut = Serial.readStringUntil('\n');
    komutIsle(komut);
  }
}

// ==================== SENSÖR OKUMA ====================
void sensorleriOku() {
  // DHT22 sensörler
  for (int i = 0; i < MAX_KUMES; i++) {
    kumesler[i].sicaklik = dhtSensors[i].readTemperature();
    kumesler[i].nem = dhtSensors[i].readHumidity();
    
    // Hata kontrolü
    if (isnan(kumesler[i].sicaklik) || isnan(kumesler[i].nem)) {
      kumesler[i].alarm = true;
      kumesler[i].alarmMesaj = "Sensor hatasi";
    }
  }
  
  // Su seviyeleri
  kumesler[0].suSeviyesi = analogRead(SU_SENSOR_1);
  kumesler[1].suSeviyesi = analogRead(SU_SENSOR_2);
  kumesler[2].suSeviyesi = (kumesler[0].suSeviyesi + kumesler[1].suSeviyesi) / 2;
  
  // Işık seviyeleri
  kumesler[0].isikSeviyesi = analogRead(LDR_1);
  kumesler[1].isikSeviyesi = analogRead(LDR_2);
  kumesler[2].isikSeviyesi = (kumesler[0].isikSeviyesi + kumesler[1].isikSeviyesi) / 2;
  
  // Çalışma süresi
  sistem.calismaSuresi = (millis() - baslangicZaman) / 1000;
}

// ==================== OTOMATİK KONTROL ====================
void otomatikKontrol() {
  for (int i = 0; i < MAX_KUMES; i++) {
    // Sıcaklık kontrolü
    if (kumesler[i].sicaklik > SICAKLIK_MAX) {
      // Çok sıcak - Fan aç
      if (i == 0) roleKontrol(ROLE_FAN_1, true);
      if (i == 1) roleKontrol(ROLE_FAN_2, true);
      kumesler[i].fanDurumu = true;
      roleKontrol(ROLE_ISITICI, false);
    }
    else if (kumesler[i].sicaklik < SICAKLIK_MIN) {
      // Çok soğuk - Isıtıcı aç
      roleKontrol(ROLE_ISITICI, true);
      if (i == 0) roleKontrol(ROLE_FAN_1, false);
      if (i == 1) roleKontrol(ROLE_FAN_2, false);
      kumesler[i].fanDurumu = false;
    }
    else {
      // Normal - Her şey kapat
      if (i == 0) roleKontrol(ROLE_FAN_1, false);
      if (i == 1) roleKontrol(ROLE_FAN_2, false);
      kumesler[i].fanDurumu = false;
    }
    
    // Nem kontrolü
    if (kumesler[i].nem < NEM_MIN) {
      kumesler[i].alarm = true;
      kumesler[i].alarmMesaj = "Nem dusuk";
    }
    
    // Su seviye kontrolü
    if (kumesler[i].suSeviyesi < SU_SEVIYE_MIN) {
      kumesler[i].alarm = true;
      kumesler[i].alarmMesaj = "Su seviyesi dusuk";
    }
  }
  
  // LED kontrolü (Işık seviyesine göre)
  int ortalamaIsik = (kumesler[0].isikSeviyesi + kumesler[1].isikSeviyesi) / 2;
  
  if (ortalamaIsik < 300) {
    // Karanlık - LED aç
    roleKontrol(ROLE_LED_1, true);
    roleKontrol(ROLE_LED_2, true);
    roleKontrol(ROLE_LED_3, true);
    for (int i = 0; i < MAX_KUMES; i++) {
      kumesler[i].ledDurumu = true;
    }
  } else {
    // Aydınlık - LED kapat
    roleKontrol(ROLE_LED_1, false);
    roleKontrol(ROLE_LED_2, false);
    roleKontrol(ROLE_LED_3, false);
    for (int i = 0; i < MAX_KUMES; i++) {
      kumesler[i].ledDurumu = false;
    }
  }
}

// ==================== RÖLE KONTROL ====================
void roleKontrol(int pin, bool durum) {
  // Röle LOW-active (LOW = AÇIK, HIGH = KAPALI)
  digitalWrite(pin, durum ? LOW : HIGH);
}

// ==================== VERİ GÖNDERME ====================
void veriGonder() {
  // JSON formatında tek satırda
  String json = "{";
  json += "\"sistem\":\"kumes\",";
  json += "\"zaman\":" + String(sistem.calismaSuresi) + ",";
  json += "\"kumesler\":[";
  
  for (int i = 0; i < MAX_KUMES; i++) {
    json += "{";
    json += "\"id\":" + String(kumesler[i].id) + ",";
    json += "\"sicaklik\":" + String(kumesler[i].sicaklik, 1) + ",";
    json += "\"nem\":" + String(kumesler[i].nem, 1) + ",";
    json += "\"su\":" + String(kumesler[i].suSeviyesi) + ",";
    json += "\"isik\":" + String(kumesler[i].isikSeviyesi) + ",";
    json += "\"fan\":" + String(kumesler[i].fanDurumu ? "true" : "false") + ",";
    json += "\"led\":" + String(kumesler[i].ledDurumu ? "true" : "false") + ",";
    json += "\"alarm\":" + String(kumesler[i].alarm ? "true" : "false");
    
    if (kumesler[i].alarm) {
      json += ",\"mesaj\":\"" + kumesler[i].alarmMesaj + "\"";
    }
    
    json += "}";
    if (i < MAX_KUMES - 1) json += ",";
  }
  
  json += "],";
  json += "\"yem\":15,";
  json += "\"pompa\":" + String(sistem.pompaDurumu ? "true" : "false");
  json += "}";
  
  // ESP32'ye gönder
  ESP32_SERIAL.println(json);
  
  // Debug
  Serial.println("Veri gönderildi:");
  Serial.println(json);
}

// ==================== KOMUT İŞLEME ====================
void komutIsle() {
  String komut = ESP32_SERIAL.readStringUntil('\n');
  komutIsle(komut);
}

void komutIsle(String komut) {
  komut.trim();
  
  Serial.println("Komut: " + komut);
  
  // FAN kontrol
  if (komut.startsWith("FAN1:")) {
    int durum = komut.substring(5).toInt();
    roleKontrol(ROLE_FAN_1, durum == 1);
    kumesler[0].fanDurumu = (durum == 1);
    ESP32_SERIAL.println("OK:Fan1");
  }
  else if (komut.startsWith("FAN2:")) {
    int durum = komut.substring(5).toInt();
    roleKontrol(ROLE_FAN_2, durum == 1);
    kumesler[1].fanDurumu = (durum == 1);
    ESP32_SERIAL.println("OK:Fan2");
  }
  
  // ISITICI kontrol
  else if (komut.startsWith("ISITICI:")) {
    int durum = komut.substring(8).toInt();
    roleKontrol(ROLE_ISITICI, durum == 1);
    ESP32_SERIAL.println("OK:Isitici");
  }
  
  // POMPA kontrol
  else if (komut.startsWith("POMPA:")) {
    int durum = komut.substring(6).toInt();
    roleKontrol(ROLE_POMPA, durum == 1);
    sistem.pompaDurumu = (durum == 1);
    ESP32_SERIAL.println("OK:Pompa");
  }
  
  // LED kontrol
  else if (komut.startsWith("LED:")) {
    int durum = komut.substring(4).toInt();
    roleKontrol(ROLE_LED_1, durum == 1);
    roleKontrol(ROLE_LED_2, durum == 1);
    roleKontrol(ROLE_LED_3, durum == 1);
    for (int i = 0; i < MAX_KUMES; i++) {
      kumesler[i].ledDurumu = (durum == 1);
    }
    ESP32_SERIAL.println("OK:LED");
  }
  
  // KAPI kontrol
  else if (komut.startsWith("KAPI:")) {
    int aci = komut.substring(5).toInt();
    servoKapi.write(aci);
    ESP32_SERIAL.println("OK:Kapi");
  }
  
  // YEM kontrol
  else if (komut.startsWith("YEM:")) {
    int sure = komut.substring(4).toInt();
    yemDagit(sure);
    ESP32_SERIAL.println("OK:Yem");
  }
  
  // OTOMATIK mod
  else if (komut == "AUTO:1") {
    otomatikMod = true;
    ESP32_SERIAL.println("OK:AutoOn");
  }
  else if (komut == "AUTO:0") {
    otomatikMod = false;
    ESP32_SERIAL.println("OK:AutoOff");
  }
  
  // STATUS
  else if (komut == "STATUS") {
    veriGonder();
    ESP32_SERIAL.println("OK:Status");
  }
  
  // Bilinmeyen komut
  else {
    ESP32_SERIAL.println("ERROR:UnknownCommand");
  }
}

// ==================== YEM DAĞITMA ====================
void yemDagit(int saniye) {
  roleKontrol(ROLE_YEM_MOTOR, true);
  
  unsigned long baslangic = millis();
  while (millis() - baslangic < saniye * 1000) {
    // Step motor döndürme (basit)
    delay(50);
  }
  
  roleKontrol(ROLE_YEM_MOTOR, false);
  Serial.println("Yem dağıtıldı");
}

// ==================== SON ====================
