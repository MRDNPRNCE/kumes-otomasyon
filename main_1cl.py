# -*- coding: utf-8 -*-
"""
Kümes Otomasyon Sistemi - Ana Pencere
Modern, profesyonel kümes yönetim arayüzü
"""

import sys
import json
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QStackedWidget, QFrame, QLabel, QGridLayout
)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont

from core.config import APP_TITLE, DEFAULT_ESP_IP, WS_PORT, KUMES_BILGILERI
from core.database import DatabaseManager
from core.websocket_bridge import WebSocketBridge
from core.alarm_manager import AlarmManager
from ui.kumes_card import KumesCard
from ui.system_status import SystemStatusPanel
from ui.control_panel import ControlPanel
from ui.alarm_view import AlarmView
from ui.settings_tab_cl import SettingsTab
from data.real_time_updater import RealTimeDataUpdater


class KumesOtomasyonMainWindow(QMainWindow):
    """Ana pencere sınıfı - sol panel tasarım"""
    
    def __init__(self, initial_ip: str = DEFAULT_ESP_IP):
        super().__init__()

        self.kumes_bilgileri = KUMES_BILGILERI.copy()
        
        print("\n" + "=" * 70)
        print("KÜMES OTOMASYON SİSTEMİ - SOL PANEL VERSİYONU")
        print("=" * 70)
        print(f"   IP  : {DEFAULT_ESP_IP}")
        print(f"   Port: {WS_PORT}")
        print("=" * 70 + "\n")
        
        self.setWindowTitle(APP_TITLE)
        self.resize(1600, 900)
        
        # Core bileşenler
        self.db = DatabaseManager()
        self.ws = WebSocketBridge(initial_ip)
        self.alarm_mgr = AlarmManager(self.db)
        self.updater = RealTimeDataUpdater(self.ws)
        
        # Veri depoları
        self.kumes_widgets = {}
        self.kumes_data = {}
        
        # UI'ı başlat
        self._init_ui()
        self._connect_signals()
        
        # Bağlantıyı başlat
        self.ws.connect()
        self.updater.start()
        
        # Test alarmı (opsiyonel - kaldırılabilir)
        self._add_test_alarms()
    
    def _init_ui(self):
        """Ana kullanıcı arayüzünü oluşturur"""
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(20)
        
        # ==================== SOL PANEL ====================
        left_panel = QVBoxLayout()
        
        # Kümes Kareleri Grid
        grid_container = QWidget()
        grid_layout = QGridLayout(grid_container)
        grid_layout.setSpacing(15)
        
        # 3 kümes için kart oluştur
        for i in range(1, 4):
            card = self._create_kumes_card(i)
            row = (i-1) // 2
            col = (i-1) % 2
            grid_layout.addWidget(card, row, col)
            
            # Widget referanslarını sakla
            self.kumes_widgets[i] = {
                'frame': card,
                'icon': card.findChild(QLabel, 'icon'),
                'name': card.findChild(QLabel, 'name'),
                'temp': card.findChild(QLabel, 'temp'),
                'status': card.findChild(QLabel, 'status')
            }
        
        left_panel.addWidget(grid_container)
        left_panel.addStretch()
        
        # Gelişmiş Sistem Durum Paneli
        self.system_panel = self._create_enhanced_status_panel()
        left_panel.addWidget(self.system_panel)
        
        main_layout.addLayout(left_panel, stretch=1)
        
        # ==================== SAĞ PANEL - SEKMELER ====================
        self.tabs = QTabWidget()
        
        # 1. Detay Sekmesi
        self.detail_tab = QStackedWidget()
        welcome = QLabel("Sol taraftan bir kümes seçin")
        welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome.setStyleSheet("font-size: 16px; color: #8b949e;")
        self.detail_tab.addWidget(welcome)
        self.tabs.addTab(self.detail_tab, "Kümes Detay")
        
        # 2. Kontrol Paneli
        self.control_panel = ControlPanel(self.ws)
        self.tabs.addTab(self.control_panel, "Kontrol")
        
        # 3. Alarmlar
        self.alarm_view = AlarmView(self.alarm_mgr)
        self.tabs.addTab(self.alarm_view, "Alarmlar")
        
        # 4. Ayarlar
        self.settings_tab = SettingsTab(self.ws)
        self.tabs.addTab(self.settings_tab, "Ayarlar")
        
        main_layout.addWidget(self.tabs, stretch=3)
    
    def _create_kumes_card(self, kumes_id: int) -> QFrame:
        """
        Sol paneldeki kümes kartını oluşturur
        
        Args:
            kumes_id: Kümes numarası (1-3)
            
        Returns:
            QFrame: Kümes kartı widget'ı
        """
        # Kümes bilgilerini config'den al
        info = KUMES_BILGILERI.get(kumes_id, {
            "ad": f"Kümes {kumes_id}",
            "tavuk_sayisi": 0,
            "gunluk": 0,
            "icon": "🏠"
        })
        
        # Kart frame'i
        card = QFrame()
        card.setFixedSize(180, 240)
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.setObjectName(f"kumes_{kumes_id}")
        card.setStyleSheet("""
            QFrame {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #21262d, stop:1 #161b22
                );
                border: 3px solid #30363d;
                border-radius: 15px;
            }
            QFrame:hover {
                border-color: #58a6ff;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(6)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # İkon
        icon = QLabel(info.get("icon", "🏠"))
        icon.setObjectName("icon")
        icon.setFont(QFont("Segoe UI", 36))
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon)
        
        # İsim
        name = QLabel(info["ad"])
        name.setObjectName("name")
        name.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name.setStyleSheet("color: #c9d1d9;")
        layout.addWidget(name)
        
        # Sıcaklık
        temp = QLabel("-- °C")
        temp.setObjectName("temp")
        temp.setFont(QFont("Segoe UI", 10))
        temp.setAlignment(Qt.AlignmentFlag.AlignCenter)
        temp.setStyleSheet("color: #8b949e;")
        layout.addWidget(temp)
        
        # Tavuk sayısı
        tavuk = QLabel(f"🐔 {info['tavuk_sayisi']} tavuk")
        tavuk.setFont(QFont("Segoe UI", 9))
        tavuk.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tavuk.setStyleSheet("color: #9ae6b4;")
        layout.addWidget(tavuk)
        
        # Günlük
        gun = QLabel(f"📅 {info['gunluk']} günlük")
        gun.setFont(QFont("Segoe UI", 9))
        gun.setAlignment(Qt.AlignmentFlag.AlignCenter)
        gun.setStyleSheet("color: #9ae6b4;")
        layout.addWidget(gun)
        
        # Durum
        status = QLabel("● Normal")
        status.setObjectName("status")
        status.setFont(QFont("Segoe UI", 11))
        status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status.setStyleSheet("color: #48bb78; font-weight: bold;")
        layout.addWidget(status)
        
        # Tıklama olayı
        card.mousePressEvent = lambda e, kid=kumes_id: self._on_kumes_clicked(kid)
        
        return card
    
    def _create_enhanced_status_panel(self) -> QFrame:
        """
        Gelişmiş sistem durum panelini oluşturur
        
        Returns:
            QFrame: Durum paneli widget'ı
        """
        panel = QFrame()
        panel.setFixedWidth(390)
        panel.setStyleSheet("""
            QFrame {
                background-color: #161b22;
                border: 2px solid #30363d;
                border-radius: 12px;
                padding: 15px;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setSpacing(12)
        
        # Başlık
        title = QLabel("📊 SİSTEM DURUMU")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #58a6ff; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Bağlantı durumu
        self.connection_status = self._create_status_row("🔌 Bağlantı", "Bekleniyor...")
        layout.addWidget(self.connection_status)
        
        # Ortalama sıcaklık
        self.avg_temp = self._create_status_row("🌡️ Ort. Sıcaklık", "--°C")
        layout.addWidget(self.avg_temp)
        
        # Ortalama nem
        self.avg_hum = self._create_status_row("💧 Ort. Nem", "--%")
        layout.addWidget(self.avg_hum)
        
        # Yem seviyesi
        self.feed_level = self._create_status_row("🌾 Yem Seviyesi", "-- cm")
        layout.addWidget(self.feed_level)
        
        # Pompa durumu
        self.pump_status = self._create_status_row("💦 Pompa", "Kapalı")
        layout.addWidget(self.pump_status)
        
        # Çalışma süresi
        self.uptime = self._create_status_row("⏱️ Çalışma", "00:00:00")
        layout.addWidget(self.uptime)
        
        # Toplam alarm
        self.total_alarms = self._create_status_row("⚠️ Toplam Alarm", "0")
        layout.addWidget(self.total_alarms)
        
        return panel
    
    def _create_status_row(self, label: str, value: str) -> QWidget:
        """
        Durum satırı widget'ı oluşturur
        
        Args:
            label: Etiket metni
            value: Değer metni
            
        Returns:
            QWidget: Durum satırı
        """
        container = QWidget()
        container.setStyleSheet("""
            QWidget {
                background: rgba(22, 27, 34, 0.5);
                border-radius: 6px;
                padding: 8px 12px;
            }
        """)
        
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Etiket
        label_widget = QLabel(label)
        label_widget.setFont(QFont("Segoe UI", 11))
        label_widget.setStyleSheet("color: #8b949e; background: transparent;")
        layout.addWidget(label_widget)
        
        layout.addStretch()
        
        # Değer
        value_label = QLabel(value)
        value_label.setObjectName("value")
        value_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        value_label.setStyleSheet("color: #c9d1d9; background: transparent;")
        layout.addWidget(value_label)
        
        return container
    
    def _connect_signals(self):
        """Sinyalleri ilgili slot'lara bağlar"""
        self.ws.dataReceived.connect(self._handle_data)
        self.ws.connectionChanged.connect(self._on_connection_changed)
        self.alarm_mgr.alarmAdded.connect(self._update_alarm_display)
        self.alarm_mgr.alarmCleared.connect(self._update_alarm_display)
    
    def _handle_data(self, raw_json: str):
        """
        WebSocket'ten gelen JSON verisini işler
        
        Args:
            raw_json: Ham JSON string
        """
        try:
            data = json.loads(raw_json)
            
            # Kümes kartlarını güncelle
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
                        self.kumes_widgets[kumes_id]['temp'].setText(f"{temp:.1f} °C")
                        
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
                    self.avg_temp.findChild(QLabel, "value").setText(f"{avg_t:.1f} °C")
                
                if hums:
                    avg_h = sum(hums) / len(hums)
                    self.avg_hum.findChild(QLabel, "value").setText(f"{avg_h:.1f} %")
            
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
        """
        Kümes kartının alarm durumunu günceller
        
        Args:
            kumes_id: Kümes ID
            has_alarm: Alarm var mı?
        """
        if kumes_id not in self.kumes_widgets:
            return
        
        status_label = self.kumes_widgets[kumes_id]['status']
        card_frame = self.kumes_widgets[kumes_id]['frame']
        
        if has_alarm:
            status_label.setText("⚠️ ALARM")
            status_label.setStyleSheet("color: #ff4444; font-weight: bold;")
            
            # Kart kenarlığını kırmızı yap
            current_style = card_frame.styleSheet()
            new_style = current_style.replace(
                "border: 3px solid #30363d",
                "border: 3px solid #ff4444"
            )
            card_frame.setStyleSheet(new_style)
        else:
            status_label.setText("● Normal")
            status_label.setStyleSheet("color: #48bb78; font-weight: bold;")
            
            # Kart kenarlığını normale döndür
            current_style = card_frame.styleSheet()
            new_style = current_style.replace(
                "border: 3px solid #ff4444",
                "border: 3px solid #30363d"
            )
            card_frame.setStyleSheet(new_style)
    
    def _update_alarm_display(self):
        """Genel alarm sayısını ve rengini günceller"""
        count = self.alarm_mgr.get_alarm_count()
        color = "#ff4444" if count > 0 else "#8b949e"
        
        value_label = self.total_alarms.findChild(QLabel, "value")
        if value_label:
            value_label.setText(str(count))
            value_label.setStyleSheet(f"color: {color}; background: transparent; font-weight: bold;")

    def _on_connection_changed(self, connected: bool):
        """
        Bağlantı durumu değiştiğinde çağrılır
        
        Args:
            connected: Bağlantı durumu
        """
        status = "Bağlı ✓" if connected else "Bağlantı Yok ✗"
        color = "#48bb78" if connected else "#ff4444"
        
        self.setWindowTitle(f"{APP_TITLE} - {status}")
        
        value_label = self.connection_status.findChild(QLabel, "value")
        if value_label:
            value_label.setText(status)
            value_label.setStyleSheet(f"color: {color}; background: transparent; font-weight: bold;")

    def _on_kumes_clicked(self, kumes_id: int):
        """
        Kümes kartına tıklandığında çağrılır
        
        Args:
            kumes_id: Tıklanan kümes ID
        """
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
        
        print(f"✓ Kümes {kumes_id} detayları gösteriliyor")

    def _add_test_alarms(self):
        """Test için örnek alarm ekler (geliştirme amaçlı)"""
        QTimer.singleShot(4000, self._create_test_alarm)

    def _create_test_alarm(self):
        """Test alarmı oluşturur"""
        print("\n🧪 Test alarmı oluşturuluyor...")
        self.alarm_mgr.add_alarm(2, "TEST: Yüksek sıcaklık!")
        self._update_kumes_card_alarm(2, True)

    def closeEvent(self, event):
        """
        Pencere kapatılırken çağrılır
        
        Args:
            event: Close event
        """
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
    """
    app.setStyleSheet(dark_theme)
    
    # Ana pencereyi oluştur ve göster
    window = KumesOtomasyonMainWindow()
    window.show()
    
    print("✓ Uygulama başlatıldı")
    print("📱 Mobil uygulama için WebSocket adresi:", f"ws://{DEFAULT_ESP_IP}:{WS_PORT}")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()