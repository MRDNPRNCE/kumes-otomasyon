from PyQt6.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget, QGridLayout, QFrame
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, pyqtSignal
from collections import deque

# Config import'ları - eksik olanlar için varsayılan değerler
try:
    from core.config import CARD_BORDER_COLOR, ALARM_COLOR, SUCCESS_COLOR
except ImportError:
    CARD_BORDER_COLOR = "#667eea"
    ALARM_COLOR = "#d32f2f"
    SUCCESS_COLOR = "#2e7d32"

# PyQtGraph import - opsiyonel
try:
    from pyqtgraph import PlotWidget, mkPen
    GRAPH_AVAILABLE = True
except ImportError:
    GRAPH_AVAILABLE = False
    print("⚠️ PyQtGraph bulunamadı. Grafikler devre dışı.")

# Graph ayarları
try:
    from core.config import GraphSettings
except ImportError:
    class GraphSettings:
        MAX_DATA_POINTS = 100


class KumesCard(QGroupBox):
    """Gelişmiş kümes kartı - Butonlar ve grafiklerle"""
    
    # Sinyaller - Ana pencereye komut göndermek için
    ledToggled = pyqtSignal(int, bool)  # (kumes_id, state)
    fanToggled = pyqtSignal(int, bool)
    doorToggled = pyqtSignal(int, bool)

    def __init__(self, kumes_id: int, parent=None):
        super().__init__(f"🏠 Kümes #{kumes_id}", parent)
        self.kumes_id = kumes_id
        
        # Grafik veri depoları
        self.temp_data = deque(maxlen=GraphSettings.MAX_DATA_POINTS)
        self.hum_data = deque(maxlen=GraphSettings.MAX_DATA_POINTS)
        self.ammonia_data = deque(maxlen=GraphSettings.MAX_DATA_POINTS)
        
        # Mevcut durumlar
        self.led_state = False
        self.fan_state = False
        self.door_state = False
        
        # UI bileşenleri
        self.labels = {}
        self.buttons = {}
        self.plot = None
        self.temp_curve = None
        self.hum_curve = None
        self.ammonia_curve = None
        self.alarm_label = None
        
        self._init_ui()
        self._apply_dark_theme()

    def _init_ui(self):
        """Gelişmiş arayüz bileşenlerini oluşturur"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 20, 15, 15)

        # ÜST KISIM: Grafik
        if GRAPH_AVAILABLE:
            self._create_enhanced_graph()
            main_layout.addWidget(self.plot)

        # ORTA KISIM: Sensör Bilgileri (2 Sütun)
        sensor_widget = self._create_sensor_grid()
        main_layout.addWidget(sensor_widget)

        # BURAYA EKLE: Tavuk sayısı ve günlük
        from core.config import KUMES_BILGILERI
        info = KUMES_BILGILERI.get(self.kumes_id, {"tavuk_sayisi": 0, "gunluk": 0})

        tavuk_lbl = QLabel(f"🐔 Tavuk Sayısı: {info.get('tavuk_sayisi', 0)}")
        tavuk_lbl.setFont(QFont("Segoe UI", 11))
        tavuk_lbl.setStyleSheet("color: #9ae6b4; padding: 5px;")
        main_layout.addWidget(tavuk_lbl)

        gunluk_lbl = QLabel(f"📅 Günlük: {info.get('gunluk', 0)}")
        gunluk_lbl.setFont(QFont("Segoe UI", 11))
        gunluk_lbl.setStyleSheet("color: #9ae6b4; padding: 5px;")
        main_layout.addWidget(gunluk_lbl)

        # ALT KISIM: Kontrol Butonları
        button_widget = self._create_control_buttons()
        main_layout.addWidget(button_widget)

        # EN ALT: Alarm Etiketi
        self.alarm_label = QLabel("")
        self.alarm_label.setWordWrap(True)
        self.alarm_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.alarm_label.setStyleSheet(f"""
            color: {ALARM_COLOR}; 
            font-weight: bold; 
            font-size: 13px;
            padding: 10px;
            background-color: rgba(211, 47, 47, 0.15);
            border-radius: 6px;
            border: 2px solid {ALARM_COLOR};
        """)
        self.alarm_label.setVisible(False)
        main_layout.addWidget(self.alarm_label)

        self.setLayout(main_layout)

    def _create_enhanced_graph(self):
        """Gelişmiş 3 eğrili grafik oluşturur"""
        self.plot = PlotWidget()
        self.plot.setBackground('#0d1117')
        self.plot.showGrid(x=True, y=True, alpha=0.3)
        self.plot.setYRange(0, 100)
        self.plot.setFixedHeight(200)
        
        # Başlık ve eksen etiketleri
        self.plot.setLabel('left', 'Değer', color='#c9d1d9', size='11pt')
        self.plot.setLabel('bottom', 'Zaman', color='#c9d1d9', size='11pt')
        self.plot.setTitle(f'Kümes {self.kumes_id} - Gerçek Zamanlı Grafikler', 
                          color='#58a6ff', size='12pt')
        
        # Legend (açıklama kutusu)
        legend = self.plot.addLegend(offset=(10, 10))
        legend.setBrush('#161b22')
        legend.setPen('#30363d')
        
        # 3 Farklı eğri
        self.temp_curve = self.plot.plot(
            pen=mkPen('#f85149', width=3),  # Kırmızı - Sıcaklık
            name='🌡️ Sıcaklık (°C)'
        )
        self.hum_curve = self.plot.plot(
            pen=mkPen('#58a6ff', width=3),  # Mavi - Nem
            name='💧 Nem (%)'
        )
        self.ammonia_curve = self.plot.plot(
            pen=mkPen('#ffa657', width=3),  # Turuncu - Amonyak
            name='🌫️ Amonyak (ppm)'
        )

    def _create_sensor_grid(self):
        """Sensör bilgilerini 2 sütunlu grid'de gösterir"""
        widget = QWidget()
        grid = QGridLayout(widget)
        grid.setSpacing(12)  # Arttırıldı
        grid.setContentsMargins(5, 5, 5, 5)

        sensors = [
            ("temp", "🌡️", "Sıcaklık", "-- °C", "#f85149", 0, 0),
            ("hum", "💧", "Nem", "-- %", "#58a6ff", 0, 1),
            ("ammonia", "🌫️", "Amonyak", "-- ppm", "#ffa657", 1, 0),
            ("su", "💦", "Su", "-- ml", "#4299e1", 1, 1),
            ("isik", "💡", "Işık", "-- lux", "#d69e2e", 2, 0),
        ]

        for key, icon, name, default, color, row, col in sensors:
            lbl = QLabel(f"{icon} {name}: {default}")
            lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            lbl.setStyleSheet(f"""
                color: {color};
                padding: 10px 12px;
                background-color: rgba(22, 27, 34, 0.5);
                border-radius: 6px;
                border-left: 4px solid {color};
                min-height: 35px;
            """)
            lbl.setWordWrap(False)  # Metinlerin kırılmasını engelle
            grid.addWidget(lbl, row, col)
            self.labels[key] = lbl

        # Grid sütunlarını eşit genişlikte yap
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        return widget

    def _create_control_buttons(self):
        """Kontrol butonlarını oluşturur"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setSpacing(10)  # Arttırıldı
        layout.setContentsMargins(5, 5, 5, 5)

        # LED Butonu
        self.buttons['led'] = self._create_toggle_button(
            "💡", "LED", "#d69e2e", self._toggle_led
        )
        layout.addWidget(self.buttons['led'])

        # Fan Butonu
        self.buttons['fan'] = self._create_toggle_button(
            "🌀", "FAN", "#58a6ff", self._toggle_fan
        )
        layout.addWidget(self.buttons['fan'])

        # Kapı Butonu
        self.buttons['door'] = self._create_toggle_button(
            "🚪", "KAPI", "#9d4edd", self._toggle_door
        )
        layout.addWidget(self.buttons['door'])

        return widget

    def _create_toggle_button(self, icon, text, color, callback):
        """Toggle butonu oluşturur"""
        btn = QPushButton(f"{icon}\n{text}\nKAPALI")
        btn.setCheckable(True)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))  # Font küçültüldü
        btn.setFixedHeight(75)  # Yükseklik arttırıldı
        btn.setMinimumWidth(100)  # Minimum genişlik
        btn.setSizePolicy(
            btn.sizePolicy().horizontalPolicy(),
            btn.sizePolicy().verticalPolicy()
        )
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #21262d;
                color: #8b949e;
                border: 2px solid #30363d;
                border-radius: 8px;
                padding: 10px;
            }}
            QPushButton:hover {{
                background-color: #30363d;
                border-color: {color};
            }}
            QPushButton:checked {{
                background-color: {color};
                color: white;
                border-color: {color};
                font-weight: bold;
            }}
            QPushButton:pressed {{
                padding-top: 12px;
                padding-bottom: 8px;
            }}
        """)
        btn.clicked.connect(callback)
        return btn

    def _toggle_led(self):
        """LED butonuna tıklandığında"""
        self.led_state = self.buttons['led'].isChecked()
        self.buttons['led'].setText(
            f"💡\nLED\n{'AÇIK' if self.led_state else 'KAPALI'}"
        )
        self.ledToggled.emit(self.kumes_id, self.led_state)

    def _toggle_fan(self):
        """Fan butonuna tıklandığında"""
        self.fan_state = self.buttons['fan'].isChecked()
        self.buttons['fan'].setText(
            f"🌀\nFAN\n{'AÇIK' if self.fan_state else 'KAPALI'}"
        )
        self.fanToggled.emit(self.kumes_id, self.fan_state)

    def _toggle_door(self):
        """Kapı butonuna tıklandığında"""
        self.door_state = self.buttons['door'].isChecked()
        self.buttons['door'].setText(
            f"🚪\nKAPI\n{'AÇIK' if self.door_state else 'KAPALI'}"
        )
        self.doorToggled.emit(self.kumes_id, self.door_state)

    def _apply_dark_theme(self):
        """Dark mode tema uygular"""
        self.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                font-size: 15px;
                border: 3px solid {CARD_BORDER_COLOR};
                border-radius: 12px;
                margin-top: 15px;
                padding: 15px;
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #161b22, stop:1 #0d1117
                );
                color: #c9d1d9;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 10px;
                color: #58a6ff;
                background-color: #0d1117;
            }}
        """)

    def update_data(self, data: dict):
        """WebSocket'ten gelen veriyi güvenli bir şekilde arayüze yansıtır"""
        if not data or data.get('id') != self.kumes_id:
            return

        # Sensör verilerini güncelle
        self._update_sensor_values(data)
        
        # Buton durumlarını güncelle
        self._update_button_states(data)
        
        # Grafikleri güncelle
        if GRAPH_AVAILABLE:
            self._update_graphs(data)
        
        # Alarm kontrolü
        self._update_alarm_status(data)

    def _update_sensor_values(self, data):
        """Sensör değerlerini günceller"""
        # Sıcaklık
        temp = data.get('sicaklik')
        if temp is not None and isinstance(temp, (int, float)):
            self.labels["temp"].setText(f"🌡️ Sıcaklık: {temp:.1f} °C")
        
        # Nem
        hum = data.get('nem')
        if hum is not None and isinstance(hum, (int, float)):
            self.labels["hum"].setText(f"💧 Nem: {hum:.1f} %")
        
        # Amonyak
        amm = data.get('amonyak')
        if amm is not None and isinstance(amm, (int, float)):
            self.labels["ammonia"].setText(f"🌫️ Amonyak: {amm:.1f} ppm")
        
        # Su
        su = data.get('su')
        if su is not None:
            self.labels["su"].setText(f"💦 Su: {su} ml")
        
        # Işık
        isik = data.get('isik')
        if isik is not None:
            self.labels["isik"].setText(f"💡 Işık: {isik} lux")

    def _update_button_states(self, data):
        """Buton durumlarını ESP32'den gelen veriye göre günceller"""
        # LED
        led = data.get('led', False)
        if led != self.led_state:
            self.led_state = led
            self.buttons['led'].setChecked(led)
            self.buttons['led'].setText(f"💡\nLED\n{'AÇIK' if led else 'KAPALI'}")
        
        # Fan
        fan = data.get('fan', False)
        if fan != self.fan_state:
            self.fan_state = fan
            self.buttons['fan'].setChecked(fan)
            self.buttons['fan'].setText(f"🌀\nFAN\n{'AÇIK' if fan else 'KAPALI'}")
        
        # Kapı
        kapi = data.get('kapi', False)
        if kapi != self.door_state:
            self.door_state = kapi
            self.buttons['door'].setChecked(kapi)
            self.buttons['door'].setText(f"🚪\nKAPI\n{'AÇIK' if kapi else 'KAPALI'}")

    def _update_graphs(self, data):
        """Grafikleri günceller - 3 eğri"""
        if not GRAPH_AVAILABLE or not self.plot:
            return
        
        # Sıcaklık
        temp = data.get('sicaklik')
        if temp is not None and isinstance(temp, (int, float)):
            self.temp_data.append(temp)
            self.temp_curve.setData(list(self.temp_data))
        
        # Nem
        hum = data.get('nem')
        if hum is not None and isinstance(hum, (int, float)):
            self.hum_data.append(hum)
            self.hum_curve.setData(list(self.hum_data))
        
        # Amonyak
        amm = data.get('amonyak')
        if amm is not None and isinstance(amm, (int, float)):
            self.ammonia_data.append(amm)
            self.ammonia_curve.setData(list(self.ammonia_data))

    def _create_kumes_card(self, kumes_id):
         info = self.kumes_bilgileri.get(kumes_id, {"ad": f"Kümes {kumes_id}", "tavuk_sayisi": 0, "gunluk": 0})
    
         card = QFrame()
    
    # Dinamik isim
         name = QLabel(info["ad"])  # ← burası artık dinamik
    
    # Tavuk ve günlük gösterimi
         tavuk_lbl = QLabel(f"🐔 {info['tavuk_sayisi']} tavuk")

         gunluk_lbl = QLabel(f"📅 {info['gunluk']} günlük")
    
    def _update_alarm_status(self, data):

        """Alarm durumunu günceller"""
        has_alarm = data.get('alarm', False)
        
        if has_alarm:
            msg = data.get('mesaj', 'Kritik Durum!')
            self.alarm_label.setText(f"⚠️ ALARM: {msg}")
            self.alarm_label.setVisible(True)
            
            # Kart kenarlığını alarm rengine çevir
            self.setStyleSheet(self.styleSheet().replace(
                f"border: 3px solid {CARD_BORDER_COLOR}",
                f"border: 4px solid {ALARM_COLOR}"
            ))
        else:
            self.alarm_label.setVisible(False)
            
            # Normal kenarlığa dön
            self.setStyleSheet(self.styleSheet().replace(
                f"border: 4px solid {ALARM_COLOR}",
                f"border: 3px solid {CARD_BORDER_COLOR}"
            ))