# -*- coding: utf-8 -*-
"""
Kümes Otomasyon Sistemi - Ana Pencere (Responsive Versiyon)
✅ Responsive layout (büyük/küçük ekran desteği)
✅ Minimum boyutlar tanımlı
✅ Dinamik yeniden boyutlandırma
✅ Sekmeli yapı korundu
"""

import sys
import json
import asyncio
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QStackedWidget, QFrame, QLabel, QGridLayout, QScrollArea, QPushButton, 
    QMessageBox, QDialog, QSizePolicy
)
from PyQt6.QtCore import QTimer, Qt, QSize, QTimer, pyqtSignal, QObject, QThread
from PyQt6.QtGui import QFont, QPalette, QColor
import websockets

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
from core.user_manager import UserManager, User
from ui.login_window import LoginWindow
from ui.user_management_tab import UserManagementTab
from core.session_manager import SessionManager


class KumesOtomasyonMainWindow(QMainWindow):
    """
    Ana pencere sınıfı - Responsive sol panel tasarımı
    
    Özellikler:
    - Responsive layout (küçük ekranlarda düzgün görünür)
    - Minimum/maksimum boyutlar
    - Scroll desteği
    - Dinamik kümes kartları
    """
    
    def __init__(self, initial_ip: str = DEFAULT_ESP_IP):
        super().__init__()

        self.user_mgr = UserManager()
        self.current_user = None

         # Session manager oluştur
        self.session_manager = SessionManager()
        
        # Signals bağla
        self.session_manager.ui_update_required.connect(self.update_ui_permissions)
        self.session_manager.auth_success.connect(self.on_auth_success)
        

        self.kumes_bilgileri = KUMES_BILGILERI.copy()
        
        print("\n" + "=" * 70)
        print("🏠 KÜMES OTOMASYON SİSTEMİ - RESPONSIVE VERSİYON")
        print("=" * 70)
        print(f"   IP  : {DEFAULT_ESP_IP}")
        print(f"   Port: {WS_PORT}")
        print(f"   Responsive: ✅ Aktif")
        print("=" * 70 + "\n")
        
        # Pencere ayarları - Responsive
        self.setWindowTitle(APP_TITLE)
        
        # Minimum ve tercih edilen boyutlar
        self.setMinimumSize(1200, 700)  # Minimum boyut
        self.resize(1600, 900)          # Başlangıç boyutu
        
        # Core bileşenler
        self.db = DatabaseManager()
        self.ws = WebSocketBridge(initial_ip)
        self.alarm_mgr = AlarmManager(self.db)
        self.updater = RealTimeDataUpdater(self.ws)
        
        # Veri depoları
        self.kumes_widgets = {}
        self.kumes_data = {}
        
        # UI'ı başlat
        #self._init_ui()
        #self._connect_signals()
        
        # Bağlantıyı başlat
        self.ws.connect()
        self.updater.start()
        
        # Test alarmı (opsiyonel)
        self._add_test_alarms()

        self._show_login()

    def _show_login(self):
        """Login ekranını göster"""
        self.login_window = LoginWindow(self.user_mgr)
        self.login_window.loginSuccessful.connect(self._on_login_success)
        self.login_window.show()

        self.hide()
    
    def on_auth_success(self, data):
        """Auth başarılı"""
        print(f"✅ Auth başarılı: {data}")
    
        if hasattr(self, 'login_dialog'):
           self.login_dialog.accept()
    
        self.update_ui_permissions()
        self.update_header()
        self.update_info_banner()

    def on_auth_failed(self, message):
        """Auth başarısız"""
        print(f"❌ Auth başarısız: {message}")

    def _on_login_success(self, user: User):
        """Login başarılı olunca"""
        self.current_user = user
        print(f"✅ Giriş başarılı: {user.full_name} ({user.role})")
        
        # Ana pencereyi başlat
        self._init_ui()
        self._connect_signals()
        self._start_services()
        
        role_icon = "🔑" if user.role == 'admin' else "👤"
        role_text = "Yönetici" if user.role == 'admin' else "Kullanıcı"
        self.setWindowTitle(
            f"🏠 Kümes Otomasyon Sistemi - {user.full_name} ({role_text})"
        )
        
        # Pencereyi göster
        self.show()
        
        # Başlık çubuğuna kullanıcı bilgisi ekle
        self.setWindowTitle(
            f"🏠 Kümes Otomasyon Sistemi - "
            f"{user.full_name} ({'Yönetici' if user.role == 'admin' else 'Kullanıcı'})"
        )
    
    def _start_services(self):
        """Servisleri başlat"""
        print("🚀 Servisler başlatılıyor...")
    
    # WebSocket'e bağlan
        if hasattr(self, 'ws') and self.ws:
           print("  📡 WebSocket bağlanıyor...")
        self.ws.connect()
    
    # AutoUpdater'ı başlat
        if hasattr(self, 'updater') and self.updater:
           print("  🔄 AutoUpdater başlatılıyor...")
        self.updater.start()
    
        print("✅ Servisler başlatıldı!")

    def _init_ui(self):
        """Ana kullanıcı arayüzünü oluşturur - Responsive"""
        self.setGeometry(100, 100, 1600, 900)  # Başlangıç
        self.setMinimumSize(1000, 600)         # En küçük
        central = QWidget()
        self.setCentralWidget(central)
        self.settings_tab = SettingsTab(
            self.ws,
            kumes_bilgileri=self.kumes_bilgileri  # ← Bilgileri ver
        )
        #tabs.addTab(self.settings_tab, "⚙️ Ayarlar")
        
        # Ana Layout - Yatay (Sol + Sağ)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(20)
        
        # ==================== SOL PANEL (RESPONSIVE) ====================
        left_panel = self._create_responsive_left_panel()
        main_layout.addWidget(left_panel, stretch=0)
        
        # ==================== SAĞ PANEL (SEKMELİ) ====================
        right_panel = self._create_tabbed_right_panel()
        main_layout.addWidget(right_panel, stretch=1)
    
    def _create_responsive_left_panel(self) -> QWidget:
        """
        Responsive sol panel oluşturur
        - Scroll desteği
        - Minimum/maksimum genişlik
        - Dinamik boyutlandırma
        """
        # Scroll alanı için container
        panel = QWidget()
    
    # ✅ YENİ: Genişlik sınırları
        panel.setMinimumWidth(250)  # En dar
        panel.setMaximumWidth(400)  # En geniş
    
    # ✅ YENİ: Size policy
        panel.setSizePolicy(
        QSizePolicy.Policy.Preferred,   # Tercih edilen
        QSizePolicy.Policy.Expanding    # Yükseklik genişler
    )
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Scroll içeriği
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(15)
        scroll_layout.setContentsMargins(5, 5, 5, 5)
        
        # Panel genişlik ayarları
        scroll_area.setMinimumWidth(350)   # Minimum genişlik
        scroll_area.setMaximumWidth(450)   # Maksimum genişlik
        
        # Stil
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        # ==================== BAŞLIK ====================
        title = QLabel("📋 KÜMES LİSTESİ")
        title.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        title.setStyleSheet("""
            color: #58a6ff; 
            padding: 10px;
            background-color: #161b22;
            border-radius: 8px;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scroll_layout.addWidget(title)
        
        # ==================== KÜMES KARTLARI GRİDİ ====================
        grid_container = QWidget()
        grid_layout = QGridLayout(grid_container)
        grid_layout.setSpacing(12)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        
        # 3 kümes kartı oluştur
        for i in range(1, 4):
            card = self._create_responsive_kumes_card(i)
            row = (i - 1) // 2
            col = (i - 1) % 2
            grid_layout.addWidget(card, row, col)
            
            # Widget referanslarını sakla
            self.kumes_widgets[i] = {
                'frame': card,
                'icon': card.findChild(QLabel, 'icon'),
                'name': card.findChild(QLabel, 'name'),
                'temp': card.findChild(QLabel, 'temp'),
                'status': card.findChild(QLabel, 'status'),
                'tavuk': card.findChild(QLabel, 'tavuk'),
                'gunluk': card.findChild(QLabel, 'gunluk')
            }
        
        scroll_layout.addWidget(grid_container)
        
        # ==================== SİSTEM DURUM PANELİ ====================
        self.system_panel = self._create_enhanced_status_panel()
        scroll_layout.addWidget(self.system_panel)
        
        scroll_layout.addStretch()
        
        # Scroll içeriğini ayarla
        scroll_area.setWidget(scroll_content)
        
        return scroll_area
    
    def _create_responsive_kumes_card(self, kumes_id: int) -> QFrame:
        """
        Responsive kümes kartı oluşturur
        - Dinamik boyutlandırma
        - Minimum/maksimum boyutlar
        """
        # Kümes bilgilerini al
        info = KUMES_BILGILERI.get(kumes_id, {
            "ad": f"Kümes {kumes_id}",
            "tavuk_sayisi": 0,
            "gunluk": 0,
            "icon": "🏠"
        })
        
        # Kart frame'i
        card = QFrame()
        
        card.setSizePolicy(
        QSizePolicy.Policy.Expanding,   # Genişlik esnek
        QSizePolicy.Policy.Fixed        # Yükseklik sabit
    )
        card.setMinimumHeight(140)
        card.setMaximumHeight(180)
        card.setObjectName(f"kumes_{kumes_id}")
        
        # Responsive boyutlar
        card.setMinimumSize(160, 200)  # Minimum
        card.setMaximumSize(200, 250)  # Maksimum
        
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.setStyleSheet("""
            QFrame {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #21262d, stop:1 #161b22
                );
                border: 3px solid #30363d;
                border-radius: 12px;
            }
            QFrame:hover {
                border-color: #58a6ff;
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2d3748, stop:1 #1a202c
                );
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(4)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # İkon
        icon = QLabel(info.get("icon", "🏠"))
        icon.setObjectName("icon")
        icon.setFont(QFont("Segoe UI", 32))
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon)
        
        # İsim
        name = QLabel(info["ad"])
        name.setObjectName("name")
        name.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name.setStyleSheet("color: #c9d1d9;")
        name.setWordWrap(True)  # Uzun isimler için
        layout.addWidget(name)
        
        # Sıcaklık
        temp = QLabel("-- °C")
        temp.setObjectName("temp")
        temp.setFont(QFont("Segoe UI", 9))
        temp.setAlignment(Qt.AlignmentFlag.AlignCenter)
        temp.setStyleSheet("color: #f85149; font-weight: bold;")
        layout.addWidget(temp)
        
        # Tavuk sayısı
        tavuk = QLabel(f"🐔 {info['tavuk_sayisi']}")
        tavuk.setObjectName("tavuk")
        tavuk.setFont(QFont("Segoe UI", 8))
        tavuk.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tavuk.setStyleSheet("color: #9ae6b4;")
        layout.addWidget(tavuk)
        
        # Günlük
        gun = QLabel(f"📅 {info['gunluk']}g")
        gun.setObjectName("gunluk")
        gun.setFont(QFont("Segoe UI", 8))
        gun.setAlignment(Qt.AlignmentFlag.AlignCenter)
        gun.setStyleSheet("color: #9ae6b4;")
        layout.addWidget(gun)
        
        # Durum
        status = QLabel("● Normal")
        status.setObjectName("status")
        status.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status.setStyleSheet("color: #48bb78;")
        layout.addWidget(status)
        
        # Tıklama olayı
        card.mousePressEvent = lambda e, kid=kumes_id: self._on_kumes_clicked(kid)
        self.kumes_widgets[kumes_id] = {
            'frame': card,
            'icon': icon,      # ← EKLE
            'name': name,      # ← EKLE
            'temp': temp,
            'status': status,
            'tavuk': tavuk,    # ← EKLE
            'gunluk': gun      # ← EKLE
    }
        layout.addStretch()
        return card
    
    def _create_enhanced_status_panel(self) -> QFrame:
        """
        Responsive sistem durum panelini oluşturur
        """
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #161b22;
                border: 2px solid #30363d;
                border-radius: 12px;
                padding: 12px;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setSpacing(10)
        
        # Başlık
        title = QLabel("📊 SİSTEM DURUMU")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #58a6ff; border: none; padding: 8px;")
        layout.addWidget(title)
        
        # Bağlantı durumu
        self.connection_status = self._create_status_row("🔌", "Bağlantı", "Bekleniyor...")
        layout.addWidget(self.connection_status)
        
        # Ortalama sıcaklık
        self.avg_temp = self._create_status_row("🌡️", "Ort. Sıc.", "--°C")
        layout.addWidget(self.avg_temp)
        
        # Ortalama nem
        self.avg_hum = self._create_status_row("💧", "Ort. Nem", "--%")
        layout.addWidget(self.avg_hum)
        
        # Yem seviyesi
        self.feed_level = self._create_status_row("🌾", "Yem", "-- cm")
        layout.addWidget(self.feed_level)
        
        # Pompa durumu
        self.pump_status = self._create_status_row("💦", "Pompa", "Kapalı")
        layout.addWidget(self.pump_status)
        
        # Çalışma süresi
        self.uptime = self._create_status_row("⏱️", "Çalışma", "00:00:00")
        layout.addWidget(self.uptime)
        
        # Toplam alarm
        self.total_alarms = self._create_status_row("⚠️", "Alarm", "0")
        layout.addWidget(self.total_alarms)
        
        return panel
    
    def _create_status_row(self, icon: str, label: str, value: str) -> QWidget:
        """
        Durum satırı widget'ı oluşturur (responsive)
        """
        container = QWidget()
        container.setStyleSheet("""
            QWidget {
                background: rgba(22, 27, 34, 0.5);
                border-radius: 6px;
                padding: 6px 10px;
            }
        """)
        
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # İkon
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Segoe UI", 12))
        icon_label.setStyleSheet("background: transparent;")
        layout.addWidget(icon_label)
        
        # Etiket
        label_widget = QLabel(label)
        label_widget.setFont(QFont("Segoe UI", 9))
        label_widget.setStyleSheet("color: #8b949e; background: transparent;")
        layout.addWidget(label_widget)
        
        layout.addStretch()
        
        # Değer
        value_label = QLabel(value)
        value_label.setObjectName("value")
        value_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        value_label.setStyleSheet("color: #c9d1d9; background: transparent;")
        layout.addWidget(value_label)
        
        return container
    
    def _create_tabbed_right_panel(self) -> QTabWidget:
        """
        Sekmeli sağ paneli oluşturur
        """
        self.tabs = QTabWidget()
        self.tabs.setSizePolicy(
        QSizePolicy.Policy.Expanding,   # Genişlik esnek
        QSizePolicy.Policy.Expanding    # Yükseklik esnek
    )
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #30363d;
                background: #161b22;
                border-radius: 10px;
                padding: 5px;
            }
            QTabBar::tab {
                background: #21262d;
                color: #8b949e;
                padding: 10px 18px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-weight: bold;
                font-size: 12px;
                min-width: 80px;
            }
            QTabBar::tab:selected {
                background: #1f6feb;
                color: white;
            }
            QTabBar::tab:hover {
                background: #30363d;
                color: #c9d1d9;
            }
        """)
        
        # SEKME 1: Detay
        self.detail_tab = QStackedWidget()
        welcome = QLabel("👈 Sol taraftan bir kümes seçin")
        welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome.setFont(QFont("Segoe UI", 16))
        welcome.setStyleSheet("color: #8b949e; padding: 50px;")
        self.detail_tab.addWidget(welcome)
        self.tabs.addTab(self.detail_tab, "📊 Detay")
        
        # SEKME 2: Kontrol
        self.control_panel = ControlPanel(self.ws)
       # if not self.user_mgr.is_admin():
            # User için kontrol panelini devre dışı bırak
          #  self.control_panel.setEnabled(False)
           # self.control_panel.setToolTip("⚠️ Bu özellik sadece yöneticiler için")
        scroll_control = QScrollArea()
        scroll_control.setWidgetResizable(True)
        scroll_control.setWidget(self.control_panel)
        scroll_control.setStyleSheet("QScrollArea { border: none; }")
        self.tabs.addTab(scroll_control, "🎮 Kontrol")
        
        # SEKME 3: Alarmlar
        self.alarm_view = AlarmView(self.alarm_mgr)
        #if not self.user_mgr.is_admin():
            # User için alarm temizleme butonlarını gizle
            # AlarmView içinde handle edilecek
           # pass
        self.tabs.addTab(self.alarm_view, "⚠️ Alarmlar")
        
        # SEKME 4: Ayarlar
        self.settings_tab = SettingsTab(self.ws, kumes_bilgileri=self.kumes_bilgileri)
        if not self.user_mgr.is_admin():
            # User için ayarları devre dışı bırak
            self.settings_tab.setEnabled(False)
            self.settings_tab.setToolTip("⚠️ Bu özellik sadece yöneticiler için")
        
        self.tabs.addTab(self.settings_tab, "⚙️ Ayarlar")

        if self.user_mgr.is_admin():
            self.user_mgmt_tab = UserManagementTab(self.user_mgr)
            self.tabs.addTab(self.user_mgmt_tab, "👥 Kullanıcılar")
        
        # ============ YENİ SEKME 6: Profil ============
        self.profile_tab = self._create_profile_tab()
        self.tabs.addTab(self.profile_tab, "👤 Profil")
        
        return self.tabs
    
    def _create_profile_tab(self) -> QWidget:
        """Profil sekmesi - Tüm kullanıcılar için"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Başlık
        title = QLabel("👤 PROFİL BİLGİLERİ")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #58a6ff; padding: 15px; background: rgba(88,166,255,0.1); border-radius: 8px;")
        layout.addWidget(title)
        
        # Kullanıcı bilgileri
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background: #161b22;
                border: 2px solid #30363d;
                border-radius: 12px;
                padding: 30px;
            }
        """)
        
        info_layout = QVBoxLayout(info_frame)
        info_layout.setSpacing(15)
        
        user = self.current_user
        
        # Bilgiler
        info_items = [
            ("👤 Kullanıcı Adı:", user.username),
            ("📝 Tam Ad:", user.full_name),
            ("🔑 Rol:", "Yönetici" if user.role == 'admin' else "Kullanıcı"),
            ("📅 Hesap Oluşturulma:", user.created_at),
            ("🕒 Son Giriş:", user.last_login or "İlk giriş")
        ]
        
        for label, value in info_items:
            row = QHBoxLayout()
            
            lbl = QLabel(label)
            lbl.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
            lbl.setStyleSheet("color: #c9d1d9;")
            row.addWidget(lbl)
            
            val = QLabel(value)
            val.setFont(QFont("Segoe UI", 12))
            val.setStyleSheet("color: #8b949e;")
            row.addWidget(val)
            
            row.addStretch()
            info_layout.addLayout(row)
        
        layout.addWidget(info_frame)
        
        # Şifre değiştirme butonu
        change_pwd_btn = QPushButton("🔒 Şifremi Değiştir")
        change_pwd_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        change_pwd_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        change_pwd_btn.setStyleSheet("""
            QPushButton {
                background: #1f6feb;
                color: white;
                border: none;
                padding: 15px 30px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: #58a6ff;
            }
        """)
        change_pwd_btn.clicked.connect(self._change_my_password)
        layout.addWidget(change_pwd_btn)
        
        # Çıkış butonu
        logout_btn = QPushButton("🚪 Çıkış Yap")
        logout_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        logout_btn.setStyleSheet("""
            QPushButton {
                background: #ff4444;
                color: white;
                border: none;
                padding: 15px 30px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: #cc0000;
            }
        """)
        logout_btn.clicked.connect(self._logout)
        layout.addWidget(logout_btn)
        
        layout.addStretch()
        
        return widget
    
    def _change_my_password(self):
        """Kendi şifresini değiştir"""
        from ui.user_management_tab import ChangePasswordDialog
        
        dialog = ChangePasswordDialog(self.current_user.username, self.user_mgr, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            old_pwd, new_pwd = dialog.get_data()
            
            success = self.user_mgr.change_password(
                self.current_user.username, 
                old_pwd, 
                new_pwd
            )
            
            if success:
                QMessageBox.information(
                    self,
                    "Başarılı",
                    "✅ Şifreniz değiştirildi!"
                )
            else:
                QMessageBox.warning(
                    self,
                    "Hata",
                    "❌ Şifre değiştirilemedi! Eski şifrenizi kontrol edin."
                )
    
    def _logout(self):
        """Çıkış yap"""
        reply = QMessageBox.question(
            self,
            "Çıkış",
            "Çıkış yapmak istediğinizden emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Servisleri durdur
            self.updater.stop()
            self.ws.disconnect()
            
            # Kullanıcıyı çıkar
            self.user_mgr.logout()
            
            # Pencereyi kapat
            self.close()
            
            # Login ekranını tekrar göster
            self._show_login()

    def _connect_signals(self):
        """Sinyalleri ilgili slot'lara bağlar"""
        self.ws.dataReceived.connect(self._handle_data)
        self.ws.connectionChanged.connect(self._on_connection_changed)
        self.alarm_mgr.alarmAdded.connect(self._update_alarm_display)
        self.alarm_mgr.alarmCleared.connect(self._update_alarm_display)
        self.alarm_mgr.alarmCleared.connect(self._on_alarm_cleared)
        self.settings_tab.kumesInfoChanged.connect(
            self._on_kumes_info_changed)

    def _on_kumes_info_changed(self, updated_info: dict):
        """Kümes bilgileri değiştiğinde"""
        self.kumes_bilgileri = updated_info
        
        # Kartları güncelle
        for kumes_id, info in updated_info.items():
            if kumes_id in self.kumes_widgets:
                self._update_kumes_card_info(kumes_id, info)
    
    def _update_kumes_card_info(self, kumes_id: int, info: dict):
        """Kart bilgilerini güncelle"""
        widgets = self.kumes_widgets[kumes_id]
        
        widgets['icon'].setText(info['icon'])
        widgets['name'].setText(info['ad'])
        widgets['tavuk'].setText(f"🐔 {info['tavuk_sayisi']} tavuk")
        widgets['gunluk'].setText(f"📅 {info['gunluk']} günlük")

    def _on_alarm_cleared(self, kumes_id: int):
        """Alarm temizlendiğinde"""
        print(f"🔔 Alarm temizlendi: Kümes {kumes_id}")
        self._update_kumes_card_alarm(kumes_id, has_alarm=False)
        self._update_alarm_display()

    def _handle_data(self, raw_json: str):
        """WebSocket'ten gelen JSON verisini işler"""
        try:
            data = json.loads(raw_json)
            
            if 'kumesler' in data:
                temps = []
                hums = []
                
                for kumes in data['kumesler']:
                    kumes_id = kumes.get('id')
                    self.kumes_data[kumes_id] = kumes
                    
                    if kumes_id in self.kumes_widgets:
                        # Sıcaklık güncelle
                        temp = kumes.get('sicaklik', 0)
                        temps.append(temp)
                        self.kumes_widgets[kumes_id]['temp'].setText(f"{temp:.1f}°C")
                        
                        # Nem
                        hum = kumes.get('nem', 0)
                        hums.append(hum)
                        
                        # Alarm kontrolü
                        has_alarm = kumes.get('alarm', False)
                        self._update_kumes_card_alarm(kumes_id, has_alarm)
                        
                        if has_alarm:
                            mesaj = kumes.get('mesaj', 'Alarm!')
                            self.alarm_mgr.add_alarm(kumes_id, mesaj)
                
                # Ortalamalar
                if temps:
                    avg_t = sum(temps) / len(temps)
                    self.avg_temp.findChild(QLabel, "value").setText(f"{avg_t:.1f}°C")
                
                if hums:
                    avg_h = sum(hums) / len(hums)
                    self.avg_hum.findChild(QLabel, "value").setText(f"{avg_h:.1f}%")
            
            # Sistem bilgileri
            if 'yem' in data:
                self.feed_level.findChild(QLabel, "value").setText(f"{data['yem']} cm")
            
            if 'pompa' in data:
                status = "Açık" if data['pompa'] else "Kapalı"
                color = "#48bb78" if data['pompa'] else "#8b949e"
                value_label = self.pump_status.findChild(QLabel, "value")
                value_label.setText(status)
                value_label.setStyleSheet(f"color: {color}; background: transparent; font-weight: bold;")
            
            if 'zaman' in data:
                seconds = data['zaman']
                hours = seconds // 3600
                minutes = (seconds % 3600) // 60
                secs = seconds % 60
                self.uptime.findChild(QLabel, "value").setText(f"{hours:02d}:{minutes:02d}:{secs:02d}")
            
            # Detay sekmesini güncelle
            if self.detail_tab.currentWidget() and isinstance(self.detail_tab.currentWidget(), KumesCard):
                current_id = self.detail_tab.currentWidget().kumes_id
                if current_id in self.kumes_data:
                    self.detail_tab.currentWidget().update_data(self.kumes_data[current_id])
                    
        except json.JSONDecodeError as e:
            print(f"❌ JSON parse hatası: {e}")
        except Exception as e:
            print(f"❌ Veri işleme hatası: {e}")
    
    def _update_kumes_card_alarm(self, kumes_id: int, has_alarm: bool):
        """Kümes kartının alarm durumunu günceller"""
        if kumes_id not in self.kumes_widgets:
            return
        
        status_label = self.kumes_widgets[kumes_id]['status']
        card_frame = self.kumes_widgets[kumes_id]['frame']
        
        if has_alarm:
            status_label.setText("⚠️ ALARM")
            status_label.setStyleSheet("color: #ff4444; font-weight: bold;")
            
            current_style = card_frame.styleSheet()
            new_style = current_style.replace(
                "border: 3px solid #30363d",
                "border: 3px solid #ff4444"
            )
            card_frame.setStyleSheet(new_style)
        else:
            status_label.setText("● Normal")
            status_label.setStyleSheet("color: #48bb78; font-weight: bold;")
            
            current_style = card_frame.styleSheet()
            new_style = current_style.replace(
                "border: 3px solid #ff4444",
                "border: 3px solid #30363d"
            )
            card_frame.setStyleSheet(new_style)
    
    def _update_alarm_display(self):
        """Genel alarm sayısını günceller"""
        count = self.alarm_mgr.get_alarm_count()
        color = "#ff4444" if count > 0 else "#8b949e"
        
        value_label = self.total_alarms.findChild(QLabel, "value")
        if value_label:
            value_label.setText(str(count))
            value_label.setStyleSheet(f"color: {color}; background: transparent; font-weight: bold;")

    def _on_connection_changed(self, connected: bool):
        """Bağlantı durumu değiştiğinde"""
        status = "Bağlı ✓" if connected else "Bağlı Değil"
        color = "#48bb78" if connected else "#ff4444"
        
        self.setWindowTitle(f"{APP_TITLE} - {status}")
        
        value_label = self.connection_status.findChild(QLabel, "value")
        if value_label:
            value_label.setText(status)
            value_label.setStyleSheet(f"color: {color}; background: transparent; font-weight: bold;")

    def _on_kumes_clicked(self, kumes_id: int):
        """Kümes kartına tıklandığında"""
        # Önceki detay widget'ları temizle
        while self.detail_tab.count() > 1:
            widget = self.detail_tab.widget(1)
            self.detail_tab.removeWidget(widget)
            widget.deleteLater()
        
        # Yeni detay kartı oluştur
        detail_card = KumesCard(kumes_id)
        if kumes_id in self.kumes_data:
            detail_card.update_data(self.kumes_data[kumes_id])
        
        self.detail_tab.addWidget(detail_card)
        self.detail_tab.setCurrentWidget(detail_card)
        self.tabs.setCurrentIndex(0)
        
        print(f"✓ Kümes {kumes_id} seçildi")

    def _add_test_alarms(self):
        """Test alarmı (opsiyonel)"""
        QTimer.singleShot(4000, self._create_test_alarm)

    def _create_test_alarm(self):
        """Test alarmı oluştur"""
        print("\n🧪 Test alarmı ekleniyor...")
        self.alarm_mgr.add_alarm(2, "TEST: Yüksek sıcaklık!")
        self._update_kumes_card_alarm(2, True)

    def resizeEvent(self, event):
        """Pencere boyutu değiştiğinde - Responsive davranış"""
        super().resizeEvent(event)
        # Gelecekte ekstra responsive davranışlar eklenebilir
        # Örn: Çok küçük ekranlarda layout değişimi
    
    def update_ui_permissions(self):
        """UI'yi yetkilere göre güncelle"""
        can_control = self.session_manager.can_control
        is_admin = (self.session_manager.role == 'admin')
        admin_active = (is_admin and self.session_manager.admin_mode == 'active')
    
        print(f"📊 UI Yetkileri Güncelleniyor:")
        print(f"   - can_control: {can_control}")
        print(f"   - is_admin: {is_admin}")
        print(f"   - admin_active: {admin_active}")
    
    # Kontrol panelindeki butonları bul ve güncelle
        if hasattr(self, 'control_panel'):
        # Eğer ControlPanel'de set_controls_enabled metodu varsa
           if hasattr(self.control_panel, 'set_controls_enabled'):
            self.control_panel.set_controls_enabled(can_control)
           else:
            # Yoksa manuel olarak butonları güncelle
            for widget in self.control_panel.findChildren(QPushButton):
                widget.setEnabled(can_control)
    
    # Ayarlar sekmesini güncelle (sadece admin aktif modda)
        if hasattr(self, 'settings_tab'):
           self.settings_tab.setEnabled(admin_active)
    
    # TabWidget'teki ayarlar sekmesini kontrol et
        if hasattr(self, 'tab_widget'):
           for i in range(self.tab_widget.count()):
            tab_text = self.tab_widget.tabText(i)
            if "Ayarlar" in tab_text or "Settings" in tab_text:
                self.tab_widget.setTabEnabled(i, admin_active)
                print(f"   - Ayarlar sekmesi: {'Aktif' if admin_active else 'Devre dışı'}")
    
    # Header güncelle
        self.update_header()
    
    # Info banner güncelle
        self.update_info_banner()

    def update_header(self):
        """Header'daki kullanıcı bilgisini güncelle"""
        if not hasattr(self, 'user_info_label'):
           print("⚠️ Header label bulunamadı")
           return
    
    # Kullanıcı bilgisi
        user_text = self.session_manager.get_user_info_text()
        badge_text = self.session_manager.get_badge_text()
    
    # Tam metni oluştur
        if badge_text:
            full_text = f"{user_text} [{badge_text}]"
        else:
            full_text = user_text
    
        self.user_info_label.setText(full_text)
    
    # Mod butonu (sadece admin için)
        if hasattr(self, 'mode_button'):
            button_text = self.session_manager.get_mode_button_text()
            if button_text:
               self.mode_button.setText(button_text)
               self.mode_button.setVisible(True)
               print(f"📋 Mod butonu: {button_text}")
            else:
               self.mode_button.setVisible(False)
    
        print(f"📋 Header güncellendi: {full_text}")

    def update_info_banner(self):
        """Bilgi banner'ını güncelle"""
    # Eğer info_banner yoksa oluştur
        if not hasattr(self, 'info_banner'):
            from PyQt6.QtWidgets import QLabel
            from PyQt6.QtCore import Qt
        
            self.info_banner = QLabel()
            self.info_banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.info_banner.setWordWrap(True)
        
        # Ana layout'un başına ekle
            if hasattr(self, 'main_layout'):
            # İlk widget olarak ekle
                self.main_layout.insertWidget(0, self.info_banner)
                print("📢 Info banner oluşturuldu")
    
    # Banner metnini al
        banner_text = self.session_manager.get_info_banner_text()
        self.info_banner.setText(banner_text)
    
    # Banner rengini ve stilini ayarla
        if self.session_manager.role == 'admin':
            if self.session_manager.admin_mode == 'active':
            # Yeşil - Admin Aktif
                style = """
                QLabel {
                    background-color: rgba(76, 175, 80, 0.15);
                    border: 2px solid #4CAF50;
                    color: #2E7D32;
                    padding: 12px 20px;
                    margin: 5px;
                    border-radius: 8px;
                    font-weight: bold;
                    font-size: 13px;
                }
            """
            else:
            # Mavi - Admin İzleme
                style = """
                QLabel {
                    background-color: rgba(33, 150, 243, 0.15);
                    border: 2px solid #2196F3;
                    color: #1565C0;
                    padding: 12px 20px;
                    margin: 5px;
                    border-radius: 8px;
                    font-weight: bold;
                    font-size: 13px;
                }
            """
        else:
            if self.session_manager.can_control:
            # Yeşil - User Kontrol
                style = """
                QLabel {
                    background-color: rgba(76, 175, 80, 0.15);
                    border: 2px solid #4CAF50;
                    color: #2E7D32;
                    padding: 12px 20px;
                    margin: 5px;
                    border-radius: 8px;
                    font-weight: bold;
                    font-size: 13px;
                }
            """
            else:
            # Turuncu - User Sadece İzleme
                style = """
                QLabel {
                    background-color: rgba(255, 152, 0, 0.15);
                    border: 2px solid #FF9800;
                    color: #E65100;
                    padding: 12px 20px;
                    margin: 5px;
                    border-radius: 8px;
                    font-weight: bold;
                    font-size: 13px;
                }
            """
    
        self.info_banner.setStyleSheet(style)
        print(f"📢 Banner güncellendi: {banner_text}")

    def on_mode_button_clicked(self):
        """Admin mod değiştirme butonu tıklandı"""
        if self.session_manager.role != 'admin':
            print("⚠️ Sadece admin mod değiştirebilir!")
            return
    
        current_mode = self.session_manager.admin_mode
    
        if current_mode == 'active':
        # İzleme moduna geç
            print("🔄 İzleme moduna geçiliyor...")
            self.session_manager.switch_mode('watching')
        else:
        # Aktif moda geç
            print("🔄 Aktif moda geçiliyor...")
            self.session_manager.switch_mode('active')

    def on_logout(self):
        """Çıkış yap"""
        from PyQt6.QtWidgets import QMessageBox
    
        reply = QMessageBox.question(
            self, 
            'Çıkış', 
            'Çıkış yapmak istediğinizden emin misiniz?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    )
    
        if reply == QMessageBox.StandardButton.Yes:
            print("👋 Çıkış yapılıyor...")
            self.session_manager.logout()
            self.close()

    def closeEvent(self, event):
        """Pencere kapatılırken"""
        try:
            print("\n🔄 Uygulama kapatılıyor...")
            
            if hasattr(self, 'updater') and self.updater:
                self.updater.stop()
            
            if hasattr(self, 'ws') and self.ws:
                self.ws.disconnect()
            
            if hasattr(self, 'db') and self.db:
                self.db.close()
            
            print("✓ Kaynaklar temizlendi")
        except Exception as e:
            print(f"❌ Kapatma hatası: {e}")
        
        event.accept()


def main():
    """Uygulamayı başlatır"""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Dark theme
    dark_theme = """
        QMainWindow {
            background-color: #0d1117;
        }
        QWidget {
            background-color: #0d1117;
            color: #c9d1d9;
        }
        QTabWidget::pane {
            border: 1px solid #30363d;
            background: #161b22;
        }
        QTabBar::tab {
            background: #21262d;
            padding: 10px 20px;
            color: #8b949e;
            border: none;
        }
        QTabBar::tab:selected {
            background: #1f6feb;
            color: white;
        }
        QTabBar::tab:hover {
            background: #30363d;
            color: #c9d1d9;
        }
        QScrollBar:vertical {
            background: #0d1117;
            width: 12px;
            border-radius: 6px;
        }
        QScrollBar::handle:vertical {
            background: #30363d;
            border-radius: 6px;
            min-height: 20px;
        }
        QScrollBar::handle:vertical:hover {
            background: #58a6ff;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
    """
    app.setStyleSheet(dark_theme)
    
    # Ana pencereyi oluştur ve göster
    window = KumesOtomasyonMainWindow()
    #window.show()
    
    print("✅ Uygulama başlatıldı")
    print("📱 Responsive mod aktif")
    print("📏 Minimum boyut: 1200x700")
    print("🎯 Tercih edilen: 1600x900")
    print("📱 Mobil WebSocket: ws://{}:{}".format(DEFAULT_ESP_IP, WS_PORT))
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()