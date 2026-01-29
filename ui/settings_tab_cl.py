from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, 
    QLineEdit, QPushButton, QMessageBox, QSpinBox, QFormLayout
)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QIntValidator
import re


class SettingsTab(QWidget):
    """ESP32 Bağlantı Ayarları Sekmesi"""

    def __init__(self, ws_bridge, parent=None):
        super().__init__(parent)
        self.ws = ws_bridge
        self._init_ui()
        self._connect_signals()
        self._update_connection_status()
        

    def _init_ui(self):
        """Arayüz bileşenlerini oluşturur"""
        # Ana Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # 1. Bağlantı Durumu Paneli
        self._create_status_panel(layout)

        # 2. Bağlantı Ayarları Grubu
        self._create_connection_settings(layout)

        # 3. Bilgi Notları
        self._create_info_section(layout)

        # 4. Test Bağlantısı Butonu
        self._create_test_button(layout)

        layout.addStretch()  # İçeriği yukarı it

    def _create_status_panel(self, parent_layout):
        """Bağlantı durumu panelini oluşturur"""
        status_group = QGroupBox("Bağlantı Durumu")
        status_group.setStyleSheet("""
            QGroupBox { 
                font-weight: bold; 
                border: 2px solid #cbd5e0; 
                border-radius: 10px; 
                margin-top: 15px; 
                padding: 15px;
            }
            QGroupBox::title { 
                subcontrol-origin: margin; 
                left: 15px; 
                padding: 0 5px; 
            }
        """)

        status_layout = QFormLayout()

        # Durum etiketi
        self.status_label = QLabel("●")
        self.status_label.setStyleSheet("font-size: 14px; color: #718096;")
        status_layout.addRow("Durum:", self.status_label)

        # IP bilgisi
        self.current_ip_label = QLabel(self.ws.ip)
        self.current_ip_label.setStyleSheet("font-size: 13px; color: #4a5568; font-family: monospace;")
        status_layout.addRow("Mevcut IP:", self.current_ip_label)

        # Port bilgisi
        self.current_port_label = QLabel(str(self.ws.port))
        self.current_port_label.setStyleSheet("font-size: 13px; color: #4a5568; font-family: monospace;")
        status_layout.addRow("Port:", self.current_port_label)

        status_group.setLayout(status_layout)
        parent_layout.addWidget(status_group)

    def _create_connection_settings(self, parent_layout):
        """Bağlantı ayarları grubunu oluşturur"""
        conn_group = QGroupBox("Donanım Bağlantı Bilgileri")
        conn_group.setStyleSheet("""
            QGroupBox { 
                font-weight: bold; 
                border: 2px solid #cbd5e0; 
                border-radius: 10px; 
                margin-top: 15px; 
                padding: 20px;
            }
            QGroupBox::title { 
                subcontrol-origin: margin; 
                left: 15px; 
                padding: 0 5px; 
            }
        """)

        group_layout = QVBoxLayout()

        # IP Giriş Alanı
        ip_label = QLabel("ESP32 IP Adresi:")
        ip_label.setStyleSheet("font-size: 13px; color: #4a5568; font-weight: bold;")

        self.ip_input = QLineEdit()
        self.ip_input.setText(self.ws.ip)
        self.ip_input.setPlaceholderText("Örn: 192.168.1.150 veya localhost")
        self.ip_input.setStyleSheet("""
            QLineEdit { 
                padding: 12px; 
                border: 1px solid #e2e8f0; 
                border-radius: 5px; 
                font-size: 15px; 
                background: white;
                font-family: monospace;
            }
            QLineEdit:focus { border: 2px solid #667eea; }
        """)

        # Port Giriş Alanı
        port_label = QLabel("WebSocket Port:")
        port_label.setStyleSheet("font-size: 13px; color: #4a5568; font-weight: bold;")

        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(self.ws.port)
        self.port_input.setStyleSheet("""
            QSpinBox { 
                padding: 10px; 
                border: 1px solid #e2e8f0; 
                border-radius: 5px; 
                font-size: 15px; 
                background: white;
            }
            QSpinBox:focus { border: 2px solid #667eea; }
        """)

        # Butonlar
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        # Kaydet ve Bağlan Butonu
        self.apply_btn = QPushButton("💾 Kaydet ve Yeniden Bağlan")
        self.apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #4c51bf; 
                color: white; 
                padding: 15px; 
                border-radius: 5px; 
                font-weight: bold; 
                font-size: 14px;
            }
            QPushButton:hover { background-color: #5a67d8; }
            QPushButton:pressed { background-color: #434190; }
        """)
        self.apply_btn.clicked.connect(self._handle_save)

        # Varsayılana Dön Butonu
        reset_btn = QPushButton("🔄 Varsayılana Dön")
        reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #718096; 
                color: white; 
                padding: 15px; 
                border-radius: 5px; 
                font-weight: bold; 
                font-size: 14px;
            }
            QPushButton:hover { background-color: #4a5568; }
        """)
        reset_btn.clicked.connect(self._reset_to_default)

        button_layout.addWidget(self.apply_btn)
        button_layout.addWidget(reset_btn)

        # Elemanları Gruba Ekle
        group_layout.addWidget(ip_label)
        group_layout.addWidget(self.ip_input)
        group_layout.addSpacing(10)
        group_layout.addWidget(port_label)
        group_layout.addWidget(self.port_input)
        group_layout.addSpacing(15)
        group_layout.addLayout(button_layout)

        conn_group.setLayout(group_layout)
        parent_layout.addWidget(conn_group)

    def _create_info_section(self, parent_layout):
        """Bilgi notları bölümünü oluşturur"""
        info_label = QLabel(
            "ℹ️ <b>Not:</b> IP/Port değişikliği sonrası sistem otomatik olarak "
            "eski bağlantıyı koparıp yenisine bağlanmaya çalışacaktır.<br>"
            "Bağlantı kurulana kadar 3-5 saniye bekleyiniz."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet(
            "color: #718096; font-size: 12px; "
            "background-color: #edf2f7; padding: 12px; "
            "border-radius: 5px; border-left: 4px solid #667eea;"
        )
        parent_layout.addWidget(info_label)

    def _create_test_button(self, parent_layout):
        """Test bağlantısı butonunu oluşturur"""
        test_btn = QPushButton("🔌 Bağlantıyı Test Et")
        test_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        test_btn.setStyleSheet("""
            QPushButton {
                background-color: #48bb78; 
                color: white; 
                padding: 12px; 
                border-radius: 5px; 
                font-weight: bold; 
                font-size: 13px;
            }
            QPushButton:hover { background-color: #38a169; }
        """)
        test_btn.clicked.connect(self._test_connection)
        parent_layout.addWidget(test_btn)

    def _connect_signals(self):
        """WebSocket sinyallerini bağlar"""
        if hasattr(self.ws, 'connectionChanged'):
            self.ws.connectionChanged.connect(self._update_connection_status)

    def _validate_ip(self, ip: str) -> bool:
        """
        IP adresinin geçerliliğini kontrol eder
        
        Args:
            ip: Kontrol edilecek IP adresi
            
        Returns:
            bool: Geçerliyse True
        """
        # localhost kontrolü
        if ip.lower() in ['localhost', '127.0.0.1']:
            return True

        # IPv4 formatı kontrolü
        ipv4_pattern = r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$'
        match = re.match(ipv4_pattern, ip)

        if not match:
            return False

        # Her oktetin 0-255 arasında olduğunu kontrol et
        octets = match.groups()
        return all(0 <= int(octet) <= 255 for octet in octets)

    def _handle_save(self):
        """IP ve Port kontrolü yapar ve bağlantıyı günceller"""
        new_ip = self.ip_input.text().strip()
        new_port = self.port_input.value()

        # Boş kontrolü
        if not new_ip:
            QMessageBox.warning(self, "Uyarı", "IP adresi boş bırakılamaz!")
            self.ip_input.setFocus()
            return

        # IP Format doğrulaması
        if not self._validate_ip(new_ip):
            QMessageBox.critical(
                self, 
                "Geçersiz IP", 
                f"'{new_ip}' geçerli bir IP adresi değil!\n\n"
                "Geçerli formatlar:\n"
                "• 192.168.1.100\n"
                "• localhost\n"
                "• 127.0.0.1"
            )
            self.ip_input.selectAll()
            self.ip_input.setFocus()
            return

        # Değişiklik var mı kontrol et
        if new_ip == self.ws.ip and new_port == self.ws.port:
            QMessageBox.information(
                self, 
                "Bilgi", 
                "Ayarlar zaten güncel. Değişiklik yapılmadı."
            )
            return

        # Onay iste
        reply = QMessageBox.question(
            self,
            "Bağlantıyı Güncelle",
            f"Yeni bağlantı ayarları:\n\n"
            f"IP: {new_ip}\n"
            f"Port: {new_port}\n\n"
            f"Mevcut bağlantı kesilip yenisi kurulacak. Devam edilsin mi?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            # WebSocketBridge.update_ip metodunu çağır
            self.ws.update_ip(new_ip, new_port)

            # Etiketleri güncelle
            self.current_ip_label.setText(new_ip)
            self.current_port_label.setText(str(new_port))

            QMessageBox.information(
                self,
                "Bağlantı Güncellendi",
                f"✓ Yeni IP: {new_ip}\n"
                f"✓ Yeni Port: {new_port}\n\n"
                f"Sistem yeniden bağlanıyor..."
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Hata",
                f"Bağlantı güncellenirken hata oluştu:\n\n{str(e)}"
            )

    def _reset_to_default(self):
        """Ayarları varsayılana döndürür"""
        from core.config import DEFAULT_ESP_IP, WS_PORT

        reply = QMessageBox.question(
            self,
            "Varsayılana Dön",
            f"Ayarlar varsayılan değerlere döndürülecek:\n\n"
            f"IP: {DEFAULT_ESP_IP}\n"
            f"Port: {WS_PORT}\n\n"
            f"Devam edilsin mi?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.ip_input.setText(DEFAULT_ESP_IP)
            self.port_input.setValue(WS_PORT)
            
            QMessageBox.information(
                self,
                "Sıfırlandı",
                "Ayarlar varsayılana döndürüldü.\n"
                "Değişiklikleri uygulamak için 'Kaydet' butonuna tıklayın."
            )

    @pyqtSlot()
    def _test_connection(self):
        """Mevcut bağlantıyı test eder"""
        if self.ws.is_connected():
            info = self.ws.get_connection_info()
            QMessageBox.information(
                self,
                "Bağlantı Başarılı ✓",
                f"ESP32'ye başarıyla bağlı!\n\n"
                f"IP: {info['ip']}\n"
                f"Port: {info['port']}\n"
                f"Durum: Aktif"
            )
        else:
            QMessageBox.warning(
                self,
                "Bağlantı Yok ✗",
                "ESP32'ye bağlantı kurulamadı.\n\n"
                "Lütfen:\n"
                "• IP adresini kontrol edin\n"
                "• ESP32'nin çalıştığından emin olun\n"
                "• Ağ bağlantısını kontrol edin"
            )

    @pyqtSlot(bool)
    def _update_connection_status(self, connected: bool = None):
        """Bağlantı durumu etiketini günceller"""
        if connected is None:
            connected = self.ws.is_connected()

        if connected:
            self.status_label.setText("● Bağlı")
            self.status_label.setStyleSheet("font-size: 14px; color: #48bb78; font-weight: bold;")
        else:
            self.status_label.setText("● Bağlı Değil")
            self.status_label.setStyleSheet("font-size: 14px; color: #f56565; font-weight: bold;")

    def _save_kumes_info(self):
        # main pencereye eriş (veya sinyal ile haber ver)
        # Şimdilik basitçe print yapalım
        for i in range(1, 4):
            print(f"Kümes {i}: {self.name_edits[i].text()}, "
                  f"{self.tavuk_edits[i].text()} tavuk, "
                  f"{self.gunluk_edits[i].text()} günlük")