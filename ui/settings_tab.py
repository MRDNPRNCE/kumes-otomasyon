# -*- coding: utf-8 -*-
"""
Ayarlar Sekmesi - Dinamik Kümes Bilgileri Düzenleme
Hem WebSocket ayarları hem de kümes bilgileri düzenlenebilir
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, 
    QLineEdit, QPushButton, QMessageBox, QSpinBox, QFormLayout,
    QScrollArea, QFrame, QTabWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
import json


class SettingsTab(QWidget):
    """
    Ayarlar sekmesi - 2 alt sekme:
    1. WebSocket Bağlantı Ayarları
    2. Kümes Bilgileri Düzenleme
    """
    
    # Signal: Kümes bilgileri değiştiğinde
    kumesInfoChanged = pyqtSignal(dict)  # {kumes_id: {ad, tavuk, gunluk, icon}}
    
    def __init__(self, ws_bridge, kumes_bilgileri=None, parent=None):
        super().__init__(parent)
        self.ws = ws_bridge
        
        # Kümes bilgileri
        if kumes_bilgileri is None:
            from core.config import KUMES_BILGILERI
            self.kumes_bilgileri = KUMES_BILGILERI.copy()
        else:
            self.kumes_bilgileri = kumes_bilgileri.copy()
        
        # Widget referansları
        self.kumes_widgets = {}
        
        self._init_ui()
        self._connect_signals()
        self._update_connection_status()
    
    def _init_ui(self):
        """Ana arayüzü oluşturur"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Tab Widget oluştur
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background: transparent;
            }
            QTabBar::tab {
                background: #21262d;
                color: #8b949e;
                padding: 12px 24px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: bold;
                font-size: 13px;
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
        
        # SEKME 1: WebSocket Ayarları
        websocket_tab = self._create_websocket_tab()
        tabs.addTab(websocket_tab, "📡 Bağlantı Ayarları")
        
        # SEKME 2: Kümes Bilgileri
        kumes_tab = self._create_kumes_info_tab()
        tabs.addTab(kumes_tab, "🏠 Kümes Bilgileri")
        
        layout.addWidget(tabs)
    
    def _create_websocket_tab(self) -> QWidget:
        """WebSocket bağlantı ayarları sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Bağlantı Durumu
        self._create_status_panel(layout)
        
        # Bağlantı Ayarları
        self._create_connection_settings(layout)
        
        # Bilgi Notları
        self._create_info_section(layout)
        
        # Test Butonu
        self._create_test_button(layout)
        
        layout.addStretch()
        
        return widget
    
    def _create_kumes_info_tab(self) -> QWidget:
        """Kümes bilgileri düzenleme sekmesi"""
        widget = QWidget()
        main_layout = QVBoxLayout(widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Başlık
        title = QLabel("🏠 KÜMES BİLGİLERİNİ DÜZENLE")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #58a6ff; padding: 15px; background: rgba(88,166,255,0.1); border-radius: 8px;")
        main_layout.addWidget(title)
        
        # Açıklama
        info = QLabel("Kümes isimlerini, tavuk sayılarını ve günlük değerleri düzenleyebilirsiniz.")
        info.setStyleSheet("color: #8b949e; font-size: 12px; padding: 10px;")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(info)
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(15)
        
        # Her kümes için kart oluştur
        for kumes_id in sorted(self.kumes_bilgileri.keys()):
            card = self._create_kumes_edit_card(kumes_id)
            scroll_layout.addWidget(card)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)
        
        # Kaydet Butonu
        save_btn = QPushButton("💾 Tüm Değişiklikleri Kaydet")
        save_btn.setStyleSheet("""
            QPushButton {
                background: #48bb78;
                color: white;
                border: none;
                padding: 15px 30px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #38a169;
            }
            QPushButton:pressed {
                background: #2f855a;
            }
        """)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self._save_all_kumes_info)
        main_layout.addWidget(save_btn)
        
        return widget
    
    def _create_kumes_edit_card(self, kumes_id: int) -> QFrame:
        """
        Tek bir kümes için düzenleme kartı oluşturur
        
        Args:
            kumes_id: Kümes ID'si
            
        Returns:
            QFrame: Düzenleme kartı
        """
        info = self.kumes_bilgileri[kumes_id]
        
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: #21262d;
                border: 2px solid #30363d;
                border-radius: 12px;
                padding: 20px;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(15)
        
        # Başlık satırı
        header = QHBoxLayout()
        
        # İkon ve başlık
        icon_label = QLabel(info.get('icon', '🏠'))
        icon_label.setFont(QFont("Segoe UI", 32))
        header.addWidget(icon_label)
        
        title_label = QLabel(f"Kümes {kumes_id}")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #58a6ff;")
        header.addWidget(title_label)
        
        header.addStretch()
        
        layout.addLayout(header)
        
        # Form alanları
        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        # Ad
        ad_input = QLineEdit()
        ad_input.setText(info.get('ad', ''))
        ad_input.setPlaceholderText("Kümes adı girin...")
        ad_input.setStyleSheet(self._get_input_style())
        ad_input.setMaxLength(50)
        form.addRow(self._create_label("📝 İsim:"), ad_input)
        
        # İkon
        icon_input = QLineEdit()
        icon_input.setText(info.get('icon', '🏠'))
        icon_input.setPlaceholderText("Emoji girin (🏠, 🐣, 🏡)...")
        icon_input.setStyleSheet(self._get_input_style())
        icon_input.setMaxLength(4)
        form.addRow(self._create_label("🎨 İkon:"), icon_input)
        
        # Tavuk sayısı
        tavuk_input = QSpinBox()
        tavuk_input.setRange(0, 10000)
        tavuk_input.setValue(info.get('tavuk_sayisi', 0))
        tavuk_input.setSuffix(" tavuk")
        tavuk_input.setStyleSheet(self._get_spinbox_style())
        form.addRow(self._create_label("🐔 Tavuk Sayısı:"), tavuk_input)
        
        # Günlük
        gunluk_input = QSpinBox()
        gunluk_input.setRange(0, 365)
        gunluk_input.setValue(info.get('gunluk', 0))
        gunluk_input.setSuffix(" günlük")
        gunluk_input.setStyleSheet(self._get_spinbox_style())
        form.addRow(self._create_label("📅 Yaş:"), gunluk_input)
        
        layout.addLayout(form)
        
        # Widget'ları sakla
        self.kumes_widgets[kumes_id] = {
            'ad': ad_input,
            'icon': icon_input,
            'tavuk': tavuk_input,
            'gunluk': gunluk_input
        }
        
        # Önizleme butonu
        preview_btn = QPushButton("👁️ Önizleme")
        preview_btn.setStyleSheet("""
            QPushButton {
                background: #30363d;
                color: #c9d1d9;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #484f58;
            }
        """)
        preview_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        preview_btn.clicked.connect(lambda: self._preview_kumes(kumes_id))
        layout.addWidget(preview_btn, alignment=Qt.AlignmentFlag.AlignRight)
        
        return card
    
    def _create_label(self, text: str) -> QLabel:
        """Form label'ı oluşturur"""
        label = QLabel(text)
        label.setStyleSheet("color: #c9d1d9; font-weight: bold; font-size: 13px;")
        return label
    
    def _get_input_style(self) -> str:
        """Input field stili"""
        return """
            QLineEdit {
                background: #161b22;
                border: 2px solid #30363d;
                border-radius: 6px;
                padding: 10px;
                color: #c9d1d9;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #58a6ff;
            }
        """
    
    def _get_spinbox_style(self) -> str:
        """SpinBox stili"""
        return """
            QSpinBox {
                background: #161b22;
                border: 2px solid #30363d;
                border-radius: 6px;
                padding: 10px;
                color: #c9d1d9;
                font-size: 13px;
            }
            QSpinBox:focus {
                border-color: #58a6ff;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background: #30363d;
                border: none;
                width: 20px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background: #484f58;
            }
        """
    
    def _preview_kumes(self, kumes_id: int):
        """Kümes bilgilerini önizleme göster"""
        widgets = self.kumes_widgets[kumes_id]
        
        ad = widgets['ad'].text()
        icon = widgets['icon'].text()
        tavuk = widgets['tavuk'].value()
        gunluk = widgets['gunluk'].value()
        
        msg = QMessageBox(self)
        msg.setWindowTitle(f"Kümes {kumes_id} Önizleme")
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setText(f"""
        <h2 style='color: #58a6ff;'>{icon} {ad}</h2>
        <p style='font-size: 14px;'>
        <b>🐔 Tavuk Sayısı:</b> {tavuk}<br>
        <b>📅 Yaş:</b> {gunluk} günlük
        </p>
        """)
        msg.setStyleSheet("""
            QMessageBox {
                background: #161b22;
            }
            QLabel {
                color: #c9d1d9;
            }
        """)
        msg.exec()
    
    def _save_all_kumes_info(self):
        """Tüm kümes bilgilerini kaydeder"""
        updated_info = {}
        
        for kumes_id, widgets in self.kumes_widgets.items():
            ad = widgets['ad'].text().strip()
            icon = widgets['icon'].text().strip()
            tavuk = widgets['tavuk'].value()
            gunluk = widgets['gunluk'].value()
            
            # Validasyon
            if not ad:
                QMessageBox.warning(
                    self,
                    "Uyarı",
                    f"Kümes {kumes_id} için isim boş olamaz!"
                )
                return
            
            if not icon:
                icon = "🏠"  # Varsayılan
            
            updated_info[kumes_id] = {
                'ad': ad,
                'icon': icon,
                'tavuk_sayisi': tavuk,
                'gunluk': gunluk
            }
        
        # Bilgileri güncelle
        self.kumes_bilgileri = updated_info
        
        # Dosyaya kaydet (opsiyonel)
        self._save_to_file()
        
        # Signal gönder
        self.kumesInfoChanged.emit(updated_info)
        
        # Başarı mesajı
        msg = QMessageBox(self)
        msg.setWindowTitle("Başarılı")
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setText("✅ Tüm kümes bilgileri kaydedildi!")
        msg.setInformativeText("Değişiklikler uygulandı. Ana ekranda güncellenmiş bilgileri görebilirsiniz.")
        msg.setStyleSheet("""
            QMessageBox {
                background: #161b22;
            }
            QLabel {
                color: #c9d1d9;
            }
        """)
        msg.exec()
        
        print("✅ Kümes bilgileri güncellendi:")
        for kid, info in updated_info.items():
            print(f"  Kümes {kid}: {info['icon']} {info['ad']} - {info['tavuk_sayisi']} tavuk, {info['gunluk']}g")
    
    def _save_to_file(self):
        """Kümes bilgilerini dosyaya kaydeder (JSON)"""
        try:
            with open('kumes_bilgileri.json', 'w', encoding='utf-8') as f:
                json.dump(self.kumes_bilgileri, f, ensure_ascii=False, indent=2)
            print("💾 Kümes bilgileri dosyaya kaydedildi: kumes_bilgileri.json")
        except Exception as e:
            print(f"⚠️ Dosyaya kayıt hatası: {e}")
    
    def get_kumes_bilgileri(self) -> dict:
        """Güncel kümes bilgilerini döndürür"""
        return self.kumes_bilgileri.copy()
    
    # ==================== WEBSOCKET BÖLÜMÜ ====================
    
    def _create_status_panel(self, parent_layout):
        """Bağlantı durumu paneli"""
        status_group = QGroupBox("📊 Bağlantı Durumu")
        status_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #30363d;
                border-radius: 10px;
                margin-top: 15px;
                padding: 15px;
                background: #21262d;
                color: #58a6ff;
                font-size: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        layout = QVBoxLayout()
        
        self.status_label = QLabel("🔌 Bağlantı durumu kontrol ediliyor...")
        self.status_label.setStyleSheet("font-size: 13px; color: #c9d1d9; padding: 10px;")
        layout.addWidget(self.status_label)
        
        status_group.setLayout(layout)
        parent_layout.addWidget(status_group)
    
    def _create_connection_settings(self, parent_layout):
        """Bağlantı ayarları"""
        settings_group = QGroupBox("⚙️ Bağlantı Ayarları")
        settings_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #30363d;
                border-radius: 10px;
                margin-top: 15px;
                padding: 15px;
                background: #21262d;
                color: #58a6ff;
                font-size: 14px;
        }
    """)
    
        form = QFormLayout()
        form.setSpacing(15)
    
    # IP Adresi
        self.ip_input = QLineEdit()
        self.ip_input.setText(self.ws.ip)  # ✅ DÜZELT: esp_ip → ip
        self.ip_input.setPlaceholderText("192.168.1.150")
        self.ip_input.setStyleSheet(self._get_input_style())
        form.addRow(self._create_label("🌐 ESP32 IP Adresi:"), self.ip_input)
    
    # Port
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(self.ws.port)  # ✅ DÜZELT: ws_port → port
        self.port_input.setStyleSheet(self._get_spinbox_style())
        form.addRow(self._create_label("🔌 Port:"), self.port_input)
    
        settings_group.setLayout(form)
        parent_layout.addWidget(settings_group)
    
    # Kaydet Butonu
        save_btn = QPushButton("💾 Kaydet ve Yeniden Bağlan")
        save_btn.setStyleSheet("""
            QPushButton {
                background: #1f6feb;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 13px;
        }
            QPushButton:hover {
                background: #0969da;
        }
    """)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self._save_and_reconnect)
        parent_layout.addWidget(save_btn)

    def _create_info_section(self, parent_layout):
        """Bilgi notu"""
        info = QLabel("ℹ️ ESP32 cihazınızın IP adresini ve port numarasını girin.")
        info.setStyleSheet("""
            background: rgba(88,166,255,0.1);
            color: #8b949e;
            padding: 12px;
            border-radius: 8px;
            font-size: 12px;
        """)
        info.setWordWrap(True)
        parent_layout.addWidget(info)
    
    def _create_test_button(self, parent_layout):
        """Test butonu"""
        test_btn = QPushButton("🔍 Bağlantıyı Test Et")
        test_btn.setStyleSheet("""
            QPushButton {
                background: #30363d;
                color: #c9d1d9;
                border: 2px solid #484f58;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #484f58;
                border-color: #58a6ff;
            }
        """)
        test_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        test_btn.clicked.connect(self._test_connection)
        parent_layout.addWidget(test_btn)
    
    def _connect_signals(self):
        """Signal bağlantıları"""
        self.ws.connectionChanged.connect(self._update_connection_status)
    
    def _update_connection_status(self):
        """Bağlantı durumunu günceller"""
    # WebSocketBridge'de 'connected' özelliği var mı kontrol et
        is_connected = getattr(self.ws, 'is_connected', 
                       getattr(self.ws, 'connected', False))
    
        if is_connected:
           self.status_label.setText("✅ Bağlı - WebSocket aktif")
           self.status_label.setStyleSheet("font-size: 13px; color: #48bb78; padding: 10px; font-weight: bold;")
        else:
           self.status_label.setText("❌ Bağlı Değil")
           self.status_label.setStyleSheet("font-size: 13px; color: #ff4444; padding: 10px; font-weight: bold;")

    def _save_and_reconnect(self):
        """Ayarları kaydeder ve yeniden bağlanır"""
        new_ip = self.ip_input.text().strip()
        new_port = self.port_input.value()
        
        # Validasyon
        if not new_ip:
            QMessageBox.warning(self, "Uyarı", "IP adresi boş olamaz!")
            return
        
        # Bağlantıyı kes
        self.ws.disconnect()
        
        # Yeni ayarları uygula
        self.ws.ip = new_ip
        self.ws.port = new_port
        
        # Yeniden bağlan
        self.ws.connect()
        
        QMessageBox.information(
            self,
            "Başarılı",
            f"Yeni bağlantı:\nIP: {new_ip}\nPort: {new_port}"
        )
    
    def _test_connection(self):
        """Bağlantıyı test eder"""
    # WebSocketBridge'de 'connected' özelliği var mı kontrol et
        is_connected = getattr(self.ws, 'is_connected', 
                       getattr(self.ws, 'connected', False))
    
        if is_connected:
           QMessageBox.information(
            self,
            "Bağlantı Testi",
            "✅ WebSocket bağlantısı aktif!\n\nVeri alışverişi yapılıyor."
        )
        else:
           QMessageBox.warning(
            self,
            "Bağlantı Testi",
            "❌ Bağlantı yok!\n\nLütfen IP ve Port ayarlarını kontrol edin."
        )