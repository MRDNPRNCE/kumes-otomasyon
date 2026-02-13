# ui/control_panel.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QPushButton,
    QHBoxLayout, QSlider, QLabel, QSpinBox, QGridLayout, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class ControlPanel(QWidget):
    """Manuel kontrol paneli - tüm aktüatörlerin tam kontrolü"""

    def __init__(self, command_sender, parent=None):
        super().__init__(parent)
        self.sender = command_sender  # WebSocketBridge nesnesi
        #self.user_mgr = user_mgr 
        self.setStyleSheet("""
            QPushButton {
                padding: 14px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 10px;
                min-height: 50px;
            }
            QPushButton:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            }
            QPushButton:pressed {
                transform: translateY(1px);
            }
        """)
        self._init_ui()

    def _send_command(self, action: str, kumes: int = None):
        """JSON formatında komut gönder"""
        import json
        cmd = {"action": action}
        if kumes is not None:
            cmd["kumes"] = kumes

        if self.sender and self.sender.is_connected():
            self.sender.send_command(json.dumps(cmd))
            print(f"✅ Komut gönderildi: {cmd}")
        else:
            QMessageBox.warning(
                self,
                "Bağlantı Yok",
                "ESP32'ye bağlı değilsiniz!\n\nLütfen bağlantıyı kontrol edin."
            )

    def _send(self, cmd: str):
        success = self.sender.send_command(cmd)
        if success:
            print(f"Komut gönderildi: {cmd}")
        else:
            print("Bağlantı yok! Komut gönderilemedi.")

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # ===================== FAN KONTROLLERİ =====================
        fan_group = QGroupBox("Fan Kontrolleri")
        fan_group.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        fan_layout = QGridLayout()
        fan_layout.setSpacing(15)

        for i in range(1, 3):  # MAX_KUMES = 3 ama sadece 2 fan var
            col = (i - 1) * 2
            lbl = QLabel(f"Fan {i}")
            lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

            btn_on = QPushButton("AÇ")
            btn_on.setStyleSheet("background-color: #4caf50; color: white;")
            btn_on.clicked.connect(lambda checked, x=i: self._send(f"FAN{x}:1"))

            btn_off = QPushButton("KAPAT")
            btn_off.setStyleSheet("background-color: #f44336; color: white;")
            btn_off.clicked.connect(lambda checked, x=i: self._send(f"FAN{x}:0"))

            fan_layout.addWidget(lbl, 0, col, 1, 2)
            fan_layout.addWidget(btn_on, 1, col)
            fan_layout.addWidget(btn_off, 1, col + 1)

        fan_group.setLayout(fan_layout)
        layout.addWidget(fan_group)

        # ===================== AYDINLATMA KONTROLLERİ =====================
        led_group = QGroupBox("Aydınlatma Kontrolleri")
        led_group.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        led_layout = QHBoxLayout()
        led_layout.setSpacing(20)

        btn_led_on = QPushButton("TÜM IŞIKLARI AÇ")
        btn_led_on.setStyleSheet("background-color: #ffc107; color: black; font-size: 15px;")
        btn_led_on.clicked.connect(lambda: self._send("LED:1"))

        btn_led_off = QPushButton("TÜM IŞIKLARI KAPAT")
        btn_led_off.setStyleSheet("background-color: #424242; color: white; font-size: 15px;")
        btn_led_off.clicked.connect(lambda: self._send("LED:0"))

        led_layout.addWidget(btn_led_on)
        led_layout.addWidget(btn_led_off)
        led_group.setLayout(led_layout)
        layout.addWidget(led_group)

        # ===================== SU SİSTEMİ =====================
        su_group = QGroupBox("Su Sistemi")
        su_group.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        su_layout = QHBoxLayout()
        su_layout.setSpacing(20)

        btn_pompa_on = QPushButton("POMPA BAŞLAT (10 sn)")
        btn_pompa_on.setStyleSheet("background-color: #2196f3; color: white;")
        btn_pompa_on.clicked.connect(lambda: self._send("POMPA:1"))

        btn_pompa_off = QPushButton("POMPA DURDUR")
        btn_pompa_off.setStyleSheet("background-color: #d32f2f; color: white;")
        btn_pompa_off.clicked.connect(lambda: self._send("POMPA:0"))

        su_layout.addWidget(btn_pompa_on)
        su_layout.addWidget(btn_pompa_off)
        su_group.setLayout(su_layout)
        layout.addWidget(su_group)

        # ===================== KAPI KONTROLÜ =====================
        kapi_group = QGroupBox("Kapı Kontrolü")
        kapi_group.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        kapi_layout = QVBoxLayout()

        # Slider + değer gösterimi
        slider_layout = QHBoxLayout()
        slider_lbl = QLabel("Kapı Açısı:")
        slider_lbl.setFont(QFont("Segoe UI", 11))

        self.kapi_slider = QSlider(Qt.Orientation.Horizontal)
        self.kapi_slider.setRange(0, 180)
        self.kapi_slider.setValue(0)
        self.kapi_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.kapi_slider.setTickInterval(30)

        self.angle_label = QLabel("0°")
        self.angle_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.angle_label.setStyleSheet("color: #667eea; min-width: 60px;")

        self.kapi_slider.valueChanged.connect(
            lambda v: [self.angle_label.setText(f"{v}°"), self._send(f"KAPI:{v}")]
        )

        slider_layout.addWidget(slider_lbl)
        slider_layout.addWidget(self.kapi_slider)
        slider_layout.addWidget(self.angle_label)
        kapi_layout.addLayout(slider_layout)

        # Hızlı butonlar
        btn_layout = QHBoxLayout()
        btn_kapat = QPushButton("TAM KAPAT (0°)")
        btn_kapat.setStyleSheet("background-color: #9e9e9e; color: white;")
        btn_kapat.clicked.connect(lambda: [self.kapi_slider.setValue(0), self._send("KAPI:0")])

        btn_yari = QPushButton("YARI AÇIK (45°)")
        btn_yari.setStyleSheet("background-color: #ff9800; color: white;")
        btn_yari.clicked.connect(lambda: [self.kapi_slider.setValue(45), self._send("KAPI:45")])

        btn_ac = QPushButton("TAM AÇ (90°)")
        btn_ac.setStyleSheet("background-color: #4caf50; color: white;")
        btn_ac.clicked.connect(lambda: [self.kapi_slider.setValue(90), self._send("KAPI:90")])

        btn_layout.addWidget(btn_kapat)
        btn_layout.addWidget(btn_yari)
        btn_layout.addWidget(btn_ac)
        kapi_layout.addLayout(btn_layout)

        kapi_group.setLayout(kapi_layout)
        layout.addWidget(kapi_group)

        # ===================== YEM DAĞITMA =====================
        yem_group = QGroupBox("Yem Dağıtma")
        yem_group.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        yem_layout = QHBoxLayout()

        yem_lbl = QLabel("Süre (saniye):")
        yem_lbl.setFont(QFont("Segoe UI", 11))

        self.yem_spin = QSpinBox()
        self.yem_spin.setRange(1, 60)
        self.yem_spin.setValue(5)
        self.yem_spin.setFont(QFont("Segoe UI", 11))

        btn_yem = QPushButton("YEM DAĞIT")
        btn_yem.setStyleSheet("background-color: #8bc34a; color: white; font-size: 16px;")
        btn_yem.clicked.connect(lambda: self._send(f"YEM:{self.yem_spin.value()}"))

        yem_layout.addWidget(yem_lbl)
        yem_layout.addWidget(self.yem_spin)
        yem_layout.addWidget(btn_yem)
        yem_group.setLayout(yem_layout)
        layout.addWidget(yem_group)

        # ===================== OTOMATİK / MANUEL MOD =====================
        mode_group = QGroupBox("Sistem Modu")
        mode_group.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        mode_layout = QHBoxLayout()

        btn_auto_on = QPushButton("OTOMATİK MODU AKTİF ET")
        btn_auto_on.setStyleSheet("background-color: #9c27b0; color: white; font-size: 15px;")
        btn_auto_on.clicked.connect(lambda: self._send("AUTO:1"))

        btn_auto_off = QPushButton("MANUEL MODA GEÇ")
        btn_auto_off.setStyleSheet("background-color: #ff5722; color: white; font-size: 15px;")
        btn_auto_off.clicked.connect(lambda: self._send("AUTO:0"))

        mode_layout.addWidget(btn_auto_on)
        mode_layout.addWidget(btn_auto_off)
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)

        # Boşluk doldur
        layout.addStretch()