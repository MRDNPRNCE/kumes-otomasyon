# 🖼️ MASAÜSTÜ UYGULAMASI GÖRÜNÜM REHBERİ

## 📱 UYGULAMA EKRAN YAPISI

Bu dosya, masaüstü uygulamasının nasıl göründüğünü ve nasıl çalıştığını adım adım açıklar.

---

## 🎯 ADIM 1: Basit Pencere

**Dosya:** `adim_01_basit_pencere.py`

```
┌────────────────────────────────────────────┐
│  🏠 Kümes Otomasyon Sistemi               │
├────────────────────────────────────────────┤
│                                            │
│                                            │
│                                            │
│     Kümes Otomasyon Sistemi Başlatıldı!  │
│                                            │
│                                            │
│                                            │
└────────────────────────────────────────────┘
```

**Ne Öğrendik:**
- PyQt6 ile temel pencere oluşturma
- QMainWindow kullanımı
- Dark tema ayarlama
- Pencere başlığı ve boyut ayarları

**Çalıştırma:**
```bash
python adim_01_basit_pencere.py
```

---

## 🎯 ADIM 2: Sol ve Sağ Panel Layout

**Dosya:** `adim_02_sol_sag_panel.py`

```
┌────────────────────────────────────────────────────────┐
│  🏠 Kümes Otomasyon Sistemi                           │
├──────────────────┬─────────────────────────────────────┤
│                  │                                     │
│  📋 KÜMES        │      📊 DETAY GÖRÜNÜMÜ             │
│    LİSTESİ       │                                     │
│                  │                                     │
│                  │                                     │
│                  │                                     │
│   (Sol Panel)    │      (Sağ Panel)                   │
│                  │                                     │
│                  │                                     │
│                  │                                     │
└──────────────────┴─────────────────────────────────────┘
```

**Ne Öğrendik:**
- QHBoxLayout ile yatay bölme
- QVBoxLayout ile dikey düzenleme
- Panel genişlik oranları (stretch)
- Widget styling ve border

**Çalıştırma:**
```bash
python adim_02_sol_sag_panel.py
```

---

## 🎯 ADIM 3: Kümes Kartları

**Dosya:** `adim_03_kumes_kartlari.py`

```
┌─────────────────────────────────────────────────────────┐
│  🏠 Kümes Otomasyon Sistemi                            │
├──────────────────┬──────────────────────────────────────┤
│                  │                                      │
│ 📋 KÜMES LİSTESİ │                                      │
│                  │   👈 Sol taraftan bir kümes seçin   │
│ ┌────────────┐   │                                      │
│ │ 🏠         │   │                                      │
│ │ Ana Kümes  │   │                                      │
│ │ 24.5°C     │   │                                      │
│ │ 🐔 120     │   │                                      │
│ │ 📅 180     │   │                                      │
│ │ ● Normal   │   │                                      │
│ └────────────┘   │                                      │
│                  │                                      │
│ ┌────────────┐   │                                      │
│ │ 🐣         │   │                                      │
│ │ Yavru      │   │                                      │
│ │ 22.1°C     │   │                                      │
│ │ 🐔 85      │   │                                      │
│ │ 📅 45      │   │                                      │
│ │ ● Normal   │   │                                      │
│ └────────────┘   │                                      │
│                  │                                      │
│ ┌────────────┐   │                                      │
│ │ 🏡         │   │                                      │
│ │ Misafir    │   │                                      │
│ │ 25.8°C     │   │                                      │
│ │ 🐔 50      │   │                                      │
│ │ 📅 90      │   │                                      │
│ │ ● Normal   │   │                                      │
│ └────────────┘   │                                      │
└──────────────────┴──────────────────────────────────────┘
```

**Ne Öğrendik:**
- QFrame ile kart oluşturma
- QGridLayout ile ızgara düzeni
- Hover efektleri (CSS)
- Mouse olayları (mousePressEvent)
- Dinamik widget oluşturma

**Özellikler:**
- ✅ 3 kümes kartı
- ✅ İkon, isim, sıcaklık, tavuk sayısı, günlük
- ✅ Hover efekti (mavi kenarlık)
- ✅ Tıklanabilir kartlar
- ✅ Konsola mesaj yazdırma

**Çalıştırma:**
```bash
python adim_03_kumes_kartlari.py
```

---

## 🎯 ADIM 4: Sekmeli Sağ Panel

**Dosya:** `adim_04_sekmeler.py`

```
┌──────────────────────────────────────────────────────────────────┐
│  🏠 Kümes Otomasyon Sistemi                                     │
├──────────────────┬───────────────────────────────────────────────┤
│                  │ [📊 Kümes Detay] [🎮 Kontrol] [⚠️ Alarmlar]  │
│                  │ [⚙️ Ayarlar]                                  │
│ 📋 KÜMES LİSTESİ ├───────────────────────────────────────────────┤
│                  │                                               │
│ ┌────────────┐   │    SEKME 1: KÜMES DETAY                      │
│ │ 🏠         │   │                                               │
│ │ Ana Kümes  │   │    👈 Sol taraftan bir kümes seçin          │
│ │ 24.5°C     │   │                                               │
│ │ 🐔 120     │   │    Burada seçilen kümesin:                   │
│ │ 📅 180     │   │    - Sensör grafikleri                       │
│ │ ● Normal   │   │    - Detaylı bilgiler                        │
│ └────────────┘   │    - Kontrol butonları                       │
│                  │    gösterilecek                               │
│ ┌────────────┐   │                                               │
│ │ 🐣         │   │                                               │
│ │ Yavru      │   │                                               │
│ │ 22.1°C     │   │                                               │
│ └────────────┘   │                                               │
│                  │                                               │
│ ┌────────────┐   │                                               │
│ │ 🏡         │   │                                               │
│ │ Misafir    │   │                                               │
│ └────────────┘   │                                               │
└──────────────────┴───────────────────────────────────────────────┘
```

**Ne Öğrendik:**
- QTabWidget kullanımı
- Sekme stilleri (QSS)
- Sekmeler arası geçiş
- Her sekme için ayrı widget

**4 Sekme:**
1. 📊 **Kümes Detay** - Seçilen kümesin detayları
2. 🎮 **Kontrol** - Manuel kontrol paneli
3. ⚠️ **Alarmlar** - Aktif alarm listesi
4. ⚙️ **Ayarlar** - Sistem ayarları

**Çalıştırma:**
```bash
python adim_04_sekmeler.py
```

---

## 🎨 GÖRSEL TEMA DETAYLARI

### Renkler
```css
Arka Plan:     #0d1117 (Koyu gri-mavi)
Panel:         #161b22 (Panel arka plan)
Kenarlık:      #30363d (Açık gri)
Vurgu:         #58a6ff (Mavi)
Seçili:        #1f6feb (Koyu mavi)
Başarı:        #48bb78 (Yeşil)
Hata:          #ff4444 (Kırmızı)
Sıcaklık:      #f85149 (Turuncu-kırmızı)
Bilgi:         #9ae6b4 (Açık yeşil)
```

### Fontlar
```
Başlık:   Segoe UI, 16px, Bold
Kart Ad:  Segoe UI, 12px, Bold
Sıcaklık: Segoe UI, 11px
Bilgi:    Segoe UI, 9px
```

### Boyutlar
```
Pencere:     1400 x 800 px
Sol Panel:   400 px genişlik
Kart:        180 x 220 px
Kenarlık:    3 px (normal), hover'da mavi
Yuvarlaklık: 15 px (kartlar), 12 px (paneller)
```

---

## 🔄 UYGULAMA AKIŞI

### 1. Başlangıç
```
Kullanıcı uygulamayı açar
    ↓
Ana pencere açılır (1400x800)
    ↓
Sol panelde 3 kümes kartı gösterilir
    ↓
Sağ panelde "Bir kümes seçin" mesajı
```

### 2. Kümes Seçimi
```
Kullanıcı bir kümes kartına tıklar
    ↓
Kart mavi kenarlık alır (seçili)
    ↓
Sağ panelde o kümesin detayları gösterilir
    ↓
Grafikler ve sensör verileri yüklenir
```

### 3. Sekme Değiştirme
```
Kullanıcı bir sekmeye tıklar
    ↓
Sekme aktif olur (mavi arka plan)
    ↓
İçerik değişir (Detay/Kontrol/Alarmlar/Ayarlar)
```

### 4. Manuel Kontrol
```
Kullanıcı "Kontrol" sekmesine geçer
    ↓
Fan, LED, Pompa butonları gösterilir
    ↓
Butona tıklandığında komut gönderilir
    ↓
ESP32'ye WebSocket ile komut iletilir
```

---

## 📊 SONRAKI ADIMLAR

### Adım 5: Kümes Detay Ekranı
- Sensör kartları
- Gerçek zamanlı grafikler
- Buton kontrolleri

### Adım 6: Kontrol Paneli
- Fan kontrol butonları
- LED aydınlatma
- Pompa kontrolü
- Kapı servo kontrolü
- Yem dağıtıcı

### Adım 7: WebSocket Bağlantısı
- ESP32'ye bağlanma
- Gerçek zamanlı veri alımı
- Komut gönderme
- Otomatik yeniden bağlanma

### Adım 8: Alarm Sistemi
- Alarm tespit
- Görsel uyarı
- Alarm geçmişi
- Alarm temizleme

### Adım 9: Veritabanı
- SQLite entegrasyonu
- Veri kayıt
- Geçmiş sorgulama
- Yedekleme

### Adım 10: Sistem Durumu Paneli
- Çalışma süresi
- Ortalama değerler
- Bağlantı durumu
- Sistem metrikleri

---

## 💡 KULLANIM İPUÇLARI

### Geliştirme İçin
1. Her dosya bağımsız çalışır
2. Adım adım test edebilirsiniz
3. Kodları değiştirerek öğrenin
4. Hata mesajlarını okuyun

### Test İçin
```bash
# Tüm adımları sırayla test et
python adim_01_basit_pencere.py
python adim_02_sol_sag_panel.py
python adim_03_kumes_kartlari.py
python adim_04_sekmeler.py
```

### Özelleştirme
- Renkleri değiştirebilirsiniz (QSS)
- Font boyutlarını ayarlayabilirsiniz
- Kümes sayısını artırabilirsiniz
- Yeni sekmeler ekleyebilirsiniz

---

## 🎓 ÖĞRENME ÇIKTILARI

Bu 4 adımı tamamladıktan sonra:

✅ PyQt6 temellerini öğrendiniz
✅ Layout sistemini anladınız
✅ Widget'ları özelleştirmeyi öğrendiniz
✅ Olay yönetimini kavradınız
✅ Sekmeli arayüz oluşturabilirsiniz
✅ Profesyonel bir UI tasarımı yapabilirsiniz

---

## 📞 YARDIM

Sorun yaşarsanız:
1. Konsol çıktısını kontrol edin
2. PyQt6'nın kurulu olduğundan emin olun
3. Python 3.11+ kullanın
4. Dosya yollarını kontrol edin

---

**Hazırlayan:** AI Geliştirme Asistanı
**Tarih:** 20 Ocak 2026
**Durum:** Tamamlandı ✅
