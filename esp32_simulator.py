"""
🚀 ESP32 WebSocket Simülatörü - GELİŞMİŞ VERSİYON
- Otomatik mod: Sensörler ve alarmlar otomatik çalışır
- Manuel mod: Terminal'den komut girebilirsiniz
- Gerçek zamanlı veri gönderimi
- Alarm simülasyonu
- Kümes bilgileri düzenleme testi
"""

import asyncio
import websockets
import json
import random
import time
from datetime import datetime
import sys
import threading

# =============================================================================
# SUNUCU AYARLARI
# =============================================================================
SERVER_IP = "127.0.0.1"  # localhost
SERVER_PORT = 81
UPDATE_INTERVAL = 2  # Saniye
AUTO_MODE = True  # Otomatik mod (False yaparsanız sadece manuel)

# =============================================================================
# BAŞLANGIÇ DURUMU
# =============================================================================
state = {
    "sistem": "kumes",
    "kumesler": [
        {
            "id": 1,
            "sicaklik": 24.5,
            "nem": 55.0,
            "amonyak": 8.0,
            "su": 1500,
            "isik": 450,
            "fan": False,
            "led": True,
            "kapi": False,
            "alarm": False,
            "mesaj": ""
        },
        {
            "id": 2,
            "sicaklik": 32.8,  # Yüksek - alarm tetiklenecek
            "nem": 62.0,
            "amonyak": 12.0,
            "su": 1200,
            "isik": 380,
            "fan": False,
            "led": False,
            "kapi": False,
            "alarm": True,
            "mesaj": "Yüksek sıcaklık tespit edildi!"
        },
        {
            "id": 3,
            "sicaklik": 25.8,
            "nem": 58.0,
            "amonyak": 10.0,
            "su": 1800,
            "isik": 520,
            "fan": True,
            "led": False,
            "kapi": False,
            "alarm": False,
            "mesaj": ""
        }
    ],
    "zaman": int(time.time()),
    "yem": 45,
    "pompa": False,
    "sistem_durumu": "OK",
    "uptime": 0
}

# Aktif bağlantılar
connected_clients = set()
simulation_running = True

# =============================================================================
# KOMUT İŞLEME
# =============================================================================
def process_command(cmd_str):
    """
    İstemciden veya konsoldan gelen komutu işler
    
    Args:
        cmd_str: JSON komut string'i
        
    Returns:
        Dict: Yanıt mesajı
    """
    try:
        cmd = json.loads(cmd_str)
        action = cmd.get("action")
        kumes_id = cmd.get("kumes")
        
        if action == "get_status":
            return {"status": "success", "message": "Durum bilgisi gönderiliyor"}
        
        # Kümes ID kontrolü
        if kumes_id and (kumes_id < 1 or kumes_id > len(state["kumesler"])):
            return {"status": "error", "message": f"Geçersiz kümes ID: {kumes_id}"}
        
        kumes_idx = kumes_id - 1 if kumes_id else None
        
        # =====================================================================
        # LED KONTROLLERI
        # =====================================================================
        if action == "led_on":
            if kumes_id:
                state["kumesler"][kumes_idx]["led"] = True
                msg = f"✅ Kümes {kumes_id} LED açıldı"
            else:
                for k in state["kumesler"]:
                    k["led"] = True
                msg = "✅ Tüm LED'ler açıldı"
            return {"status": "success", "message": msg}
        
        elif action == "led_off":
            if kumes_id:
                state["kumesler"][kumes_idx]["led"] = False
                msg = f"❌ Kümes {kumes_id} LED kapatıldı"
            else:
                for k in state["kumesler"]:
                    k["led"] = False
                msg = "❌ Tüm LED'ler kapatıldı"
            return {"status": "success", "message": msg}
        
        # =====================================================================
        # FAN KONTROLLERI
        # =====================================================================
        elif action == "fan_on":
            if kumes_id:
                state["kumesler"][kumes_idx]["fan"] = True
                msg = f"🌀 Kümes {kumes_id} fan açıldı"
            else:
                for k in state["kumesler"]:
                    k["fan"] = True
                msg = "🌀 Tüm fanlar açıldı"
            return {"status": "success", "message": msg}
        
        elif action == "fan_off":
            if kumes_id:
                state["kumesler"][kumes_idx]["fan"] = False
                msg = f"⏸️ Kümes {kumes_id} fan kapatıldı"
            else:
                for k in state["kumesler"]:
                    k["fan"] = False
                msg = "⏸️ Tüm fanlar kapatıldı"
            return {"status": "success", "message": msg}
        
        # =====================================================================
        # KAPI KONTROLLERI
        # =====================================================================
        elif action == "door_open":
            state["kumesler"][kumes_idx]["kapi"] = True
            return {"status": "success", "message": f"🚪 Kümes {kumes_id} kapısı açıldı"}
        
        elif action == "door_close":
            state["kumesler"][kumes_idx]["kapi"] = False
            return {"status": "success", "message": f"🔒 Kümes {kumes_id} kapısı kapatıldı"}
        
        # =====================================================================
        # POMPA KONTROLLERI
        # =====================================================================
        elif action == "pump_on":
            state["pompa"] = True
            return {"status": "success", "message": "💧 Pompa açıldı"}
        
        elif action == "pump_off":
            state["pompa"] = False
            return {"status": "success", "message": "💧 Pompa kapatıldı"}
        
        # =====================================================================
        # ALARM KONTROLLERI
        # =====================================================================
        elif action == "reset_alarms":
            for k in state["kumesler"]:
                k["alarm"] = False
                k["mesaj"] = ""
            return {"status": "success", "message": "✅ Tüm alarmlar sıfırlandı"}
        
        elif action == "trigger_alarm":
            if kumes_id:
                state["kumesler"][kumes_idx]["alarm"] = True
                state["kumesler"][kumes_idx]["mesaj"] = cmd.get("mesaj", "Test alarmı!")
                return {"status": "success", "message": f"⚠️ Kümes {kumes_id} alarm tetiklendi"}
            return {"status": "error", "message": "Kümes ID gerekli"}
        
        # =====================================================================
        # SICAKLIK AYARLAMA (TEST İÇİN)
        # =====================================================================
        elif action == "set_temp":
            if kumes_id:
                temp = cmd.get("value", 25.0)
                state["kumesler"][kumes_idx]["sicaklik"] = temp
                return {"status": "success", "message": f"🌡️ Kümes {kumes_id} sıcaklık: {temp}°C"}
            return {"status": "error", "message": "Kümes ID ve value gerekli"}
        
        elif action == "set_humidity":
            if kumes_id:
                hum = cmd.get("value", 60.0)
                state["kumesler"][kumes_idx]["nem"] = hum
                return {"status": "success", "message": f"💧 Kümes {kumes_id} nem: {hum}%"}
            return {"status": "error", "message": "Kümes ID ve value gerekli"}
        
        return {"status": "error", "message": f"❌ Bilinmeyen aksiyon: {action}"}
        
    except json.JSONDecodeError as e:
        return {"status": "error", "message": f"JSON parse hatası: {str(e)}"}
    except Exception as e:
        return {"status": "error", "message": f"Komut hatası: {str(e)}"}

# =============================================================================
# SİMÜLASYON
# =============================================================================
def simulate_sensor_changes():
    """Sensör değerlerinde gerçekçi değişimler simüle eder"""
    for kumes in state["kumesler"]:
        kumes_id = kumes["id"]
        
        # Sıcaklık değişimi (daha gerçekçi)
        base_temp = kumes["sicaklik"]
        change = random.uniform(-0.3, 0.3)
        
        # Fan açıksa sıcaklık düşer
        if kumes["fan"]:
            change -= 0.2
        
        kumes["sicaklik"] = round(max(18.0, min(38.0, base_temp + change)), 1)
        
        # Nem değişimi
        kumes["nem"] += random.uniform(-1.5, 1.5)
        kumes["nem"] = round(max(35.0, min(85.0, kumes["nem"])), 1)
        
        # Amonyak değişimi
        kumes["amonyak"] += random.uniform(-0.8, 0.8)
        kumes["amonyak"] = round(max(0.0, min(50.0, kumes["amonyak"])), 1)
        
        # Su seviyesi azalması (tavuklar içiyor)
        if random.random() < 0.15:
            kumes["su"] = max(0, kumes["su"] - random.randint(10, 30))
        
        # Işık seviyesi (gündüz/gece)
        hour = datetime.now().hour
        if 6 <= hour <= 18:
            # LED açıksa daha parlak
            if kumes["led"]:
                kumes["isik"] = random.randint(600, 900)
            else:
                kumes["isik"] = random.randint(400, 700)
        else:
            if kumes["led"]:
                kumes["isik"] = random.randint(300, 500)
            else:
                kumes["isik"] = random.randint(20, 100)
        
        # Alarm kontrolü (otomatik)
        if AUTO_MODE:
            # Yüksek sıcaklık
            if kumes["sicaklik"] > 32:
                kumes["alarm"] = True
                kumes["mesaj"] = f"⚠️ Yüksek sıcaklık: {kumes['sicaklik']}°C"
            # Düşük su
            elif kumes["su"] < 300:
                kumes["alarm"] = True
                kumes["mesaj"] = f"⚠️ Düşük su seviyesi: {kumes['su']}ml"
            # Yüksek amonyak
            elif kumes["amonyak"] > 35:
                kumes["alarm"] = True
                kumes["mesaj"] = f"⚠️ Yüksek amonyak: {kumes['amonyak']} ppm"
            # Normal durumda alarm kapalı
            else:
                # Fan açıksa sıcaklık normale dönüyor, alarmı kapat
                if kumes["fan"] and kumes["sicaklik"] < 28:
                    kumes["alarm"] = False
                    kumes["mesaj"] = ""
    
    # Yem seviyesi azalması
    if random.random() < 0.08:
        state["yem"] = max(0, state["yem"] - 1)
    
    # Uptime güncelleme
    state["uptime"] += UPDATE_INTERVAL
    state["zaman"] = int(time.time())

# =============================================================================
# WEBSOCKET İŞLEYİCİ
# =============================================================================
async def handle_client(websocket):
    """Tek bir istemci bağlantısını yönetir"""
    client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"\n[{timestamp}] ✅ YENİ BAĞLANTI: {client_id}")
    connected_clients.add(websocket)
    print(f"   👥 Aktif bağlantı sayısı: {len(connected_clients)}")
    
    # Otomatik veri gönderme
    async def send_periodic_updates():
        """Belirli aralıklarla güncel veri gönderir"""
        try:
            while simulation_running:
                if AUTO_MODE:
                    simulate_sensor_changes()
                await websocket.send(json.dumps(state))
                await asyncio.sleep(UPDATE_INTERVAL)
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            print(f"❌ Veri gönderme hatası: {e}")
    
    # Arka planda veri gönder
    update_task = asyncio.create_task(send_periodic_updates())
    
    try:
        # İlk durumu gönder
        await websocket.send(json.dumps(state))
        print(f"[{timestamp}] 📤 İlk durum gönderildi")
        
        # Komutları dinle
        async for message in websocket:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"\n[{timestamp}] 📥 KOMUT ALINDI:")
            print(f"   {message}")
            
            response = process_command(message)
            
            # Durumu gönder
            await websocket.send(json.dumps(state))
            
            # Sonuç
            status_icon = "✅" if response.get("status") == "success" else "❌"
            print(f"[{timestamp}] {status_icon} {response.get('message')}")
    
    except websockets.exceptions.ConnectionClosed:
        print(f"\n⚠️  Bağlantı kapatıldı: {client_id}")
    except Exception as e:
        print(f"\n❌ İstemci hatası ({client_id}): {e}")
    finally:
        update_task.cancel()
        connected_clients.discard(websocket)
        print(f"❌ Bağlantı sonlandı: {client_id}")
        print(f"   👥 Kalan bağlantı: {len(connected_clients)}\n")

# =============================================================================
# MANUEL KONSOL KONTROLÜ
# =============================================================================
def console_input_handler():
    """Konsoldan komut girişi için thread"""
    print("\n" + "="*70)
    print("💡 MANUEL KONTROL KOMUTLARI:")
    print("="*70)
    print("ALARM:")
    print("  alarm 2        - Kümes 2'de alarm tetikle")
    print("  clear          - Tüm alarmları temizle")
    print("\nKONTROL:")
    print("  led 1 on       - Kümes 1 LED'i aç")
    print("  fan 2 off      - Kümes 2 fan'ı kapat")
    print("  pump on        - Pompayı aç")
    print("  door 3 open    - Kümes 3 kapısını aç")
    print("\nSENSÖR:")
    print("  temp 1 35      - Kümes 1 sıcaklığı 35°C yap")
    print("  hum 2 70       - Kümes 2 nemi %70 yap")
    print("\nDİĞER:")
    print("  status         - Mevcut durumu göster")
    print("  auto           - Otomatik modu aç/kapat")
    print("  quit / exit    - Sunucuyu kapat")
    print("="*70 + "\n")
    
    global AUTO_MODE, simulation_running
    
    while simulation_running:
        try:
            cmd = input("👉 Komut: ").strip().lower()
            
            if not cmd:
                continue
            
            parts = cmd.split()
            
            # Çıkış
            if cmd in ['quit', 'exit', 'q']:
                print("\n🛑 Sunucu kapatılıyor...")
                simulation_running = False
                break
            
            # Otomatik mod
            elif cmd == 'auto':
                AUTO_MODE = not AUTO_MODE
                print(f"🔄 Otomatik mod: {'AÇIK ✅' if AUTO_MODE else 'KAPALI ❌'}")
                continue
            
            # Durum
            elif cmd == 'status':
                print("\n" + "="*70)
                print("📊 MEVCUT DURUM:")
                print("="*70)
                for k in state["kumesler"]:
                    alarm_icon = "⚠️" if k["alarm"] else "✅"
                    print(f"  Kümes {k['id']}: {k['sicaklik']}°C | {k['nem']}% | {k['su']}ml | {alarm_icon}")
                    if k["alarm"]:
                        print(f"    └─ {k['mesaj']}")
                print(f"  Yem: {state['yem']}cm | Pompa: {'AÇIK' if state['pompa'] else 'KAPALI'}")
                print(f"  Uptime: {state['uptime']}s | Bağlantı: {len(connected_clients)}")
                print("="*70 + "\n")
                continue
            
            # Alarm
            elif parts[0] == 'alarm':
                kumes_id = int(parts[1])
                cmd_json = json.dumps({
                    "action": "trigger_alarm",
                    "kumes": kumes_id,
                    "mesaj": "Manuel test alarmı!"
                })
            
            elif cmd == 'clear':
                cmd_json = json.dumps({"action": "reset_alarms"})
            
            # LED
            elif parts[0] == 'led':
                kumes_id = int(parts[1])
                on_off = parts[2]
                cmd_json = json.dumps({
                    "action": f"led_{on_off}",
                    "kumes": kumes_id
                })
            
            # Fan
            elif parts[0] == 'fan':
                kumes_id = int(parts[1])
                on_off = parts[2]
                cmd_json = json.dumps({
                    "action": f"fan_{on_off}",
                    "kumes": kumes_id
                })
            
            # Pompa
            elif parts[0] == 'pump':
                on_off = parts[1]
                cmd_json = json.dumps({"action": f"pump_{on_off}"})
            
            # Kapı
            elif parts[0] == 'door':
                kumes_id = int(parts[1])
                open_close = parts[2]
                cmd_json = json.dumps({
                    "action": f"door_{open_close}",
                    "kumes": kumes_id
                })
            
            # Sıcaklık
            elif parts[0] == 'temp':
                kumes_id = int(parts[1])
                value = float(parts[2])
                cmd_json = json.dumps({
                    "action": "set_temp",
                    "kumes": kumes_id,
                    "value": value
                })
            
            # Nem
            elif parts[0] == 'hum':
                kumes_id = int(parts[1])
                value = float(parts[2])
                cmd_json = json.dumps({
                    "action": "set_humidity",
                    "kumes": kumes_id,
                    "value": value
                })
            
            else:
                print("❌ Bilinmeyen komut! 'status' yazarak yardım alın.")
                continue
            
            # Komutu işle
            response = process_command(cmd_json)
            status_icon = "✅" if response.get("status") == "success" else "❌"
            print(f"{status_icon} {response.get('message')}")
            
        except (ValueError, IndexError):
            print("❌ Hatalı format! Örnek: alarm 2")
        except Exception as e:
            print(f"❌ Hata: {e}")

# =============================================================================
# ANA SUNUCU
# =============================================================================
async def main():
    """Ana sunucu döngüsü"""
    print("\n" + "🚀 "*35)
    print("="*70)
    print("🏠 ESP32 WEBSOCKET SİMÜLATÖRÜ - GELİŞMİŞ VERSİYON")
    print("="*70)
    print(f"📡 Sunucu     : ws://{SERVER_IP}:{SERVER_PORT}")
    print(f"⏱️  Güncelleme : Her {UPDATE_INTERVAL} saniye")
    print(f"🏠 Kümes      : {len(state['kumesler'])} adet")
    print(f"🤖 Oto. Mod   : {'AÇIK ✅' if AUTO_MODE else 'KAPALI ❌'}")
    print("="*70)
    
    # Başlangıç durumu
    print("\n📊 BAŞLANGIÇ DURUMU:")
    for k in state["kumesler"]:
        alarm_icon = "⚠️" if k["alarm"] else "✅"
        print(f"  Kümes {k['id']}: {k['sicaklik']}°C | {k['nem']}% | {alarm_icon}")
        if k["alarm"]:
            print(f"    └─ {k['mesaj']}")
    
    print("\n⏳ Sunucu başlatılıyor...\n")
    
    # Konsol input thread'i başlat
    input_thread = threading.Thread(target=console_input_handler, daemon=True)
    input_thread.start()
    
    try:
        async with websockets.serve(
            handle_client,
            SERVER_IP,
            SERVER_PORT,
            ping_interval=5,
            ping_timeout=3
        ):
            print(f"✅ SUNUCU HAZIR! Bağlantılar bekleniyor...")
            print(f"💡 Ana uygulamayı başlatın: python main.py\n")
            
            # Sunucu çalışırken bekle
            while simulation_running:
                await asyncio.sleep(0.1)
            
    except OSError as e:
        print(f"\n❌ HATA: Sunucu başlatılamadı!")
        print(f"   Sebep: {e}")
        print(f"\n💡 Çözüm:")
        print(f"   1. Port {SERVER_PORT} zaten kullanımda olabilir")
        print(f"   2. Başka terminal'de simülatör çalışıyor olabilir")
    except Exception as e:
        print(f"\n❌ Beklenmeyen hata: {e}")

# =============================================================================
# GİRİŞ NOKTASI
# =============================================================================
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n" + "="*70)
        print("⏹️  SUNUCU DURDURULDU (Ctrl+C)")
        print(f"📊 Son bağlantı sayısı: {len(connected_clients)}")
        print("="*70)
        simulation_running = False
    except Exception as e:
        print(f"\n❌ Fatal hata: {e}")
    finally:
        print("\n👋 Hoşçakalın!\n")