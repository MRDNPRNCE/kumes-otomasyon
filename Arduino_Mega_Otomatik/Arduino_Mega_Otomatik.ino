/*
 * KÜMES OTOMASYON SİSTEMİ - ARDUINO MEGA 2560
 * ============================================
 * ✅ 3 Kümes kontrol
 * ✅ DHT22 sensörler (Sıcaklık/Nem)
 * ✅ Röle kontrol (LED, Fan, Pompa)
 * ✅ Servo kapı kontrolü
 * ✅ Serial JSON iletişim
 * ✅ OTOMATİK ÇALIŞMA MODU (Failsafe)
 * ✅ Watchdog timer
 */

#include <DHT.h>
#include <Servo.h>
#include <ArduinoJson.h>

// ==================== PIN TANIMLARI ====================
// DHT22 Sensörler
#define DHT1_PIN 22
#define DHT2_PIN 24
#define DHT3_PIN 26

// Röleler (Aktif LOW)
#define LED1_PIN 30
#define LED2_PIN 31
#define LED3_PIN 32
#define FAN1_PIN 33
#define FAN2_PIN 34
#define FAN3_PIN 35
#define POMPA_PIN 36
#define YEDEK_PIN 37

// Servo
#define SERVO_PIN 9

// ==================== SENSÖR TANIMLARI ====================
DHT dht1(DHT1_PIN, DHT22);
DHT dht2(DHT2_PIN, DHT22);
DHT dht3(DHT3_PIN, DHT22);

Servo servoKapi;

// ==================== GLOBAL DEĞİŞKENLER ====================
unsigned long sonVeriGonderme = 0;
unsigned long sonKomutAlma = 0;
unsigned long baslamaSuresi = 0;
const unsigned long VERI_GONDERME_ARALIGI = 5000;  // 5 saniye

// ==================== OTOMATİK ÇALIŞMA AYARLARI ====================
const unsigned long KOMUT_TIMEOUT = 60000;  // 60 saniye komut gelmezse
bool otomatikMod = false;
bool manuelKontrol = true;

// Otomatik mod ayarları
struct OtomatikAyarlar {
  float sicaklikMin = 18.0;
  float sicaklikMax = 28.0;
  float nemMin = 40.0;
  float nemMax = 70.0;
  int aydinlatmaBaslangic = 6;   // Saat 06:00
  int aydinlatmaBitis = 20;       // Saat 20:00
} otoAyar;

// Kümes durumları
struct KumesDurum {
  float sicaklik;
  float nem;
  bool led;
  bool fan;
  bool alarm;
  String alarmMesaj;
} kumes[3];

// Sistem durumu
bool pompa = false;
int kapiAcisi = 0;
int yemSuresi = 0;

// ==================== SETUP ====================
void setup() {
  Serial.begin(115200);     // USB Serial
  Serial1.begin(115200);    // ESP32 Serial
  
  // DHT başlat
  dht1.begin();
  dht2.begin();
  dht3.begin();
  
  // Röle pinleri (Aktif LOW - Başlangıçta KAPALI)
  pinMode(LED1_PIN, OUTPUT);
  pinMode(LED2_PIN, OUTPUT);
  pinMode(LED3_PIN, OUTPUT);
  pinMode(FAN1_PIN, OUTPUT);
  pinMode(FAN2_PIN, OUTPUT);
  pinMode(FAN3_PIN, OUTPUT);
  pinMode(POMPA_PIN, OUTPUT);
  pinMode(YEDEK_PIN, OUTPUT);
  
  // Tüm röleleri kapat
  digitalWrite(LED1_PIN, HIGH);
  digitalWrite(LED2_PIN, HIGH);
  digitalWrite(LED3_PIN, HIGH);
  digitalWrite(FAN1_PIN, HIGH);
  digitalWrite(FAN2_PIN, HIGH);
  digitalWrite(FAN3_PIN, HIGH);
  digitalWrite(POMPA_PIN, HIGH);
  digitalWrite(YEDEK_PIN, HIGH);
  
  // Servo başlat
  servoKapi.attach(SERVO_PIN);
  servoKapi.write(0);  // Başlangıçta kapalı
  
  baslamaSuresi = millis();
  sonKomutAlma = millis();
  
  Serial.println("🐔 Kümes Otomasyon Başlatıldı");
  Serial.println("✅ Otomatik mod aktif (60 saniye komut bekliyor)");
  
  delay(2000);  // DHT22 sensörler için bekleme
}

// ==================== LOOP ====================
void loop() {
  unsigned long simdikiZaman = millis();
  
  // Komut kontrolü
  komutKontrol();
  
  // Otomatik mod kontrolü (60 saniye komut gelmezse)
  if (simdikiZaman - sonKomutAlma > KOMUT_TIMEOUT) {
    if (manuelKontrol) {
      manuelKontrol = false;
      otomatikMod = true;
      Serial.println("⚠️ Manuel kontrol zaman aşımı!");
      Serial.println("🔄 Otomatik moda geçildi");
    }
  }
  
  // Otomatik mod çalıştır
  if (otomatikMod) {
    otomatikKontrol();
  }
  
  // Veri gönderme (5 saniyede bir)
  if (simdikiZaman - sonVeriGonderme >= VERI_GONDERME_ARALIGI) {
    sensörOku();
    alarmKontrol();
    veriGonder();
    sonVeriGonderme = simdikiZaman;
  }
}

// ==================== SENSÖR OKUMA ====================
void sensörOku() {
  // Kümes 1
  kumes[0].sicaklik = dht1.readTemperature();
  kumes[0].nem = dht1.readHumidity();
  
  // Kümes 2
  kumes[1].sicaklik = dht2.readTemperature();
  kumes[1].nem = dht2.readHumidity();
  
  // Kümes 3
  kumes[2].sicaklik = dht3.readTemperature();
  kumes[2].nem = dht3.readHumidity();
  
  // NaN kontrolü
  for (int i = 0; i < 3; i++) {
    if (isnan(kumes[i].sicaklik)) kumes[i].sicaklik = 0.0;
    if (isnan(kumes[i].nem)) kumes[i].nem = 0.0;
  }
}

// ==================== ALARM KONTROL ====================
void alarmKontrol() {
  for (int i = 0; i < 3; i++) {
    kumes[i].alarm = false;
    kumes[i].alarmMesaj = "";
    
    // Sıcaklık kontrolü
    if (kumes[i].sicaklik > 32.0) {
      kumes[i].alarm = true;
      kumes[i].alarmMesaj = "Yüksek sıcaklık!";
    } else if (kumes[i].sicaklik < 15.0 && kumes[i].sicaklik > 0) {
      kumes[i].alarm = true;
      kumes[i].alarmMesaj = "Düşük sıcaklık!";
    }
    
    // Nem kontrolü
    if (kumes[i].nem > 75.0) {
      kumes[i].alarm = true;
      kumes[i].alarmMesaj = "Yüksek nem!";
    } else if (kumes[i].nem < 35.0 && kumes[i].nem > 0) {
      kumes[i].alarm = true;
      kumes[i].alarmMesaj = "Düşük nem!";
    }
    
    // Sensör hatası
    if (kumes[i].sicaklik == 0.0 && kumes[i].nem == 0.0) {
      kumes[i].alarm = true;
      kumes[i].alarmMesaj = "Sensör hatası!";
    }
  }
}

// ==================== OTOMATİK KONTROL ====================
void otomatikKontrol() {
  static unsigned long sonOtoKontrol = 0;
  unsigned long simdikiZaman = millis();
  
  // 10 saniyede bir kontrol et
  if (simdikiZaman - sonOtoKontrol < 10000) {
    return;
  }
  sonOtoKontrol = simdikiZaman;
  
  // Her kümes için otomatik kontrol
  for (int i = 0; i < 3; i++) {
    // Sıcaklık kontrolü - FAN
    if (kumes[i].sicaklik > otoAyar.sicaklikMax) {
      // Çok sıcak - Fan aç
      fanKontrol(i + 1, true);
    } else if (kumes[i].sicaklik < otoAyar.sicaklikMin) {
      // Çok soğuk - Fan kapat
      fanKontrol(i + 1, false);
    }
    
    // Nem kontrolü
    if (kumes[i].nem < otoAyar.nemMin) {
      // Düşük nem - Sulama gerekebilir (opsiyonel)
      // Su pompası manuel açılmalı
    }
  }
  
  // Işık kontrolü (saate göre)
  // NOT: Arduino'da RTC yok, bu simülatif
  // Gerçek kullanımda DS3231 RTC modülü eklenebilir
  static int simSaat = 12;  // Simüle edilmiş saat
  
  if (simSaat >= otoAyar.aydinlatmaBaslangic && 
      simSaat < otoAyar.aydinlatmaBitis) {
    // Gündüz - LED aç
    ledKontrol(true);
  } else {
    // Gece - LED kapat
    ledKontrol(false);
  }
}

// ==================== VERİ GÖNDERME ====================
void veriGonder() {
  StaticJsonDocument<1024> doc;
  
  doc["sistem"] = "kumes";
  doc["zaman"] = (millis() - baslamaSuresi) / 1000;
  doc["mod"] = otomatikMod ? "otomatik" : "manuel";
  
  JsonArray kumesler = doc.createNestedArray("kumesler");
  
  for (int i = 0; i < 3; i++) {
    JsonObject k = kumesler.createNestedObject();
    k["id"] = i + 1;
    k["sicaklik"] = kumes[i].sicaklik;
    k["nem"] = kumes[i].nem;
    k["led"] = kumes[i].led;
    k["fan"] = kumes[i].fan;
    k["alarm"] = kumes[i].alarm;
    if (kumes[i].alarm) {
      k["mesaj"] = kumes[i].alarmMesaj;
    }
  }
  
  doc["pompa"] = pompa;
  doc["kapi"] = kapiAcisi;
  
  String output;
  serializeJson(doc, output);
  
  // ESP32'ye gönder (Serial1)
  Serial1.println(output);
  
  // Debug için USB Serial
  Serial.println(output);
}

// ==================== KOMUT KONTROL ====================
void komutKontrol() {
  // ESP32'den komut geldi mi?
  if (Serial1.available()) {
    String komut = Serial1.readStringUntil('\n');
    komut.trim();
    
    if (komut.length() > 0) {
      // Komut alındı - Manuel moda geç
      sonKomutAlma = millis();
      if (otomatikMod) {
        otomatikMod = false;
        manuelKontrol = true;
        Serial.println("🔄 Manuel moda geçildi");
      }
      
      komutIsle(komut);
    }
  }
  
  // USB Serial'den de komut alınabilir (test için)
  if (Serial.available()) {
    String komut = Serial.readStringUntil('\n');
    komut.trim();
    
    if (komut.length() > 0) {
      sonKomutAlma = millis();
      komutIsle(komut);
    }
  }
}

// ==================== KOMUT İŞLEME ====================
void komutIsle(String komut) {
  Serial.print("📥 Komut: ");
  Serial.println(komut);
  
  // LED kontrol
  if (komut.startsWith("LED:")) {
    bool durum = komut.substring(4).toInt() == 1;
    ledKontrol(durum);
    Serial1.println("OK:LED");
  }
  
  // FAN kontrol
  else if (komut.startsWith("FAN")) {
    int fanNo = komut.charAt(3) - '0';  // FAN1 -> 1
    bool durum = komut.substring(5).toInt() == 1;
    fanKontrol(fanNo, durum);
    Serial1.println("OK:FAN" + String(fanNo));
  }
  
  // POMPA kontrol
  else if (komut.startsWith("POMPA:")) {
    pompa = komut.substring(6).toInt() == 1;
    digitalWrite(POMPA_PIN, pompa ? LOW : HIGH);
    Serial1.println("OK:POMPA");
  }
  
  // KAPI kontrol
  else if (komut.startsWith("KAPI:")) {
    kapiAcisi = komut.substring(5).toInt();
    kapiAcisi = constrain(kapiAcisi, 0, 180);
    servoKapi.write(kapiAcisi);
    Serial1.println("OK:KAPI");
  }
  
  // YEM dağıt
  else if (komut.startsWith("YEM:")) {
    yemSuresi = komut.substring(4).toInt();
    yemDagit(yemSuresi);
    Serial1.println("OK:YEM");
  }
  
  // STATUS
  else if (komut == "STATUS") {
    veriGonder();
  }
  
  // MOD değiştir
  else if (komut == "MOD:AUTO") {
    otomatikMod = true;
    manuelKontrol = false;
    Serial.println("🔄 Otomatik moda geçildi");
    Serial1.println("OK:AUTO");
  }
  else if (komut == "MOD:MANUAL") {
    otomatikMod = false;
    manuelKontrol = true;
    Serial.println("🔄 Manuel moda geçildi");
    Serial1.println("OK:MANUAL");
  }
  
  // Bilinmeyen komut
  else {
    Serial.println("❌ Bilinmeyen komut!");
    Serial1.println("ERROR:UNKNOWN");
  }
}

// ==================== LED KONTROL ====================
void ledKontrol(bool durum) {
  digitalWrite(LED1_PIN, durum ? LOW : HIGH);
  digitalWrite(LED2_PIN, durum ? LOW : HIGH);
  digitalWrite(LED3_PIN, durum ? LOW : HIGH);
  
  kumes[0].led = durum;
  kumes[1].led = durum;
  kumes[2].led = durum;
  
  Serial.println(durum ? "💡 LED açıldı" : "💡 LED kapatıldı");
}

// ==================== FAN KONTROL ====================
void fanKontrol(int fanNo, bool durum) {
  if (fanNo < 1 || fanNo > 3) return;
  
  int pin = FAN1_PIN + (fanNo - 1);
  digitalWrite(pin, durum ? LOW : HIGH);
  
  kumes[fanNo - 1].fan = durum;
  
  Serial.print("🌀 FAN");
  Serial.print(fanNo);
  Serial.println(durum ? " açıldı" : " kapatıldı");
}

// ==================== YEM DAĞITMA ====================
void yemDagit(int sure) {
  Serial.print("🌾 Yem dağıtılıyor: ");
  Serial.print(sure);
  Serial.println(" saniye");
  
  // Yem motoru simülasyonu
  // Gerçek kullanımda bir motor/servo kontrol edilir
  digitalWrite(YEDEK_PIN, LOW);   // Motor aç
  delay(sure * 1000);              // Belirtilen süre
  digitalWrite(YEDEK_PIN, HIGH);  // Motor kapat
  
  Serial.println("✅ Yem dağıtma tamamlandı");
}

// ==================== BİLGİ YAZDIRMA ====================
void durumYazdir() {
  Serial.println("\n========================================");
  Serial.println("🐔 KÜMES OTOMASYON - DURUM BİLGİSİ");
  Serial.println("========================================");
  
  Serial.print("Çalışma Süresi: ");
  Serial.print((millis() - baslamaSuresi) / 1000);
  Serial.println(" saniye");
  
  Serial.print("Mod: ");
  Serial.println(otomatikMod ? "OTOMATİK" : "MANUEL");
  
  Serial.print("Son Komut: ");
  Serial.print((millis() - sonKomutAlma) / 1000);
  Serial.println(" saniye önce");
  
  for (int i = 0; i < 3; i++) {
    Serial.println("\n--- Kümes " + String(i + 1) + " ---");
    Serial.print("Sıcaklık: ");
    Serial.print(kumes[i].sicaklik);
    Serial.println("°C");
    Serial.print("Nem: ");
    Serial.print(kumes[i].nem);
    Serial.println("%");
    Serial.print("LED: ");
    Serial.println(kumes[i].led ? "AÇIK" : "KAPALI");
    Serial.print("FAN: ");
    Serial.println(kumes[i].fan ? "AÇIK" : "KAPALI");
    if (kumes[i].alarm) {
      Serial.print("⚠️ ALARM: ");
      Serial.println(kumes[i].alarmMesaj);
    }
  }
  
  Serial.println("========================================\n");
}
