#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KÜMES OTOMASYON PWA - GELİŞMİŞ TEST SUNUCUSU
=============================================
✅ Flask web server
✅ WebSocket server (gerçek zamanlı veri)
✅ Authentication simülasyonu
✅ Mock data generator
✅ Auto reload
"""

from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
from flask_sock import Sock
import os
import json
import time
import random
import threading
from datetime import datetime

# ==================== FLASK SETUP ====================
app = Flask(__name__, static_folder='pwa')
CORS(app)
sock = Sock(app)

# PWA klasörü
PWA_DIR = os.path.join(os.path.dirname(__file__), 'pwa')

# ==================== GLOBAL DEĞİŞKENLER ====================
connected_clients = []
authenticated_clients = {}
mock_data_running = True

# Kullanıcı veritabanı (test için)
USERS = {
    'admin': {'password': 'admin123', 'role': 'admin'},
    'user': {'password': 'user123', 'role': 'user'},
    'test': {'password': 'test', 'role': 'user'}
}

# Mock kümes verisi
kumes_data = {
    "sistem": "kumes",
    "zaman": 0,
    "kumesler": [
        {
            "id": 1,
            "sicaklik": 24.5,
            "nem": 55.0,
            "su": 750,
            "isik": 450,
            "fan": False,
            "led": False,
            "alarm": False,
            "mesaj": ""
        },
        {
            "id": 2,
            "sicaklik": 26.8,
            "nem": 58.0,
            "su": 680,
            "isik": 380,
            "fan": False,
            "led": False,
            "alarm": False,
            "mesaj": ""
        },
        {
            "id": 3,
            "sicaklik": 25.2,
            "nem": 52.0,
            "su": 720,
            "isik": 410,
            "fan": False,
            "led": False,
            "alarm": False,
            "mesaj": ""
        }
    ],
    "yem": 15,
    "pompa": False
}

# ==================== MOCK DATA GENERATOR ====================
def generate_mock_data():
    """Gerçekçi sensör verisi üret"""
    global kumes_data
    
    while mock_data_running:
        # Zaman güncelle (saniye)
        kumes_data["zaman"] += 5
        
        # Her kümes için veri üret
        for kumes in kumes_data["kumesler"]:
            # Sıcaklık (18-32°C arası, yavaş değişim)
            kumes["sicaklik"] += random.uniform(-0.3, 0.3)
            kumes["sicaklik"] = max(18, min(35, kumes["sicaklik"]))
            
            # Nem (%40-70 arası)
            kumes["nem"] += random.uniform(-1, 1)
            kumes["nem"] = max(40, min(75, kumes["nem"]))
            
            # Su seviyesi (yavaş azalma)
            kumes["su"] -= random.randint(0, 2)
            kumes["su"] = max(0, kumes["su"])
            
            # Işık (200-600 arası, günün saatine göre)
            hour = datetime.now().hour
            if 6 <= hour <= 18:  # Gündüz
                kumes["isik"] = random.randint(400, 600)
            else:  # Gece
                kumes["isik"] = random.randint(200, 300)
            
            # Alarm kontrolü
            kumes["alarm"] = False
            kumes["mesaj"] = ""
            
            # Sıcaklık alarmı
            if kumes["sicaklik"] > 30:
                kumes["alarm"] = True
                kumes["mesaj"] = f"Yüksek sıcaklık: {kumes['sicaklik']:.1f}°C"
            elif kumes["sicaklik"] < 20:
                kumes["alarm"] = True
                kumes["mesaj"] = f"Düşük sıcaklık: {kumes['sicaklik']:.1f}°C"
            
            # Su seviyesi alarmı
            if kumes["su"] < 200:
                kumes["alarm"] = True
                kumes["mesaj"] = "Su seviyesi kritik!"
            
            # Nem alarmı
            if kumes["nem"] < 45:
                kumes["alarm"] = True
                kumes["mesaj"] = f"Düşük nem: {kumes['nem']:.1f}%"
        
        # Yem seviyesi (yavaş azalma)
        kumes_data["yem"] -= random.uniform(0, 0.1)
        kumes_data["yem"] = max(0, kumes_data["yem"])
        
        # 5 saniyede bir güncelle
        time.sleep(5)
        
        # Authenticated clientlara gönder
        send_data_to_clients()

def send_data_to_clients():
    """Tüm bağlı clientlara veri gönder"""
    if authenticated_clients:
        data_json = json.dumps(kumes_data)
        print(f"📤 {len(authenticated_clients)} client'a veri gönderiliyor...")
        
        # Disconnected clientları temizle
        disconnected = []
        for ws, username in authenticated_clients.items():
            try:
                ws.send(data_json)
            except:
                disconnected.append(ws)
        
        for ws in disconnected:
            del authenticated_clients[ws]

# ==================== WEBSOCKET HANDLER ====================
@sock.route('/ws')
def websocket(ws):
    """WebSocket bağlantısı"""
    print(f"🔌 Yeni WebSocket bağlantısı")
    connected_clients.append(ws)
    
    # Auth gerekli mesajı gönder
    ws.send(json.dumps({
        "type": "auth_required",
        "message": "Lütfen giriş yapın"
    }))
    
    try:
        while True:
            message = ws.receive()
            if message is None:
                break
            
            print(f"📥 Mesaj alındı: {message}")
            
            try:
                data = json.loads(message)
                msg_type = data.get('type', '')
                
                # AUTH mesajı
                if msg_type == 'auth':
                    username = data.get('username', '')
                    password = data.get('password', '')
                    
                    # Kullanıcı kontrolü
                    if username in USERS and USERS[username]['password'] == password:
                        # Başarılı auth
                        authenticated_clients[ws] = username
                        role = USERS[username]['role']
                        
                        response = {
                            "type": "auth_success",
                            "username": username,
                            "role": role
                        }
                        
                        ws.send(json.dumps(response))
                        print(f"✅ Auth başarılı: {username} ({role})")
                        
                        # İlk veriyi gönder
                        ws.send(json.dumps(kumes_data))
                    else:
                        # Başarısız auth
                        response = {
                            "type": "auth_failed",
                            "message": "Kullanıcı adı veya şifre hatalı"
                        }
                        ws.send(json.dumps(response))
                        print(f"❌ Auth başarısız: {username}")
                
                # COMMAND mesajı
                elif msg_type == 'command':
                    if ws in authenticated_clients:
                        command = data.get('command', '')
                        handle_command(command, ws)
                    else:
                        ws.send(json.dumps({
                            "type": "error",
                            "message": "Önce giriş yapmalısınız"
                        }))
                
            except json.JSONDecodeError:
                print(f"⚠️ JSON parse hatası: {message}")
    
    except Exception as e:
        print(f"❌ WebSocket hatası: {e}")
    
    finally:
        # Bağlantı kesildi
        if ws in connected_clients:
            connected_clients.remove(ws)
        if ws in authenticated_clients:
            username = authenticated_clients[ws]
            del authenticated_clients[ws]
            print(f"👋 {username} çıkış yaptı")
        print(f"⚠️ WebSocket bağlantısı kesildi")

# ==================== KOMUT İŞLEME ====================
def handle_command(command, ws):
    """Komutları işle"""
    print(f"🎮 Komut: {command}")
    
    # LED kontrol
    if command.startswith("LED:"):
        state = command.split(":")[1]
        for kumes in kumes_data["kumesler"]:
            kumes["led"] = (state == "1")
        ws.send(json.dumps({"type": "ok", "command": "LED"}))
    
    # FAN kontrol
    elif command.startswith("FAN"):
        parts = command.split(":")
        fan_id = int(parts[0][-1])  # FAN1 → 1
        state = parts[1]
        
        if 1 <= fan_id <= 3:
            kumes_data["kumesler"][fan_id - 1]["fan"] = (state == "1")
            ws.send(json.dumps({"type": "ok", "command": f"FAN{fan_id}"}))
    
    # POMPA kontrol
    elif command.startswith("POMPA:"):
        state = command.split(":")[1]
        kumes_data["pompa"] = (state == "1")
        ws.send(json.dumps({"type": "ok", "command": "POMPA"}))
    
    # KAPI kontrol
    elif command.startswith("KAPI:"):
        angle = command.split(":")[1]
        print(f"🚪 Kapı açısı: {angle}°")
        ws.send(json.dumps({"type": "ok", "command": "KAPI"}))
    
    # YEM dağıt
    elif command.startswith("YEM:"):
        duration = command.split(":")[1]
        print(f"🌾 Yem dağıtılıyor ({duration} saniye)...")
        kumes_data["yem"] = max(0, kumes_data["yem"] - 1)
        ws.send(json.dumps({"type": "ok", "command": "YEM"}))
    
    # STATUS
    elif command == "STATUS":
        ws.send(json.dumps(kumes_data))
    
    else:
        ws.send(json.dumps({
            "type": "error",
            "message": f"Bilinmeyen komut: {command}"
        }))

# ==================== HTTP ROUTES ====================
@app.route('/')
def index():
    """Ana sayfa"""
    return send_from_directory(PWA_DIR, 'index.html')

@app.route('/<path:path>')
def serve_file(path):
    """Static dosyalar"""
    try:
        return send_from_directory(PWA_DIR, path)
    except:
        return f"Dosya bulunamadı: {path}", 404

# ==================== API ENDPOINTS ====================
@app.route('/api/status')
def api_status():
    """Mevcut durum"""
    return jsonify(kumes_data)

@app.route('/api/auth', methods=['POST'])
def api_auth():
    """Authentication (HTTP)"""
    data = request.json
    username = data.get('username', '')
    password = data.get('password', '')
    
    if username in USERS and USERS[username]['password'] == password:
        return jsonify({
            "success": True,
            "username": username,
            "role": USERS[username]['role']
        })
    else:
        return jsonify({
            "success": False,
            "message": "Kullanıcı adı veya şifre hatalı"
        }), 401

@app.route('/api/command', methods=['POST'])
def api_command():
    """Komut gönder (HTTP)"""
    data = request.json
    command = data.get('command', '')
    
    print(f"📤 API Komutu: {command}")
    
    # Mock işlem
    return jsonify({
        "status": "ok",
        "command": command,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/users')
def api_users():
    """Kullanıcı listesi"""
    users = []
    for username, info in USERS.items():
        users.append({
            "username": username,
            "role": info['role']
        })
    return jsonify({"users": users})

@app.route('/api/info')
def api_info():
    """Sunucu bilgisi"""
    return jsonify({
        "server": "PWA Test Server",
        "version": "2.0.0",
        "connected_clients": len(connected_clients),
        "authenticated_clients": len(authenticated_clients),
        "uptime": kumes_data["zaman"],
        "mock_data": True
    })

# ==================== ANA PROGRAM ====================
if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("🐔 KÜMES OTOMASYON PWA - GELİŞMİŞ TEST SUNUCUSU")
    print("=" * 60)
    print()
    print("📦 Özellikler:")
    print("   ✅ Flask Web Server")
    print("   ✅ WebSocket Server (Gerçek zamanlı)")
    print("   ✅ Authentication (admin/admin123)")
    print("   ✅ Mock Data Generator")
    print("   ✅ Auto Refresh (5 saniye)")
    print()
    print("📱 Erişim:")
    print(f"   💻 Bilgisayar:  http://localhost:5000")
    print(f"   📱 Telefon:     http://[BİLGİSAYAR-IP]:5000")
    print()
    print("👥 Test Kullanıcıları:")
    print("   👤 admin / admin123  (Admin)")
    print("   👤 user / user123    (User)")
    print("   👤 test / test       (User)")
    print()
    print("🔌 WebSocket:")
    print(f"   ws://localhost:5000/ws")
    print()
    print("📊 API Endpoints:")
    print("   GET  /api/status    → Mevcut durum")
    print("   POST /api/auth      → Giriş yap")
    print("   POST /api/command   → Komut gönder")
    print("   GET  /api/users     → Kullanıcı listesi")
    print("   GET  /api/info      → Sunucu bilgisi")
    print()
    print("💡 İpuçları:")
    print("   • PWA'yı aç ve admin/admin123 ile giriş yap")
    print("   • Veriler her 5 saniyede otomatik güncellenir")
    print("   • Sıcaklık 30°C üstüne çıkarsa alarm oluşur")
    print("   • Ctrl+C ile durdurun")
    print()
    print("=" * 60)
    print()
    
    # Mock data generator'ı başlat
    mock_thread = threading.Thread(target=generate_mock_data, daemon=True)
    mock_thread.start()
    print("✅ Mock data generator başlatıldı")
    print()
    
    try:
        # Flask sunucusunu başlat
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        print("\n\n👋 Sunucu kapatılıyor...")
        mock_data_running = False
        print("✅ Kapatıldı!")