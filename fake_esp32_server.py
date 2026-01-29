"""
ESP32 WebSocket Simülatörü
Gerçek ESP32 cihazını simüle eden test sunucusu
"""

import asyncio
import websockets
import json
import random
import time
from datetime import datetime
from typing import Dict, Any

# =============================================================================
# SUNUCU AYARLARI
# =============================================================================
SERVER_IP = "192.168.1.107"
SERVER_PORT = 81  # Gerçek ESP32 ile aynı port
UPDATE_INTERVAL = 2  # Saniye

# =============================================================================
# BAŞLANGIÇ DURUMU
# =============================================================================
state: Dict[str, Any] = {
    "kumesler": [
        {
            "id": 1,
            "sicaklik": 22.5,
            "nem": 55.0,
            "amonyak": 15.0,
            "su": 600,
            "isik": 500,
            "fan": False,
            "led": False,
            "kapi": False,
            "alarm": False,
            "mesaj": ""
        },
        {
            "id": 2,
            "sicaklik": 23.0,
            "nem": 60.0,
            "amonyak": 18.0,
            "su": 700,
            "isik": 400,
            "fan": False,
            "led": True,
            "kapi": False,
            "alarm": False,
            "mesaj": ""
        },
        {
            "id": 3,
            "sicaklik": 21.0,
            "nem": 50.0,
            "amonyak": 12.0,
            "su": 800,
            "isik": 600,
            "fan": True,
            "led": False,
            "kapi": False,
            "alarm": False,
            "mesaj": ""
        }
    ],
    "zaman": int(time.time()),
    "yem": 20,
    "pompa": False,
    "sistem_durumu": "OK",
    "uptime": 0
}

# Aktif bağlantılar
connected_clients = set()

# =============================================================================
# KOMUT İŞLEME
# =============================================================================
def update_state_from_command(cmd: str) -> Dict[str, Any]:
    """
    İstemciden gelen komutu işler ve durumu günceller
    
    Args:
        cmd: Komut string'i (eski format) veya JSON
        
    Returns:
        Dict: Yanıt mesajı
    """
    try:
        # JSON komut formatı kontrolü
        if cmd.strip().startswith('{'):
            return process_json_command(cmd)
        
        # Eski string formatı (geriye dönük uyumluluk)
        cmd = cmd.strip()
        
        # FAN komutu: FAN1:1, FAN2:0
        if cmd.startswith("FAN"):
            parts = cmd.split(":")
            fan_id = int(parts[0][3:])  # FAN1 -> 1
            state_val = parts[1] == "1"
            
            if 1 <= fan_id <= len(state["kumesler"]):
                state["kumesler"][fan_id - 1]["fan"] = state_val
                return {
                    "status": "success",
                    "message": f"Kümes {fan_id} fanı {'açıldı' if state_val else 'kapatıldı'}"
                }
        
        # LED komutu: LED:1 (tümü), LED:0 (tümü)
        elif cmd.startswith("LED:"):
            led_state = cmd.endswith("1")
            for k in state["kumesler"]:
                k["led"] = led_state
            return {
                "status": "success",
                "message": f"Tüm LED'ler {'açıldı' if led_state else 'kapatıldı'}"
            }
        
        # POMPA komutu
        elif cmd.startswith("POMPA:"):
            state["pompa"] = cmd.endswith("1")
            return {
                "status": "success",
                "message": f"Pompa {'açıldı' if state['pompa'] else 'kapatıldı'}"
            }
        
        return {"status": "error", "message": f"Bilinmeyen komut: {cmd}"}
        
    except Exception as e:
        print(f"❌ Komut işleme hatası: {e}")
        return {"status": "error", "message": str(e)}

def process_json_command(json_str: str) -> Dict[str, Any]:
    """
    JSON formatındaki komutları işler
    
    Desteklenen komutlar:
    - {"action": "led_on", "kumes": 1}
    - {"action": "fan_off", "kumes": 2}
    - {"action": "door_open", "kumes": 1}
    - {"action": "get_status"}
    """
    try:
        cmd = json.loads(json_str)
        action = cmd.get("action")
        kumes_id = cmd.get("kumes")
        
        # Durum sorgulama
        if action == "get_status":
            return {"status": "success", "data": state}
        
        # Kümes ID kontrolü
        if kumes_id and (kumes_id < 1 or kumes_id > len(state["kumesler"])):
            return {"status": "error", "message": f"Geçersiz kümes ID: {kumes_id}"}
        
        kumes_idx = kumes_id - 1 if kumes_id else None
        
        # LED kontrolleri
        if action == "led_on":
            if kumes_id:
                state["kumesler"][kumes_idx]["led"] = True
                msg = f"Kümes {kumes_id} LED açıldı"
            else:
                for k in state["kumesler"]:
                    k["led"] = True
                msg = "Tüm LED'ler açıldı"
            return {"status": "success", "message": msg}
        
        elif action == "led_off":
            if kumes_id:
                state["kumesler"][kumes_idx]["led"] = False
                msg = f"Kümes {kumes_id} LED kapatıldı"
            else:
                for k in state["kumesler"]:
                    k["led"] = False
                msg = "Tüm LED'ler kapatıldı"
            return {"status": "success", "message": msg}
        
        # FAN kontrolleri
        elif action == "fan_on":
            state["kumesler"][kumes_idx]["fan"] = True
            return {"status": "success", "message": f"Kümes {kumes_id} fan açıldı"}
        
        elif action == "fan_off":
            state["kumesler"][kumes_idx]["fan"] = False
            return {"status": "success", "message": f"Kümes {kumes_id} fan kapatıldı"}
        
        # KAPI kontrolleri
        elif action == "door_open":
            state["kumesler"][kumes_idx]["kapi"] = True
            return {"status": "success", "message": f"Kümes {kumes_id} kapısı açıldı"}
        
        elif action == "door_close":
            state["kumesler"][kumes_idx]["kapi"] = False
            return {"status": "success", "message": f"Kümes {kumes_id} kapısı kapatıldı"}
        
        # POMPA kontrolleri
        elif action == "pump_on":
            state["pompa"] = True
            return {"status": "success", "message": "Pompa açıldı"}
        
        elif action == "pump_off":
            state["pompa"] = False
            return {"status": "success", "message": "Pompa kapatıldı"}
        
        # Alarm sıfırlama
        elif action == "reset_alarms":
            for k in state["kumesler"]:
                k["alarm"] = False
                k["mesaj"] = ""
            return {"status": "success", "message": "Tüm alarmlar sıfırlandı"}
        
        return {"status": "error", "message": f"Bilinmeyen aksiyon: {action}"}
        
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
        # Sıcaklık değişimi (-0.2 ile +0.2 arası)
        kumes["sicaklik"] += random.uniform(-0.2, 0.2)
        kumes["sicaklik"] = round(max(15.0, min(35.0, kumes["sicaklik"])), 1)
        
        # Nem değişimi
        kumes["nem"] += random.uniform(-1.0, 1.0)
        kumes["nem"] = round(max(30.0, min(80.0, kumes["nem"])), 1)
        
        # Amonyak değişimi
        kumes["amonyak"] += random.uniform(-0.5, 0.5)
        kumes["amonyak"] = round(max(0.0, min(50.0, kumes["amonyak"])), 1)
        
        # Su seviyesi azalması (zamanla)
        if random.random() < 0.1:  # %10 ihtimalle
            kumes["su"] = max(0, kumes["su"] - random.randint(5, 15))
        
        # Işık seviyesi (gündüz/gece simülasyonu)
        hour = datetime.now().hour
        if 6 <= hour <= 18:  # Gündüz
            kumes["isik"] = random.randint(400, 800)
        else:  # Gece
            kumes["isik"] = random.randint(50, 200)
        
        # Alarm simülasyonu (rastgele)
        if random.random() < 0.02:  # %2 ihtimalle alarm
            if kumes["sicaklik"] > 30:
                kumes["alarm"] = True
                kumes["mesaj"] = "Yüksek sıcaklık!"
            elif kumes["su"] < 200:
                kumes["alarm"] = True
                kumes["mesaj"] = "Düşük su seviyesi!"
    
    # Yem seviyesi azalması
    if random.random() < 0.05:  # %5 ihtimalle
        state["yem"] = max(0, state["yem"] - 1)
    
    # Uptime güncelleme
    state["uptime"] += UPDATE_INTERVAL
    state["zaman"] = int(time.time())

# =============================================================================
# WEBSOCKET İŞLEYİCİ
# =============================================================================
async def handle_client(websocket):
    """
    Tek bir istemci bağlantısını yönetir
    
    Args:
        websocket: WebSocket bağlantı nesnesi
    """
    client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
    print(f"✓ Yeni bağlantı: {client_id}")
    connected_clients.add(websocket)
    
    # Otomatik veri gönderme görevi
    async def send_periodic_updates():
        """Belirli aralıklarla güncel veri gönderir"""
        try:
            while True:
                simulate_sensor_changes()
                await websocket.send(json.dumps(state))
                await asyncio.sleep(UPDATE_INTERVAL)
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            print(f"❌ Veri gönderme hatası: {e}")
    
    # Arka planda veri göndermeyi başlat
    update_task = asyncio.create_task(send_periodic_updates())
    
    try:
        # İlk bağlantıda mevcut durumu gönder
        await websocket.send(json.dumps(state))
        
        # İstemciden gelen komutları dinle
        async for message in websocket:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] ← Komut ({client_id}): {message[:100]}")
            
            # Komutu işle
            response = update_state_from_command(message)
            
            # Yanıt gönder
            await websocket.send(json.dumps(state))
            
            # Komut sonucunu logla
            if response.get("status") == "success":
                print(f"[{timestamp}] ✓ {response.get('message')}")
            else:
                print(f"[{timestamp}] ✗ {response.get('message')}")
    
    except websockets.exceptions.ConnectionClosed:
        print(f"⚠ Bağlantı kapatıldı: {client_id}")
    except Exception as e:
        print(f"❌ İstemci hatası ({client_id}): {e}")
    finally:
        # Temizlik
        update_task.cancel()
        connected_clients.discard(websocket)
        print(f"✗ Bağlantı sonlandı: {client_id}")
        print(f"   Aktif bağlantılar: {len(connected_clients)}")

# =============================================================================
# ANA SUNUCU
# =============================================================================
async def main():
    """Ana sunucu döngüsü"""
    print("=" * 60)
    print("🔧 ESP32 WebSocket Simülatörü")
    print("=" * 60)
    print(f"📡 Sunucu Adresi: ws://{SERVER_IP}:{SERVER_PORT}")
    print(f"⏱️  Güncelleme Aralığı: {UPDATE_INTERVAL} saniye")
    print(f"🏠 Kümes Sayısı: {len(state['kumesler'])}")
    print("=" * 60)
    print("\n📝 Desteklenen Komutlar:")
    print("  Eski Format:")
    print("    - FAN1:1, FAN2:0")
    print("    - LED:1, LED:0")
    print("    - POMPA:1, POMPA:0")
    print("\n  JSON Format:")
    print('    - {"action": "led_on", "kumes": 1}')
    print('    - {"action": "fan_off", "kumes": 2}')
    print('    - {"action": "door_open", "kumes": 1}')
    print('    - {"action": "get_status"}')
    print("=" * 60)
    print("\n⏳ Sunucu başlatılıyor...\n")
    
    try:
        async with websockets.serve(
            handle_client,
            SERVER_IP,
            SERVER_PORT,
            ping_interval=5,
            ping_timeout=3
        ):
            print(f"✅ Sunucu hazır! Bağlantılar bekleniyor...\n")
            await asyncio.Future()  # Sonsuz döngü
    except OSError as e:
        print(f"\n❌ Sunucu başlatılamadı: {e}")
        print(f"   Port {SERVER_PORT} kullanımda olabilir veya IP adresi yanlış.")
    except Exception as e:
        print(f"\n❌ Beklenmeyen hata: {e}")

# =============================================================================
# GİRİŞ NOKTASI
# =============================================================================
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  Sunucu durduruldu (Ctrl+C)")
        print(f"📊 Son bağlantı sayısı: {len(connected_clients)}")
    except Exception as e:
        print(f"\n❌ Fatal hata: {e}")