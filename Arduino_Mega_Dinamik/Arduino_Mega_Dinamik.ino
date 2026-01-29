/*
 * KÜMES OTOMASYON SİSTEMİ - ARDUINO MEGA 2560
 * ============================================
 * ✅ 3 Kümes kontrol
 * ✅ DHT22 sensörler (Sıcaklık/Nem)
 * ✅ Röle kontrol (LED, Fan, Pompa)
 * ✅ Servo kapı kontrolü
 * ✅ Serial JSON iletişim
 * ✅ OTOMATİK ÇALIŞMA MODU (Failsafe)
 * ✅ DİNAMİK AYARLAR (PWA'dan değiştirilebilir)
 */

#include <DHT.h>
#include <Servo.h>
#include <ArduinoJson.h>
#include <EEPROM.h>

// ==================== PIN TANIMLARI ====================
#define DHT1_PIN 22
#define DHT2_PIN 24
#define DHT3_PIN 26

#define LED1_PIN 30
#define LED2_PIN 31
#define LED3_PIN 32
#define FAN1_PIN 33
#define FAN2_PIN 34
#define FAN3_PIN 35
#define POMPA_PIN 36
#define YEDEK_PIN 37

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
const unsigned long VERI_GONDERME_ARALIGI = 5000;

// ==================== OTOMATİK AYARLAR (DİNAMİK) ====================
struct OtomatikAyarlar {
  unsigned long timeout = 60000;        // Timeout süresi (ms)
  float sicaklikMin = 18.0;             // Min sıcaklık (°C)
  float sicaklikMax = 28.0;             // Max sıcaklık (°C)
  float nemMin = 40.0;                  // Min nem (%)
  float nemMax = 70.0;                  // Max nem (%)
  int aydinlatmaBaslangic = 6;          // LED açılış saati
  int aydinlatmaBitis = 20;             // LED kapanış saati
  bool otomatikFan = true;              // Otomatik fan kontrolü
  bool otomatikLed = true;              // Otomatik LED kontrolü
  int kontrol_araligi = 10;             // Kontrol aralığı (saniye)
} otoAyar;

// EEPROM adresleri
#define EEPROM_ADDR_TIMEOUT 0
#define EEPROM_ADDR_SICAK_MIN 4
#define EEPROM_ADDR_SICAK_MAX 8
#define EEPROM_ADDR_NEM_MIN 12
#define EEPROM_ADDR_NEM_MAX 16
#define EEPROM_ADDR_AYDINLATMA_START 20
#define EEPROM_ADDR_AYDINLATMA_END 24
#define EEPROM_ADDR_AUTO_FAN 28
#define EEPROM_ADDR_AUTO_LED 29
#define EEPROM_ADDR_KONTROL_ARALIGI 30

bool otomatikMod = false;
bool manuelKontrol = true;

// Kümes durumları
struct KumesDurum {
  float sicaklik;
  float nem;
  bool led;
  bool fan;
  bool alarm;
  String alarmMesaj;
} kumes[3];

bool pompa = false;
int kapiAcisi = 0;
int yemSuresi = 0;

// ==================== SETUP ====================
void setup() {
  Serial.begin(115200);
  Serial1.begin(115200);
  
  // DHT başlat
  dht1.begin();
  dht2.begin();
  dht3.begin();
  
  // Röle pinleri
  pinMode(LED1_PIN, OUTPUT);
  pinMode(LED2_PIN, OUTPUT);
  pinMode(LED3_PIN, OUTPUT);
  pinMode(FAN1_PIN, OUTPUT);
  pinMode(FAN2_PIN, OUTPUT);
  pinMode(FAN3_PIN, OUTPUT);
  pinMode(POMPA_PIN, OUTPUT);
  pinMode(YEDEK_PIN, OUTPUT);
  
  digitalWrite(LED1_PIN, HIGH);
  digitalWrite(LED2_PIN, HIGH);
  digitalWrite(LED3_PIN, HIGH);
  digitalWrite(FAN1_PIN, HIGH);
  digitalWrite(FAN2_PIN, HIGH);
  digitalWrite(FAN3_PIN, HIGH);
  digitalWrite(POMPA_PIN, HIGH);
  digitalWrite(YEDEK_PIN, HIGH);
  
  servoKapi.attach(SERVO_PIN);
  servoKapi.write(0);
  
  // EEPROM'dan ayarları yükle
  ayarlariYukle();
  
  baslamaSuresi = millis();
  sonKomutAlma = millis();
  
  Serial.println("🐔 Kümes Otomasyon Başlatıldı");
  Serial.print("✅ Otomatik mod timeout: ");
  Serial.print(otoAyar.timeout / 1000);
  Serial.println(" saniye");
  ayarlariYazdir();
  
  delay(2000);
}

// ==================== LOOP ====================
void loop() {
  unsigned long simdikiZaman = millis();
  
  komutKontrol();
  
  // Otomatik mod kontrolü (dinamik timeout)
  if (simdikiZaman - sonKomutAlma > otoAyar.timeout) {
    if (manuelKontrol) {
      manuelKontrol = false;
      otomatikMod = true;
      Serial.println("⚠️ Manuel kontrol zaman aşımı!");
      Serial.println("🔄 Otomatik moda geçildi");
    }
  }
  
  if (otomatikMod) {
    otomatikKontrol();
  }
  
  if (simdikiZaman - sonVeriGonderme >= VERI_GONDERME_ARALIGI) {
    sensorOku();
    alarmKontrol();
    veriGonder();
    sonVeriGonderme = simdikiZaman;
  }
}

// ==================== EEPROM FONKSİYONLARI ====================
void ayarlariKaydet() {
  EEPROM.put(EEPROM_ADDR_TIMEOUT, otoAyar.timeout);
  EEPROM.put(EEPROM_ADDR_SICAK_MIN, otoAyar.sicaklikMin);
  EEPROM.put(EEPROM_ADDR_SICAK_MAX, otoAyar.sicaklikMax);
  EEPROM.put(EEPROM_ADDR_NEM_MIN, otoAyar.nemMin);
  EEPROM.put(EEPROM_ADDR_NEM_MAX, otoAyar.nemMax);
  EEPROM.put(EEPROM_ADDR_AYDINLATMA_START, otoAyar.aydinlatmaBaslangic);
  EEPROM.put(EEPROM_ADDR_AYDINLATMA_END, otoAyar.aydinlatmaBitis);
  EEPROM.put(EEPROM_ADDR_AUTO_FAN, otoAyar.otomatikFan);
  EEPROM.put(EEPROM_ADDR_AUTO_LED, otoAyar.otomatikLed);
  EEPROM.put(EEPROM_ADDR_KONTROL_ARALIGI, otoAyar.kontrol_araligi);
  
  Serial.println("💾 Ayarlar EEPROM'a kaydedildi");
}

void ayarlariYukle() {
  unsigned long timeout;
  EEPROM.get(EEPROM_ADDR_TIMEOUT, timeout);
  
  // İlk çalıştırma kontrolü (EEPROM boş)
  if (timeout == 0xFFFFFFFF || timeout == 0 || timeout > 3600000) {
    Serial.println("⚠️ EEPROM boş, varsayılan ayarlar kullanılıyor");
    ayarlariKaydet();
    return;
  }
  
  otoAyar.timeout = timeout;
  EEPROM.get(EEPROM_ADDR_SICAK_MIN, otoAyar.sicaklikMin);
  EEPROM.get(EEPROM_ADDR_SICAK_MAX, otoAyar.sicaklikMax);
  EEPROM.get(EEPROM_ADDR_NEM_MIN, otoAyar.nemMin);
  EEPROM.get(EEPROM_ADDR_NEM_MAX, otoAyar.nemMax);
  EEPROM.get(EEPROM_ADDR_AYDINLATMA_START, otoAyar.aydinlatmaBaslangic);
  EEPROM.get(EEPROM_ADDR_AYDINLATMA_END, otoAyar.aydinlatmaBitis);
  EEPROM.get(EEPROM_ADDR_AUTO_FAN, otoAyar.otomatikFan);
  EEPROM.get(EEPROM_ADDR_AUTO_LED, otoAyar.otomatikLed);
  EEPROM.get(EEPROM_ADDR_KONTROL_ARALIGI, otoAyar.kontrol_araligi);
  
  Serial.println("✅ Ayarlar EEPROM'dan yüklendi");
}

void ayarlariSifirla() {
  otoAyar.timeout = 60000;
  otoAyar.sicaklikMin = 18.0;
  otoAyar.sicaklikMax = 28.0;
  otoAyar.nemMin = 40.0;
  otoAyar.nemMax = 70.0;
  otoAyar.aydinlatmaBaslangic = 6;
  otoAyar.aydinlatmaBitis = 20;
  otoAyar.otomatikFan = true;
  otoAyar.otomatikLed = true;
  otoAyar.kontrol_araligi = 10;
  
  ayarlariKaydet();
  Serial.println("🔄 Ayarlar varsayılana sıfırlandı");
}

// ==================== SENSÖR OKUMA ====================
void sensorOku() {
  kumes[0].sicaklik = dht1.readTemperature();
  kumes[0].nem = dht1.readHumidity();
  
  kumes[1].sicaklik = dht2.readTemperature();
  kumes[1].nem = dht2.readHumidity();
  
  kumes[2].sicaklik = dht3.readTemperature();
  kumes[2].nem = dht3.readHumidity();
  
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
    
    // Sıcaklık kontrolü (dinamik limitler)
    if (kumes[i].sicaklik > otoAyar.sicaklikMax + 4) {
      kumes[i].alarm = true;
      kumes[i].alarmMesaj = "Yüksek sıcaklık!";
    } else if (kumes[i].sicaklik < otoAyar.sicaklikMin - 3 && kumes[i].sicaklik > 0) {
      kumes[i].alarm = true;
      kumes[i].alarmMesaj = "Düşük sıcaklık!";
    }
    
    // Nem kontrolü (dinamik limitler)
    if (kumes[i].nem > otoAyar.nemMax + 5) {
      kumes[i].alarm = true;
      kumes[i].alarmMesaj = "Yüksek nem!";
    } else if (kumes[i].nem < otoAyar.nemMin - 5 && kumes[i].nem > 0) {
      kumes[i].alarm = true;
      kumes[i].alarmMesaj = "Düşük nem!";
    }
    
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
  
  // Dinamik kontrol aralığı
  if (simdikiZaman - sonOtoKontrol < otoAyar.kontrol_araligi * 1000) {
    return;
  }
  sonOtoKontrol = simdikiZaman;
  
  // Otomatik fan kontrolü
  if (otoAyar.otomatikFan) {
    for (int i = 0; i < 3; i++) {
      if (kumes[i].sicaklik > otoAyar.sicaklikMax) {
        fanKontrol(i + 1, true);
      } else if (kumes[i].sicaklik < otoAyar.sicaklikMin) {
        fanKontrol(i + 1, false);
      }
    }
  }
  
  // Otomatik LED kontrolü (saate göre)
  if (otoAyar.otomatikLed) {
    // Simüle edilmiş saat (gerçek RTC kullanılabilir)
    static int simSaat = 12;
    
    if (simSaat >= otoAyar.aydinlatmaBaslangic && 
        simSaat < otoAyar.aydinlatmaBitis) {
      ledKontrol(true);
    } else {
      ledKontrol(false);
    }
  }
}

// ==================== VERİ GÖNDERME ====================
void veriGonder() {
  StaticJsonDocument<2048> doc;
  
  doc["sistem"] = "kumes";
  doc["zaman"] = (millis() - baslamaSuresi) / 1000;
  doc["mod"] = otomatikMod ? "otomatik" : "manuel";
  
  // Otomatik ayarları ekle
  JsonObject ayarlar = doc.createNestedObject("otomatik_ayarlar");
  ayarlar["timeout"] = otoAyar.timeout / 1000;  // saniye cinsinden
  ayarlar["sicaklik_min"] = otoAyar.sicaklikMin;
  ayarlar["sicaklik_max"] = otoAyar.sicaklikMax;
  ayarlar["nem_min"] = otoAyar.nemMin;
  ayarlar["nem_max"] = otoAyar.nemMax;
  ayarlar["led_baslangic"] = otoAyar.aydinlatmaBaslangic;
  ayarlar["led_bitis"] = otoAyar.aydinlatmaBitis;
  ayarlar["otomatik_fan"] = otoAyar.otomatikFan;
  ayarlar["otomatik_led"] = otoAyar.otomatikLed;
  ayarlar["kontrol_araligi"] = otoAyar.kontrol_araligi;
  
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
  
  Serial1.println(output);
  // Serial.println(output);  // Debug için
}

// ==================== KOMUT KONTROL ====================
void komutKontrol() {
  if (Serial1.available()) {
    String komut = Serial1.readStringUntil('\n');
    komut.trim();
    
    if (komut.length() > 0) {
      sonKomutAlma = millis();
      if (otomatikMod) {
        otomatikMod = false;
        manuelKontrol = true;
        Serial.println("🔄 Manuel moda geçildi");
      }
      
      komutIsle(komut);
    }
  }
  
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
    int fanNo = komut.charAt(3) - '0';
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
  
  // AYAR komutları (JSON formatında)
  else if (komut.startsWith("AYAR:")) {
    ayarKomutIsle(komut.substring(5));
  }
  
  // AYAR sorgula
  else if (komut == "AYAR?") {
    ayarlariGonder();
  }
  
  // AYAR sıfırla
  else if (komut == "AYAR:RESET") {
    ayarlariSifirla();
    Serial1.println("OK:RESET");
  }
  
  else {
    Serial.println("❌ Bilinmeyen komut!");
    Serial1.println("ERROR:UNKNOWN");
  }
}

// ==================== AYAR KOMUT İŞLEME ====================
void ayarKomutIsle(String jsonStr) {
  StaticJsonDocument<512> doc;
  DeserializationError error = deserializeJson(doc, jsonStr);
  
  if (error) {
    Serial.println("❌ JSON parse hatası!");
    Serial1.println("ERROR:JSON");
    return;
  }
  
  bool degisti = false;
  
  if (doc.containsKey("timeout")) {
    otoAyar.timeout = doc["timeout"].as<unsigned long>() * 1000;  // saniye → ms
    degisti = true;
  }
  if (doc.containsKey("sicaklik_min")) {
    otoAyar.sicaklikMin = doc["sicaklik_min"];
    degisti = true;
  }
  if (doc.containsKey("sicaklik_max")) {
    otoAyar.sicaklikMax = doc["sicaklik_max"];
    degisti = true;
  }
  if (doc.containsKey("nem_min")) {
    otoAyar.nemMin = doc["nem_min"];
    degisti = true;
  }
  if (doc.containsKey("nem_max")) {
    otoAyar.nemMax = doc["nem_max"];
    degisti = true;
  }
  if (doc.containsKey("led_baslangic")) {
    otoAyar.aydinlatmaBaslangic = doc["led_baslangic"];
    degisti = true;
  }
  if (doc.containsKey("led_bitis")) {
    otoAyar.aydinlatmaBitis = doc["led_bitis"];
    degisti = true;
  }
  if (doc.containsKey("otomatik_fan")) {
    otoAyar.otomatikFan = doc["otomatik_fan"];
    degisti = true;
  }
  if (doc.containsKey("otomatik_led")) {
    otoAyar.otomatikLed = doc["otomatik_led"];
    degisti = true;
  }
  if (doc.containsKey("kontrol_araligi")) {
    otoAyar.kontrol_araligi = doc["kontrol_araligi"];
    degisti = true;
  }
  
  if (degisti) {
    ayarlariKaydet();
    ayarlariYazdir();
    Serial1.println("OK:AYAR");
  }
}

// ==================== AYARLARI GÖNDER ====================
void ayarlariGonder() {
  StaticJsonDocument<512> doc;
  
  doc["timeout"] = otoAyar.timeout / 1000;
  doc["sicaklik_min"] = otoAyar.sicaklikMin;
  doc["sicaklik_max"] = otoAyar.sicaklikMax;
  doc["nem_min"] = otoAyar.nemMin;
  doc["nem_max"] = otoAyar.nemMax;
  doc["led_baslangic"] = otoAyar.aydinlatmaBaslangic;
  doc["led_bitis"] = otoAyar.aydinlatmaBitis;
  doc["otomatik_fan"] = otoAyar.otomatikFan;
  doc["otomatik_led"] = otoAyar.otomatikLed;
  doc["kontrol_araligi"] = otoAyar.kontrol_araligi;
  
  String output;
  serializeJson(doc, output);
  
  Serial1.print("AYAR:");
  Serial1.println(output);
  
  Serial.print("AYAR:");
  Serial.println(output);
}

// ==================== AYARLARI YAZDIR ====================
void ayarlariYazdir() {
  Serial.println("\n========== OTOMATİK MOD AYARLARI ==========");
  Serial.print("Timeout: "); Serial.print(otoAyar.timeout / 1000); Serial.println(" sn");
  Serial.print("Sıcaklık Min: "); Serial.print(otoAyar.sicaklikMin); Serial.println("°C");
  Serial.print("Sıcaklık Max: "); Serial.print(otoAyar.sicaklikMax); Serial.println("°C");
  Serial.print("Nem Min: "); Serial.print(otoAyar.nemMin); Serial.println("%");
  Serial.print("Nem Max: "); Serial.print(otoAyar.nemMax); Serial.println("%");
  Serial.print("LED Başlangıç: "); Serial.println(otoAyar.aydinlatmaBaslangic);
  Serial.print("LED Bitiş: "); Serial.println(otoAyar.aydinlatmaBitis);
  Serial.print("Otomatik Fan: "); Serial.println(otoAyar.otomatikFan ? "Aktif" : "Pasif");
  Serial.print("Otomatik LED: "); Serial.println(otoAyar.otomatikLed ? "Aktif" : "Pasif");
  Serial.print("Kontrol Aralığı: "); Serial.print(otoAyar.kontrol_araligi); Serial.println(" sn");
  Serial.println("==========================================\n");
}

// ==================== LED KONTROL ====================
void ledKontrol(bool durum) {
  digitalWrite(LED1_PIN, durum ? LOW : HIGH);
  digitalWrite(LED2_PIN, durum ? LOW : HIGH);
  digitalWrite(LED3_PIN, durum ? LOW : HIGH);
  
  kumes[0].led = durum;
  kumes[1].led = durum;
  kumes[2].led = durum;
}

// ==================== FAN KONTROL ====================
void fanKontrol(int fanNo, bool durum) {
  if (fanNo < 1 || fanNo > 3) return;
  
  int pin = FAN1_PIN + (fanNo - 1);
  digitalWrite(pin, durum ? LOW : HIGH);
  
  kumes[fanNo - 1].fan = durum;
}

// ==================== YEM DAĞITMA ====================
void yemDagit(int sure) {
  Serial.print("🌾 Yem dağıtılıyor: ");
  Serial.print(sure);
  Serial.println(" saniye");
  
  digitalWrite(YEDEK_PIN, LOW);
  delay(sure * 1000);
  digitalWrite(YEDEK_PIN, HIGH);
  
  Serial.println("✅ Yem dağıtma tamamlandı");
}
