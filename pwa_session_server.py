#!/usr/bin/env python3
"""
PWA Test Sunucusu - SessionManager & Auth Destekli
===================================================
- WebSocket auth sistemi
- Session yönetimi
- Admin mod kontrolü
- Mock kümes verisi
"""

import asyncio
import websockets
import json
import random
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
import os
from pathlib import Path

# ==================== KULLANICILAR ====================
USERS = {
    "admin": {"password": "admin123", "role": "admin"},
    "user": {"password": "user123", "role": "user"},
    "test": {"password": "test", "role": "user"}
}

# ==================== SESSION YÖNETİMİ ====================
active_sessions = {}
admin_session_id = None
admin_mode = "active"  # "active" veya "watching"

def generate_session_id():
    """Session ID oluştur"""
    return f"sess_{''.join(random.choices('0123456789abcdef', k=8))}"

def update_permissions():
    """Tüm session'ların yetkilerini güncelle"""
    global admin_mode, admin_session_id
    
    admin_active = False
    
    # Admin aktif mi?
    if admin_session_id and admin_session_id in active_sessions:
        admin_active = (active_sessions[admin_session_id]["admin_mode"] == "active")
    
    # Tüm session'ları güncelle
    for sid, session in active_sessions.items():
        if session["role"] == "admin":
            session["can_control"] = (session["admin_mode"] == "active")
        else:
            session["can_control"] = not admin_active
    
    print(f"📊 Yetkiler güncellendi (Admin aktif: {admin_active})")

# ==================== MOCK VERİ OLUŞTURMA ====================
def generate_mock_data():
    """Mock kümes verisi oluştur"""
    kumesler = []
    for i in range(1, 4):
        kumesler.append({
            "id": i,
            "sicaklik": round(random.uniform(20, 30), 2),
            "nem": round(random.uniform(40, 70), 2),
            "su": random.randint(600, 800),
            "isik": random.randint(400, 600),
            "fan": False,
            "led": False,
            "alarm": False,
            "mesaj": ""
        })
    
    return {
        "sistem": "kumes",
        "zaman": int(time.time()) % 1000,
        "kumesler": kumesler,
        "yem": round(random.uniform(10, 20), 2),
        "pompa": False
    }

# ==================== WEBSOCKET HANDLER ====================
connected_clients = set()

async def handle_websocket(websocket, path):
    """WebSocket bağlantısını yönet"""
    global admin_session_id, admin_mode
    
    client_id = id(websocket)
    connected_clients.add(websocket)
    session_id = None
    
    print(f"🔌 Yeni bağlantı: Client #{client_id}")
    
    # Auth gerekli mesajı gönder
    await websocket.send(json.dumps({
        "type": "auth_required",
        "message": "Lütfen giriş yapın"
    }))
    
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get("type")
                
                # ==================== AUTH ====================
                if msg_type == "auth":
                    username = data.get("username")
                    password = data.get("password")
                    client_type = data.get("client_type", "unknown")
                    
                    print(f"🔑 Login denemesi: {username} ({client_type})")
                    
                    # Kullanıcı kontrolü
                    if username in USERS and USERS[username]["password"] == password:
                        user = USERS[username]
                        session_id = generate_session_id()
                        
                        # Session oluştur
                        session = {
                            "session_id": session_id,
                            "username": username,
                            "role": user["role"],
                            "client_type": client_type,
                            "websocket": websocket,
                            "can_control": True  # Başlangıçta true
                        }
                        
                        if user["role"] == "admin":
                            session["admin_mode"] = "active"
                            
                            # Önceki admin varsa override
                            if admin_session_id and admin_session_id in active_sessions:
                                old_ws = active_sessions[admin_session_id]["websocket"]
                                await old_ws.send(json.dumps({
                                    "type": "admin_override",
                                    "message": "Başka bir cihazdan admin girişi yapıldı",
                                    "new_admin_client": client_type
                                }))
                            
                            admin_session_id = session_id
                        else:
                            session["admin_mode"] = None
                        
                        active_sessions[session_id] = session
                        update_permissions()
                        
                        # Başarılı yanıt
                        response = {
                            "type": "auth_success",
                            "username": username,
                            "role": user["role"],
                            "session_id": session_id,
                            "permissions": {
                                "can_control": session["can_control"],
                                "can_change_settings": (user["role"] == "admin"),
                                "can_view": True
                            }
                        }
                        
                        if user["role"] == "admin":
                            response["admin_mode"] = session["admin_mode"]
                        
                        await websocket.send(json.dumps(response))
                        
                        print(f"✅ {username} ({user['role']}) giriş yaptı - Kontrol: {session['can_control']}")
                        
                        # Diğer clientlara bildir
                        await broadcast({
                            "type": "user_joined",
                            "username": username,
                            "role": user["role"],
                            "client_type": client_type
                        }, exclude=websocket)
                    
                    else:
                        # Hatalı giriş
                        await websocket.send(json.dumps({
                            "type": "auth_failed",
                            "message": "Kullanıcı adı veya şifre hatalı"
                        }))
                        print("❌ Giriş başarısız!")
                
                # ==================== MOD DEĞİŞTİRME ====================
                elif msg_type == "change_mode":
                    sid = data.get("session_id")
                    new_mode = data.get("mode")
                    
                    if sid in active_sessions:
                        session = active_sessions[sid]
                        
                        if session["role"] == "admin":
                            old_mode = session["admin_mode"]
                            session["admin_mode"] = new_mode
                            
                            print(f"🔄 Admin modu: {old_mode} → {new_mode}")
                            
                            update_permissions()
                            
                            # Admin'e onay
                            await websocket.send(json.dumps({
                                "type": "mode_changed",
                                "mode": new_mode
                            }))
                            
                            # User'lara bildir
                            if new_mode == "watching":
                                await broadcast({
                                    "type": "control_available",
                                    "message": "Admin izleme moduna geçti. Artık kontrol edebilirsiniz!",
                                    "admin_mode": "watching"
                                }, exclude_roles=["admin"])
                            else:
                                await broadcast({
                                    "type": "control_revoked",
                                    "message": "Admin kontrolü aldı. Sadece izleyebilirsiniz.",
                                    "admin_mode": "active"
                                }, exclude_roles=["admin"])
                
                # ==================== KOMUT ====================
                elif msg_type == "command":
                    sid = data.get("session_id")
                    command = data.get("command")
                    
                    if sid in active_sessions:
                        session = active_sessions[sid]
                        
                        if session["can_control"]:
                            print(f"📤 Komut: {command} (by {session['username']})")
                            
                            # Başarı mesajı
                            await websocket.send(json.dumps({
                                "type": "command_sent",
                                "command": command
                            }))
                        else:
                            # Yetki yok
                            await websocket.send(json.dumps({
                                "type": "permission_denied",
                                "message": "Bu işlem için kontrol yetkisi gerekli"
                            }))
                            print(f"❌ Komut reddedildi: {session['username']} (Yetki yok)")
            
            except json.JSONDecodeError:
                print("❌ JSON parse hatası")
    
    except websockets.exceptions.ConnectionClosed:
        pass
    
    finally:
        # Bağlantı kesildi
        connected_clients.discard(websocket)
        
        # Session temizle
        if session_id and session_id in active_sessions:
            username = active_sessions[session_id]["username"]
            role = active_sessions[session_id]["role"]
            
            print(f"👋 {username} ({role}) ayrıldı")
            
            # Admin ayrıldıysa
            if role == "admin" and session_id == admin_session_id:
                admin_session_id = None
                
                # User'lara kontrol ver
                await broadcast({
                    "type": "admin_left",
                    "message": "Admin ayrıldı. Artık kontrol edebilirsiniz!"
                }, exclude_roles=["admin"])
            
            del active_sessions[session_id]
            update_permissions()
        
        print(f"⚠️ Bağlantı kesildi: Client #{client_id}")

async def broadcast(message, exclude=None, exclude_roles=None):
    """Tüm clientlara mesaj gönder"""
    msg_json = json.dumps(message)
    
    for sid, session in active_sessions.items():
        ws = session["websocket"]
        
        # Exclude kontrolü
        if exclude and ws == exclude:
            continue
        
        if exclude_roles and session["role"] in exclude_roles:
            continue
        
        try:
            await ws.send(msg_json)
        except:
            pass

async def send_periodic_data():
    """Periyodik veri gönderme"""
    while True:
        await asyncio.sleep(5)
        
        if connected_clients:
            data = generate_mock_data()
            data_json = json.dumps(data)
            
            # Tüm clientlara gönder
            disconnected = set()
            for client in connected_clients:
                try:
                    await client.send(data_json)
                except:
                    disconnected.add(client)
            
            # Kopmuş clientları temizle
            connected_clients.difference_update(disconnected)

# ==================== HTTP SERVER ====================
class CORSRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

def run_http_server():
    """HTTP sunucusu başlat"""
    # PWA dizinine geç
    pwa_dir = Path(__file__).parent / "pwa"
    if pwa_dir.exists():
        os.chdir(pwa_dir)
        print(f"📁 PWA dizini: {pwa_dir}")
    
    server = HTTPServer(('localhost', 5001), CORSRequestHandler)
    print("🌐 HTTP Server: http://localhost:5001")
    server.serve_forever()

# ==================== MAIN ====================
async def main():
    """Ana fonksiyon"""
    print("\n" + "=" * 60)
    print("PWA TEST SUNUCUSU - SESSION MANAGER & AUTH")
    print("=" * 60)
    print("📡 WebSocket: ws://localhost:8765")
    print("🌐 HTTP: http://localhost:5001")
    print("\n👥 Kullanıcılar:")
    print("   👑 admin / admin123 (Admin)")
    print("   👤 user / user123 (User)")
    print("   👤 test / test (User)")
    print("=" * 60 + "\n")
    
    # HTTP sunucusu thread'de çalıştır
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()
    
    # WebSocket sunucusu (farklı port!)
    async with websockets.serve(handle_websocket, "localhost", 8765):
        # Periyodik veri gönderme task'ı
        await send_periodic_data()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Sunucu kapatılıyor...")