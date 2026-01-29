/*
 * KÜMES OTOMASYON SİSTEMİ - ARDUINO MEGA 2560
 * ============================================
 * ✅ 3 Kümes kontrol
 * ✅ CJX-HT1420DXSA Sensörler (28V, 4-20mA, 650Ω ŞÖNT)
 * ✅ VOLTAJ BÖLÜCÜ: 650Ω + 220Ω
 * ✅ Röle kontrol (LED, Fan, Pompa)
 * ✅ Servo kapı kontrolü
 * ✅ Serial JSON iletişim
 * ✅ OTOMATİK ÇALIŞMA MODU (Failsafe)
 * ✅ DİNAMİK AYARLAR (PWA'dan değiştirilebilir)
 * 
 * ⚠️ ÖNEMLİ UYARI:
 * Bu kod 650Ω şönt direnci + 220Ω voltaj bölücü kullanır!
 * Voltaj bölücü OLMADAN bağlarsanız Arduino YANAR!
 * 
 * DEVRE ŞEMASI:
 * Sensör OUT → 650Ω (2W) → ┬─ 220Ω (0.5W) → Arduino Analog Pin
 *                          │                 → GND
 *                          └─ GND
 * 
 * VOLTAJ ARALIĞI:
 * 4mA  → 2.6V × (220/870) = 0.66V (Arduino'da)
 * 20mA → 13.0V × (220/870) = 3.30V (Arduino'da)
 */

#include <Servo.h>
#include <ArduinoJson.h>
#include <EEPROM.h>

// ==================== PIN TANIMLARI ====================
// 4-20mA Analog Sensör Pinleri (Sıcaklık)
#define TEMP1_PIN A0
#define TEMP2_PIN A1
#define TEMP3_PIN A2

// 4-20mA Analog Sensör Pinleri (Nem)
#define HUM1_PIN A3
#define HUM2_PIN A4
#define HUM3_PIN A5

#define LED1_PIN 30
#define LED2_PIN 31
#define LED3_PIN 32
#define FAN1_PIN 33
#define FAN2_PIN 34
#define FAN3_PIN 35
#define POMPA_PIN 36
#define YEDEK_PIN 37

#define SERVO_PIN 9

// ==================== SENSÖR KALİBRASYON (650Ω ŞÖNT) ====================
#define CURRENT_MIN 4.0              // mA (minimum akım)
#define CURRENT_MAX 20.0             // mA (maksimum akım)
#define SHUNT_RESISTOR 650.0         // Ω (şönt direnci - 2W)
#define VOLTAGE_DIVIDER_R1 650.0     // Ω (şönt)
#define VOLTAGE_DIVIDER_R2 220.0     // Ω (voltaj bölücü - 0.5W)
#define DIVIDER_RATIO (VOLTAGE_DIVIDER_R2 / (VOLTAGE_DIVIDER_R1 + VOLTAGE_DIVIDER_R2))

// Arduino'da ölçülen voltaj aralığı (voltaj bölücü sonrası)
#define VOLT_MIN 0.66                // V (4mA × 650Ω × 0.253)
#define VOLT_MAX 3.30                // V (20mA × 650Ω × 0.253)

// Sensör ölçüm aralıkları (CJX-HT1420DXSA default)
#define TEMP_MIN -30.0               // °C
#define TEMP_MAX 110.0               // °C
#define HUM_MIN 0.0                  // %RH
#define HUM_MAX 100.0                // %RH

// ADC referansı
#define ADC_VREF 5.0                 // Arduino referans voltajı
#define ADC_RESOLUTION 1023.0        // 10-bit ADC

Servo servoKapi;

// ==================== GLOBAL DEĞİŞKENLER ====================
unsigned long sonVeriGonderme = 0;
unsigned long sonKomutAlma = 0;
unsigned long baslamaSuresi = 0;
const unsigned long VERI_GONDERME_ARALIGI = 5000;

// Filtre için örnekleme
#define SAMPLE_COUNT 10
float tempSamples[3][SAMPLE_COUNT];
float humSamples[3][SAMPLE_COUNT];
int sampleIndex = 0;

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
  float sicaklikRaw;        // Arduino voltajı
  float nemRaw;             // Arduino voltajı
  float sicaklikShunt;      // Şönt voltajı (debug)
  float nemShunt;           // Şönt voltajı (debug)
  float sicaklikAkim;       // Akım (debug)
  float nemAkim;            // Akım (debug)
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
  
  // Analog referansı ayarla
  analogReference(DEFAULT);  // 5V referans
  
  // Analog pinleri input olarak ayarla
  pinMode(TEMP1_PIN, INPUT);
  pinMode(TEMP2_PIN, INPUT);
  pinMode(TEMP3_PIN, INPUT);
  pinMode(HUM1_PIN, INPUT);
  pinMode(HUM2_PIN, INPUT);
  pinMode(HUM3_PIN, INPUT);
  
  // Röle pinleri
  pinMode(LED1_PIN, OUTPUT);
  pinMode(LED2_PIN, OUTPUT);
  pinMode(LED3_PIN, OUTPUT);
  pinMode(FAN1_PIN, OUTPUT);
  pinMode(FAN2_PIN, OUTPUT);
  pinMode(FAN3_PIN, OUTPUT);
  pinMode(POMPA_PIN, OUTPUT);
  pinMode(YEDEK_PIN, OUTPUT);
  
  // Röleler başlangıçta kapalı (HIGH = kapalı, LOW = açık)
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
  
  // Filtre dizilerini sıfırla
  for (int i = 0; i < 3; i++) {
    for (int j = 0; j < SAMPLE_COUNT; j++) {
      tempSamples[i][j] = 0.0;
      humSamples[i][j] = 0.0;
    }
  }
  
  baslamaSuresi = millis();
  sonKomutAlma = millis();
  
  Serial.println("🐔 Kümes Otomasyon Başlatıldı");
  Serial.println("📡 Sensör: CJX-HT1420DXSA (28V, 4-20mA)");
  Serial.print("✅ Şönt direnci: ");
  Serial.print(SHUNT_RESISTOR);
  Serial.println("Ω (2W)");
  Serial.print("✅ Voltaj bölücü: ");
  Serial.print(VOLTAGE_DIVIDER_R2);
  Serial.println("Ω (0.5W)");
  Serial.print("✅ Bölücü oranı: ");
  Serial.println(DIVIDER_RATIO, 3);
  Serial.print("✅ Arduino voltaj aralığı: ");
  Serial.print(VOLT_MIN);
  Serial.print("V - ");
  Serial.print(VOLT_MAX);
  Serial.println("V");
  Serial.println("⚠️ UYARI: Voltaj bölücü olmadan BAĞLAMAYIN!");
  Serial.print("✅ Otomatik mod timeout: ");
  Serial.print(otoAyar.timeout / 1000);
  Serial.println(" saniye");
  ayarlariYazdir();
  
  delay(2000);
  
  // İlk kalibrasyon okuması
  Serial.println("\n🔧 Sensör kalibrasyonu yapılıyor...");
  for (int i = 0; i < 20; i++) {
    sensorOku();
    delay(100);
  }
  Serial.println("✅ Kalibrasyon tamamlandı\n");
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

// ==================== 4-20mA SENSÖR OKUMA (650Ω ŞÖNT) ====================
float okuAnalogVoltaj(int pin) {
  // Çoklu okuma ile gürültüyü azalt
  long toplam = 0;
  for (int i = 0; i < 10; i++) {
    toplam += analogRead(pin);
    delayMicroseconds(100);
  }
  int ortalama = toplam / 10;
  
  // ADC değerini voltaja çevir (Arduino'da ölçülen)
  float arduino_voltaj = (ortalama / ADC_RESOLUTION) * ADC_VREF;
  return arduino_voltaj;
}

float arduinoVoltajToShuntVoltaj(float arduino_voltaj) {
  // Voltaj bölücüden gerçek şönt voltajını hesapla
  // V_shunt = V_arduino / (R2 / (R1 + R2))
  float shunt_voltaj = arduino_voltaj / DIVIDER_RATIO;
  return shunt_voltaj;
}

float shuntVoltajToAkim(float shunt_voltaj) {
  // Ohm kanunu: I = V / R
  float akim = (shunt_voltaj / SHUNT_RESISTOR) * 1000.0; // mA cinsinden
  return akim;
}

float akimToSicaklik(float akim) {
  // 4-20mA → -30°C ile 110°C arası lineer dönüşüm
  if (akim < 3.5) return TEMP_MIN; // Sensör hatası
  if (akim > 20.5) return TEMP_MAX; // Aşırı değer
  
  float sicaklik = map_float(akim, CURRENT_MIN, CURRENT_MAX, TEMP_MIN, TEMP_MAX);
  return sicaklik;
}

float akimToNem(float akim) {
  // 4-20mA → 0-100% RH arası lineer dönüşüm
  if (akim < 3.5) return 0.0; // Sensör hatası
  if (akim > 20.5) return 100.0; // Aşırı değer
  
  float nem = map_float(akim, CURRENT_MIN, CURRENT_MAX, HUM_MIN, HUM_MAX);
  return nem;
}

// Float map fonksiyonu
float map_float(float x, float in_min, float in_max, float out_min, float out_max) {
  return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
}

// Hareketli ortalama filtresi
float movingAverage(float samples[], int count) {
  float toplam = 0.0;
  for (int i = 0; i < count; i++) {
    toplam += samples[i];
  }
  return toplam / count;
}

void sensorOku() {
  // Her sensörü oku ve filtrele
  for (int i = 0; i < 3; i++) {
    // ======== SICAKLIK OKUMA ========
    int tempPin = TEMP1_PIN + i;
    
    // 1. Arduino voltajını oku
    float tempArduinoVolt = okuAnalogVoltaj(tempPin);
    
    // 2. Gerçek şönt voltajını hesapla
    float tempShuntVolt = arduinoVoltajToShuntVoltaj(tempArduinoVolt);
    
    // 3. Akımı hesapla
    float tempAkim = shuntVoltajToAkim(tempShuntVolt);
    
    // 4. Sıcaklığa çevir
    float tempDegeri = akimToSicaklik(tempAkim);
    
    // ======== NEM OKUMA ========
    int humPin = HUM1_PIN + i;
    
    float humArduinoVolt = okuAnalogVoltaj(humPin);
    float humShuntVolt = arduinoVoltajToShuntVoltaj(humArduinoVolt);
    float humAkim = shuntVoltajToAkim(humShuntVolt);
    float humDegeri = akimToNem(humAkim);
    
    // Filtre dizisine ekle
    tempSamples[i][sampleIndex] = tempDegeri;
    humSamples[i][sampleIndex] = humDegeri;
    
    // Hareketli ortalama hesapla
    kumes[i].sicaklik = movingAverage(tempSamples[i], SAMPLE_COUNT);
    kumes[i].nem = movingAverage(humSamples[i], SAMPLE_COUNT);
    
    // Ham değerleri kaydet (debug için)
    kumes[i].sicaklikRaw = tempArduinoVolt;
    kumes[i].nemRaw = humArduinoVolt;
    kumes[i].sicaklikShunt = tempShuntVolt;
    kumes[i].nemShunt = humShuntVolt;
    kumes[i].sicaklikAkim = tempAkim;
    kumes[i].nemAkim = humAkim;
    
    // Sınır kontrolü
    if (kumes[i].sicaklik < TEMP_MIN - 10 || kumes[i].sicaklik > TEMP_MAX + 10) {
      kumes[i].sicaklik = 0.0; // Hata
    }
    if (kumes[i].nem < -5 || kumes[i].nem > 105) {
      kumes[i].nem = 0.0; // Hata
    }
  }
  
  // Örnek indeksini güncelle
  sampleIndex = (sampleIndex + 1) % SAMPLE_COUNT;
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
    
    // Sensör hatası kontrolü
    if (kumes[i].sicaklik == 0.0 && kumes[i].nem == 0.0) {
      kumes[i].alarm = true;
      kumes[i].alarmMesaj = "Sensör hatası!";
    }
    
    // Düşük voltaj hatası (bağlantı kopuk)
    if (kumes[i].sicaklikRaw < 0.5 || kumes[i].nemRaw < 0.5) {
      kumes[i].alarm = true;
      kumes[i].alarmMesaj = "Sensör bağlantı hatası!";
    }
    
    // Yüksek voltaj uyarısı (voltaj bölücü arızası)
    if (kumes[i].sicaklikRaw > 3.5 || kumes[i].nemRaw > 3.5) {
      kumes[i].alarm = true;
      kumes[i].alarmMesaj = "Voltaj bölücü arızası! Arduino risk altında!";
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
  doc["sensor_tip"] = "CJX-HT1420DXSA";
  doc["sensor_protokol"] = "4-20mA";
  doc["sensor_sunt"] = "650ohm";
  doc["sensor_bolcu"] = "220ohm";
  
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
    k["sicaklik"] = round(kumes[i].sicaklik * 10) / 10.0;  // 1 ondalık
    k["nem"] = round(kumes[i].nem * 10) / 10.0;
    
    // Debug bilgileri (geliştirme için)
    JsonObject debug = k.createNestedObject("debug");
    debug["arduino_v_temp"] = round(kumes[i].sicaklikRaw * 100) / 100.0;
    debug["arduino_v_hum"] = round(kumes[i].nemRaw * 100) / 100.0;
    debug["shunt_v_temp"] = round(kumes[i].sicaklikShunt * 100) / 100.0;
    debug["shunt_v_hum"] = round(kumes[i].nemShunt * 100) / 100.0;
    debug["akim_temp_ma"] = round(kumes[i].sicaklikAkim * 10) / 10.0;
    debug["akim_hum_ma"] = round(kumes[i].nemAkim * 10) / 10.0;
    
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
  
  // Serial Monitor Debug Çıktısı
  Serial.println("\n========== SENSOR DATA ==========");
  serializeJsonPretty(doc, Serial);
  Serial.println("\n=================================\n");
}

// ==================== KOMUT İŞLEME ve DİĞER FONKSİYONLAR ====================
// (Önceki kodla aynı - komutKontrol, komutIsle, ayarKomutIsle, vb.)

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

void komutIsle(String komut) {
  Serial.print("📥 Komut: ");
  Serial.println(komut);
  
  if (komut.startsWith("LED:")) {
    bool durum = komut.substring(4).toInt() == 1;
    ledKontrol(durum);
    Serial1.println("OK:LED");
  }
  else if (komut.startsWith("FAN")) {
    int fanNo = komut.charAt(3) - '0';
    bool durum = komut.substring(5).toInt() == 1;
    fanKontrol(fanNo, durum);
    Serial1.println("OK:FAN" + String(fanNo));
  }
  else if (komut.startsWith("POMPA:")) {
    pompa = komut.substring(6).toInt() == 1;
    digitalWrite(POMPA_PIN, pompa ? LOW : HIGH);
    Serial1.println("OK:POMPA");
  }
  else if (komut.startsWith("KAPI:")) {
    kapiAcisi = komut.substring(5).toInt();
    kapiAcisi = constrain(kapiAcisi, 0, 180);
    servoKapi.write(kapiAcisi);
    Serial1.println("OK:KAPI");
  }
  else if (komut.startsWith("YEM:")) {
    yemSuresi = komut.substring(4).toInt();
    yemDagit(yemSuresi);
    Serial1.println("OK:YEM");
  }
  else if (komut == "STATUS") {
    veriGonder();
  }
  else if (komut == "KALIBRASYON") {
    Serial.println("🔧 Sensör kalibrasyonu başlatılıyor...");
    for (int i = 0; i < 50; i++) {
      sensorOku();
      delay(100);
    }
    Serial.println("✅ Kalibrasyon tamamlandı");
    Serial1.println("OK:KALIBRASYON");
  }
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
  else if (komut.startsWith("AYAR:")) {
    ayarKomutIsle(komut.substring(5));
  }
  else if (komut == "AYAR?") {
    ayarlariGonder();
  }
  else if (komut == "AYAR:RESET") {
    ayarlariSifirla();
    Serial1.println("OK:RESET");
  }
  else {
    Serial.println("❌ Bilinmeyen komut!");
    Serial1.println("ERROR:UNKNOWN");
  }
}

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
    otoAyar.timeout = doc["timeout"].as<unsigned long>() * 1000;
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

void ledKontrol(bool durum) {
  digitalWrite(LED1_PIN, durum ? LOW : HIGH);
  digitalWrite(LED2_PIN, durum ? LOW : HIGH);
  digitalWrite(LED3_PIN, durum ? LOW : HIGH);
  
  kumes[0].led = durum;
  kumes[1].led = durum;
  kumes[2].led = durum;
}

void fanKontrol(int fanNo, bool durum) {
  if (fanNo < 1 || fanNo > 3) return;
  
  int pin = FAN1_PIN + (fanNo - 1);
  digitalWrite(pin, durum ? LOW : HIGH);
  
  kumes[fanNo - 1].fan = durum;
}

void yemDagit(int sure) {
  Serial.print("🌾 Yem dağıtılıyor: ");
  Serial.print(sure);
  Serial.println(" saniye");
  
  digitalWrite(YEDEK_PIN, LOW);
  delay(sure * 1000);
  digitalWrite(YEDEK_PIN, HIGH);
  
  Serial.println("✅ Yem dağıtma tamamlandı");
}
