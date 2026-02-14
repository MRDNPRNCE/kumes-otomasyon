#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kümes Otomasyon Sistemi - Birleştirilmiş Ana Pencere
=====================================================
✅ Session Manager entegrasyonu (admin/user yetkileri)
✅ Modern PyQt6 UI
✅ WebSocket ile ESP32 bağlantısı
✅ Gerçek zamanlı veri güncellemesi
✅ Dark mode tema
✅ Login sistemi
"""

import sys
import json
import asyncio
from typing import Optional
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QStackedWidget, QFrame, QLabel, QGridLayout, 
    QPushButton, QMessageBox, QDialog, QLineEdit, QFormLayout,
    QScrollArea
)
from PyQt6.QtCore import QTimer, Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QPalette, QColor
import websockets

# Eski dosyadan importlar
try:
    from core.config import APP_TITLE, DEFAULT_ESP_IP, WS_PORT, KUMES_BILGILERI
    from core.database import DatabaseManager
    from core.websocket_bridge import WebSocketBridge
    from core.alarm_manager import AlarmManager
    from ui.kumes_card import KumesCard
    from ui.system_status import SystemStatusPanel
    from ui.control_panel import ControlPanel
    from ui.alarm_view import AlarmView
    from ui.settings_tab import SettingsTab
    from data.real_time_updater import RealTimeDataUpdater
    from core.session_manager import SessionManager
    FULL_FEATURES = True
    print("✅ Tüm modüller yüklendi (Tam özellikli mod)")
except ImportError as e:
    print(f"⚠️ Bazı modüller bulunamadı: {e}")
    print("📦 Basit mod aktif (Temel özellikler)")
    FULL_FEATURES = False
    # Varsayılan değerler
    APP_TITLE = "Kümes Otomasyon Sistemi"
    DEFAULT_ESP_IP = "192.168.1.117"
    WS_PORT = 81
    KUMES_BILGILERI = {
        1: {"ad": "Kümes 1", "tavuk_sayisi": 50, "gunluk": 45, "icon": "🐔"},
        2: {"ad": "Kümes 2", "tavuk_sayisi": 40, "gunluk": 30, "icon": "🐓"},
        3: {"ad": "Kümes 3", "tavuk_sayisi": 60, "gunluk": 60, "icon": "🦆"}
    }


# ==================== WEBSOCKET THREAD ====================
class WebSocketThread(QThread):
    """WebSocket bağlantısını ayrı thread'de çalıştır"""
    message_received = pyqtSignal(str)
    connection_status = pyqtSignal(bool)

    def __init__(self, ip, port=81):
        super().__init__()
        self.ip = ip
        self.port = port
        self.websocket = None
        self.running = True
        self.session_id = None
        self._loop = None  # Event loop referansı
        self._send_queue = asyncio.Queue()

    async def connect_and_listen(self):
        """WebSocket'e bağlan ve dinle"""
        uri = f"ws://{self.ip}:{self.port}"
        print(f"🔌 Bağlanılıyor: {uri}")

        try:
            async with websockets.connect(uri, open_timeout=10) as websocket:
                self.websocket = websocket
                self.connection_status.emit(True)
                print("✅ WebSocket bağlandı!")

                # Mesaj alma ve gönderme görevlerini paralel çalıştır
                receive_task = asyncio.create_task(self._receive_loop(websocket))
                send_task = asyncio.create_task(self._send_loop(websocket))

                try:
                    await asyncio.gather(receive_task, send_task)
                except Exception:
                    receive_task.cancel()
                    send_task.cancel()

        except Exception as e:
            print(f"❌ Bağlantı hatası: {e}")
            self.connection_status.emit(False)

    async def _receive_loop(self, websocket):
        """Mesaj alma döngüsü"""
        while self.running:
            try:
                message = await asyncio.wait_for(
                    websocket.recv(),
                    timeout=1.0
                )
                self.message_received.emit(message)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"❌ Mesaj alma hatası: {e}")
                break

    async def _send_loop(self, websocket):
        """Mesaj gönderme döngüsü - kuyruktan mesaj alıp gönderir"""
        while self.running:
            try:
                message = await asyncio.wait_for(
                    self._send_queue.get(),
                    timeout=1.0
                )
                await websocket.send(message)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"❌ Mesaj gönderme hatası: {e}")
                break

    def run(self):
        """Thread başlatıldığında çalışır"""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self.connect_and_listen())
        self._loop.close()

    def send_message(self, message):
        """Thread-safe mesaj gönder (herhangi bir thread'den çağrılabilir)"""
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._send_queue.put_nowait, message)

    def stop(self):
        """Thread'i durdur"""
        self.running = False


# ==================== LOGIN DIALOG ====================
class LoginDialog(QDialog):
    """Login Dialog"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🐔 Kümes Otomasyon - Giriş")
        self.setFixedSize(400, 300)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Başlık
        title = QLabel("🐔 Kümes Otomasyon Sistemi")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        layout.addSpacing(20)
        
        # Form
        form_layout = QFormLayout()
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Kullanıcı adı")
        self.username_input.setText("admin")
        form_layout.addRow("👤 Kullanıcı:", self.username_input)
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Şifre")
        self.password_input.setText("admin123")
        form_layout.addRow("🔒 Şifre:", self.password_input)
        
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("192.168.1.117")
        self.ip_input.setText(DEFAULT_ESP_IP)
        form_layout.addRow("📡 ESP32 IP:", self.ip_input)
        
        layout.addLayout(form_layout)
        layout.addSpacing(20)
        
        # Butonlar
        btn_layout = QHBoxLayout()
        
        self.login_btn = QPushButton("🔓 Giriş Yap")
        self.login_btn.setMinimumHeight(40)
        self.login_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.login_btn)
        
        self.cancel_btn = QPushButton("❌ İptal")
        self.cancel_btn.setMinimumHeight(40)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(btn_layout)
        
        # Info
        layout.addSpacing(10)
        info = QLabel("Test Kullanıcıları:\n👑 admin / admin123\n👤 user / user123")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(info)
        
        self.setLayout(layout)
    
    def get_credentials(self):
        return {
            'username': self.username_input.text(),
            'password': self.password_input.text(),
            'ip': self.ip_input.text()
        }


# ==================== KÜMES KART (Basit Versiyon) ====================
class SimpleKumesCard(QFrame):
    """Basit kümes kartı widget"""
    
    def __init__(self, kumes_id, parent=None):
        super().__init__(parent)
        self.kumes_id = kumes_id
        self.setup_ui()
        
    def setup_ui(self):
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setLineWidth(2)
        self.setStyleSheet("""
            QFrame {
                border: 2px solid #30363d;
                border-radius: 10px;
                padding: 10px;
                background-color: #161b22;
            }
            QFrame:hover {
                border-color: #58a6ff;
            }
        """)
        
        layout = QVBoxLayout()
        
        # Kümes bilgisi
        info = KUMES_BILGILERI.get(self.kumes_id, {})
        
        # Başlık
        title_layout = QHBoxLayout()
        icon = QLabel(info.get('icon', '🐔'))
        icon.setFont(QFont("Arial", 24))
        title_layout.addWidget(icon)
        
        self.title = QLabel(info.get('ad', f"Kümes {self.kumes_id}"))
        self.title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title_layout.addWidget(self.title)
        title_layout.addStretch()
        
        layout.addLayout(title_layout)
        
        # Veriler
        self.sicaklik_label = QLabel("🌡️ Sıcaklık: --°C")
        self.nem_label = QLabel("💧 Nem: --%")
        self.su_label = QLabel("💦 Su: --")
        self.isik_label = QLabel("💡 Işık: --")
        
        for label in [self.sicaklik_label, self.nem_label, self.su_label, self.isik_label]:
            label.setFont(QFont("Arial", 11))
            layout.addWidget(label)
        
        # Tavuk bilgisi
        tavuk_info = QLabel(f"🐔 {info.get('tavuk_sayisi', 0)} tavuk • 📅 {info.get('gunluk', 0)} günlük")
        tavuk_info.setStyleSheet("color: #9ae6b4; font-size: 10px;")
        layout.addWidget(tavuk_info)
        
        layout.addSpacing(10)
        
        # Kontrol butonları
        btn_layout = QHBoxLayout()
        
        self.fan_btn = QPushButton("💨 Fan")
        self.fan_btn.setCheckable(True)
        self.fan_btn.clicked.connect(lambda: self.on_button_click('fan'))
        btn_layout.addWidget(self.fan_btn)
        
        self.led_btn = QPushButton("💡 LED")
        self.led_btn.setCheckable(True)
        self.led_btn.clicked.connect(lambda: self.on_button_click('led'))
        btn_layout.addWidget(self.led_btn)
        
        layout.addLayout(btn_layout)
        
        # Alarm butonu
        self.alarm_btn = QPushButton("🚨 Alarm")
        self.alarm_btn.setStyleSheet("background-color: #ff6b6b; color: white;")
        self.alarm_btn.clicked.connect(lambda: self.on_button_click('alarm'))
        layout.addWidget(self.alarm_btn)
        
        self.setLayout(layout)
    
    def update_data(self, data):
        """Veriyi güncelle"""
        self.sicaklik_label.setText(f"🌡️ Sıcaklık: {data.get('sicaklik', '--')}°C")
        self.nem_label.setText(f"💧 Nem: {data.get('nem', '--')}%")
        self.su_label.setText(f"💦 Su: {data.get('su', '--')}")
        self.isik_label.setText(f"💡 Işık: {data.get('isik', '--')}")
        
        # Buton durumları
        self.fan_btn.setChecked(data.get('fan', False))
        self.led_btn.setChecked(data.get('led', False))
        
        if data.get('alarm', False):
            self.alarm_btn.setStyleSheet("background-color: #ff0000; color: white;")
        else:
            self.alarm_btn.setStyleSheet("background-color: #ff6b6b; color: white;")
    
    def on_button_click(self, control_type):
        """Buton tıklandığında"""
        parent = self.parent()
        while parent and not isinstance(parent, KumesOtomasyonMainWindow):
            parent = parent.parent()
        
        if parent:
            if control_type == 'fan':
                state = 1 if self.fan_btn.isChecked() else 0
                parent.send_command(f"FAN{self.kumes_id}:{state}")
            elif control_type == 'led':
                state = 1 if self.led_btn.isChecked() else 0
                parent.send_command(f"LED{self.kumes_id}:{state}")
            elif control_type == 'alarm':
                parent.send_command(f"ALARM{self.kumes_id}:0")


# ==================== ANA PENCERE ====================
class KumesOtomasyonMainWindow(QMainWindow):
    """Ana pencere - Eski ve yeni özelliklerin birleşimi"""
    
    def __init__(self, initial_ip: str = DEFAULT_ESP_IP):
        super().__init__()
        
        global FULL_FEATURES  # Global değişken olarak kullan
        
        print("\n" + "=" * 70)
        print("🐔 KÜMES OTOMASYON SİSTEMİ")
        print("=" * 70)
        print(f"   Mod       : {'Tam Özellikli' if FULL_FEATURES else 'Basit'}")
        print(f"   IP        : {initial_ip}")
        print(f"   Port      : {WS_PORT}")
        print("=" * 70 + "\n")
        
        self.session_manager = None
        self.websocket_thread = None
        self.kumes_cards = {}
        self.kumes_data = {}
        self.full_features = FULL_FEATURES  # Instance variable olarak da sakla
        
        # Eski sistem bileşenleri (varsa)
        if FULL_FEATURES:
            try:
                self.db = DatabaseManager()
                self.ws = WebSocketBridge(initial_ip)
                self.alarm_mgr = AlarmManager(self.db)
                self.updater = RealTimeDataUpdater(self.ws)
                print("✅ Eski sistem bileşenleri yüklendi")
            except Exception as e:
                print(f"⚠️ Eski bileşenler yüklenemedi: {e}")
                FULL_FEATURES = False
                self.full_features = False
        
        self.setWindowTitle(APP_TITLE)
        self.setMinimumSize(1000, 700)
        
        # Login göster
        if not self.show_login():
            sys.exit(0)
        
        self.setup_ui()
        self.connect_websocket()
    
    def show_login(self):
        """Login dialog göster"""
        dialog = LoginDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            creds = dialog.get_credentials()
            self.username = creds['username']
            self.password = creds['password']
            self.esp32_ip = creds['ip']
            return True
        return False
    
    def setup_ui(self):
        """UI oluştur"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        
        # Header
        header = self.create_header()
        main_layout.addWidget(header)
        
        # Ana içerik
        content_layout = QHBoxLayout()
        
        # Sol panel - Kümes kartları
        left_panel = self.create_left_panel()
        content_layout.addWidget(left_panel, stretch=2)
        
        # Sağ panel - Tabs
        right_panel = self.create_right_panel()
        content_layout.addWidget(right_panel, stretch=3)
        
        main_layout.addLayout(content_layout)
        
        # Footer
        self.status_label = QLabel("🔴 Bağlantı bekleniyor...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.status_label)
        
        central_widget.setLayout(main_layout)
    
    def create_header(self):
        """Header oluştur"""
        header = QFrame()
        header.setFrameStyle(QFrame.Shape.StyledPanel)
        header.setMaximumHeight(60)
        
        layout = QHBoxLayout()
        
        # Kullanıcı bilgisi
        self.user_label = QLabel(f"👤 {self.username}")
        self.user_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(self.user_label)
        
        layout.addStretch()
        
        # Mod butonu (admin için)
        if self.username == "admin":
            self.mode_btn = QPushButton("👁️ İzleme Modu")
            self.mode_btn.clicked.connect(self.toggle_mode)
            layout.addWidget(self.mode_btn)
        
        # Çıkış butonu
        logout_btn = QPushButton("🚪 Çıkış")
        logout_btn.clicked.connect(self.logout)
        layout.addWidget(logout_btn)
        
        header.setLayout(layout)
        return header
    
    def create_left_panel(self):
        """Sol panel - Kümes kartları"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        container = QWidget()
        layout = QGridLayout()
        layout.setSpacing(15)
        
        # 3 kümes kartı
        for i in range(1, 4):
            card = SimpleKumesCard(i, self)
            self.kumes_cards[i] = card
            row = (i - 1) // 2
            col = (i - 1) % 2
            layout.addWidget(card, row, col)
        
        container.setLayout(layout)
        scroll.setWidget(container)
        return scroll
    
    def create_right_panel(self):
        """Sağ panel - Tabs"""
        self.tabs = QTabWidget()
        
        # Ana Ekran
        main_tab = QLabel("📊 Genel Durum\n\nTüm kümesler sol tarafta görünüyor")
        main_tab.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_tab.setStyleSheet("font-size: 14px;")
        self.tabs.addTab(main_tab, "📊 Ana Ekran")
        
        # Kontrol (varsa eski panel)
        if self.full_features and hasattr(self, 'ws'):
            try:
                self.control_panel = ControlPanel(self.ws)
                self.tabs.addTab(self.control_panel, "⚙️ Kontrol")
            except Exception as e:
                print(f"⚠️ Kontrol paneli yüklenemedi: {e}")
        
        # Alarmlar
        alarm_tab = QLabel("🚨 Alarmlar\n\nAlarm sistemi aktif")
        alarm_tab.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.tabs.addTab(alarm_tab, "🚨 Alarmlar")
        
        # Ayarlar
        settings_tab = QLabel("⚙️ Ayarlar\n\nSistem ayarları")
        settings_tab.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.tabs.addTab(settings_tab, "⚙️ Ayarlar")
        
        return self.tabs
    
    def connect_websocket(self):
        """WebSocket'e bağlan"""
        self.websocket_thread = WebSocketThread(self.esp32_ip, WS_PORT)
        self.websocket_thread.message_received.connect(self.on_message)
        self.websocket_thread.connection_status.connect(self.on_connection_status)
        self.websocket_thread.start()
        
        # 2 saniye sonra login yap
        QTimer.singleShot(2000, self.send_login)
        
        # Eski sistem WebSocket'i de başlat (varsa)
        if self.full_features and hasattr(self, 'ws'):
            try:
                self.ws.connect()
                self.ws.dataReceived.connect(self.on_old_data)
            except Exception as e:
                print(f"⚠️ Eski WebSocket başlatılamadı: {e}")
    
    def send_login(self):
        """Login mesajı gönder"""
        message = json.dumps({
            'type': 'auth',
            'username': self.username,
            'password': self.password,
            'client_type': 'desktop'
        })
        
        if self.websocket_thread:
            self.websocket_thread.send_message(message)
            print(f"📤 Login gönderildi: {self.username}")
    
    def on_connection_status(self, connected):
        """Bağlantı durumu değişti"""
        if connected:
            self.status_label.setText("🟢 Bağlandı")
            self.status_label.setStyleSheet("color: green;")
        else:
            self.status_label.setText("🔴 Bağlantı kesildi")
            self.status_label.setStyleSheet("color: red;")
    
    def on_message(self, message):
        """Yeni WebSocket mesaj alındı"""
        try:
            data = json.loads(message)
            msg_type = data.get('type')
            
            print(f"📥 Mesaj: {msg_type}")
            
            if msg_type == 'auth_success':
                self.websocket_thread.session_id = data.get('session_id')
                print(f"✅ {data.get('username')} giriş yaptı!")
                QMessageBox.information(self, "Başarılı", f"Hoş geldiniz {data.get('username')}!")
            
            elif msg_type == 'auth_failed':
                QMessageBox.warning(self, "Hata", data.get('message', 'Giriş başarısız!'))
            
            elif data.get('sistem') == 'kumes' or data.get('kumesler'):
                # Kümes verisi (sistem alanı olan veya olmayan formatları destekle)
                self.update_kumes_data(data)
            
        except json.JSONDecodeError:
            print("❌ JSON parse hatası")
        except Exception as e:
            print(f"❌ Hata: {e}")
    
    def on_old_data(self, raw_json: str):
        """Eski WebSocket'ten veri (eski sistem için)"""
        try:
            data = json.loads(raw_json)
            self.update_kumes_data(data)
        except:
            pass
    
    def update_kumes_data(self, data):
        """Kümes verilerini güncelle"""
        kumesler = data.get('kumesler', [])
        
        for kumes_data in kumesler:
            kumes_id = kumes_data.get('id')
            self.kumes_data[kumes_id] = kumes_data
            
            if kumes_id in self.kumes_cards:
                self.kumes_cards[kumes_id].update_data(kumes_data)
    
    def send_command(self, command):
        """Komut gönder"""
        message = json.dumps({
            'type': 'command',
            'command': command,
            'session_id': self.websocket_thread.session_id if self.websocket_thread else 'test'
        })
        
        if self.websocket_thread:
            self.websocket_thread.send_message(message)
            print(f"📤 Komut: {command}")
    
    def toggle_mode(self):
        """Admin modu değiştir"""
        # TODO: Implement
        QMessageBox.information(self, "Mod", "Mod değiştirme henüz aktif değil")
    
    def logout(self):
        """Çıkış yap"""
        reply = QMessageBox.question(
            self, 
            'Çıkış', 
            'Çıkmak istediğinize emin misiniz?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.websocket_thread:
                self.websocket_thread.stop()
            self.close()
    
    def closeEvent(self, event):
        """Pencere kapatılıyor"""
        try:
            if hasattr(self, 'websocket_thread') and self.websocket_thread:
                self.websocket_thread.stop()
                self.websocket_thread.wait()
            
            if self.full_features:
                if hasattr(self, 'updater') and self.updater: 
                    self.updater.stop()
                if hasattr(self, 'ws') and self.ws: 
                    self.ws.disconnect()
                if hasattr(self, 'db') and self.db: 
                    self.db.close()
        except Exception as e:
            print(f"⚠️ Kapanış hatası: {e}")
        event.accept()


# ==================== MAIN ====================
def main():
    app = QApplication(sys.argv)
    
    # Dark mode
    app.setStyle("Fusion")
    
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.ColorRole.Window, QColor(13, 17, 23))
    dark_palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
    dark_palette.setColor(QPalette.ColorRole.Base, QColor(22, 27, 34))
    dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(13, 17, 23))
    dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(25, 25, 25))
    dark_palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
    dark_palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
    dark_palette.setColor(QPalette.ColorRole.Button, QColor(48, 54, 61))
    dark_palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
    dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
    
    app.setPalette(dark_palette)
    
    # Stil
    app.setStyleSheet("""
        QMainWindow { background-color: #0d1117; }
        QWidget { background-color: #0d1117; color: #c9d1d9; }
        QTabWidget::pane { border: 1px solid #30363d; background: #161b22; border-radius: 8px; }
        QTabBar::tab { 
            background: #21262d; 
            padding: 10px 20px; 
            color: #8b949e;
            border-radius: 4px;
            margin: 2px;
        }
        QTabBar::tab:selected { 
            background: #1f6feb; 
            color: white; 
        }
        QTabBar::tab:hover {
            background: #30363d;
        }
        QPushButton {
            background-color: #21262d;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 8px 16px;
            color: #c9d1d9;
        }
        QPushButton:hover {
            background-color: #30363d;
            border-color: #58a6ff;
        }
        QPushButton:checked {
            background-color: #238636;
            border-color: #2ea043;
        }
        QLineEdit {
            background-color: #0d1117;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 8px;
            color: #c9d1d9;
        }
        QLineEdit:focus {
            border-color: #58a6ff;
        }
    """)
    
    window = KumesOtomasyonMainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()