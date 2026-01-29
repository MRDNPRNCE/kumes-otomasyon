import sys
import json
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout
from PyQt6.QtCore import QTimer

# Modül içe aktarmaları
from core.config import APP_TITLE, DEFAULT_ESP_IP
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
    def __init__(self, initial_ip: str = DEFAULT_ESP_IP):
        super().__init__()
        
        # ═══════════════════════════════════════════════════════
        # DEBUG ÇIKTISI
        # ═══════════════════════════════════════════════════════
        print("\n" + "🚀 " * 35)
        print("=" * 70)
        print("🚀 ANA UYGULAMA BAŞLATILIYOR")
        print("=" * 70)
        print(f"   Config'den IP  : {DEFAULT_ESP_IP}")
        from core.config import WS_PORT
        print(f"   Config'den Port: {WS_PORT}")
        print(f"   Parametre IP   : {initial_ip}")
        print("=" * 70 + "\n")
        # ═══════════════════════════════════════════════════════
        
        self.setWindowTitle(APP_TITLE)
        self.resize(1200, 800)

        # 1. Arka Plan Bileşenleri
        self.db = DatabaseManager()
        self.ws = WebSocketBridge(initial_ip)
        self.alarm_mgr = AlarmManager(self.db)
        self.updater = RealTimeDataUpdater(self.ws)

        # Widget referansları (init'ten önce tanımla)
        self.kumes_cards = []
        self.system_panel = None
        self.control_panel = None
        self.alarm_view = None
        self.settings_tab = None
        self.tabs = None

        # 2. Arayüzü Başlat
        self._init_ui()
        self._connect_signals()
        
        # 3. Çalıştır
        self.ws.connect()
        self.updater.start()
        
        # 4. Test Alarmları Ekle (geliştirme aşamasında)
        self._add_test_alarms()

    def _init_ui(self):
        """Ana arayüz bileşenlerini oluşturur"""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # --- SEKME 1: GENEL BAKIŞ ---
        overview = QWidget()
        overview_layout = QVBoxLayout(overview)
        
        # 3 adet kümes kartı oluştur
        self.kumes_cards = [KumesCard(i + 1) for i in range(3)]
        for card in self.kumes_cards:
            overview_layout.addWidget(card)

            card.ledToggled.connect(self._handle_led_toggle)
            card.ledToggled.connect(self._handle_fan_toggle)
            card.ledToggled.connect(self._handle_door_toggle)
        
        # Sistem durum paneli
        self.system_panel = SystemStatusPanel()
        overview_layout.addWidget(self.system_panel)
        self.tabs.addTab(overview, "Genel Bakış")

        # --- SEKME 2: KONTROL ---
        self.control_panel = ControlPanel(self.ws)
        self.tabs.addTab(self.control_panel, "Kontrol")

        # --- SEKME 3: ALARMLAR ---
        self.alarm_view = AlarmView(self.alarm_mgr)
        self.tabs.addTab(self.alarm_view, "Alarmlar")

        # --- SEKME 4: AYARLAR ---
        self.settings_tab = SettingsTab(self.ws)
        self.tabs.addTab(self.settings_tab, "Ayarlar")

    def _connect_signals(self):
        """Sinyal-slot bağlantılarını kurar"""
        self.ws.dataReceived.connect(self._handle_data)
        self.ws.connectionChanged.connect(self._update_connection_status)
def _handle_led_toggle(self, kumes_id: int, state: bool):
    """LED butonu değiştiğinde"""
    action = "led_on" if state else "led_off"
    self.ws.send_json({"action": action, "kumes": kumes_id})
    print(f"💡 Kümes {kumes_id} LED: {'AÇIK' if state else 'KAPALI'}")

def _handle_fan_toggle(self, kumes_id: int, state: bool):
    """Fan butonu değiştiğinde"""
    action = "fan_on" if state else "fan_off"
    self.ws.send_json({"action": action, "kumes": kumes_id})
    print(f"🌀 Kümes {kumes_id} FAN: {'AÇIK' if state else 'KAPALI'}")

def _handle_door_toggle(self, kumes_id: int, state: bool):
    """Kapı butonu değiştiğinde"""
    action = "door_open" if state else "door_close"
    self.ws.send_json({"action": action, "kumes": kumes_id})
    print(f"🚪 Kümes {kumes_id} KAPI: {'AÇIK' if state else 'KAPALI'}")
   
    def _handle_data(self, raw_json: str):
        """WebSocket'ten gelen veriyi işler"""
        try:
            data = json.loads(raw_json)
            
            # Kümes kartlarını güncelle
            if 'kumesler' in data:
                for kumes in data['kumesler']:
                    kumes_id = kumes.get('id', 1)
                    idx = kumes_id - 1
                    
                    # Kart güncelle
                    if 0 <= idx < len(self.kumes_cards):
                        self.kumes_cards[idx].update_data(kumes)
                    
                    # Alarm kontrolü (ESP32'den gelen)
                    if kumes.get('alarm', False):
                        mesaj = kumes.get('mesaj', 'Alarm tetiklendi!')
                        if self.alarm_mgr.add_alarm(kumes_id, mesaj):
                            print(f"🚨 YENİ ALARM: Kümes {kumes_id} - {mesaj}")

            # Sistem panelini güncelle
            if self.system_panel:
                self.system_panel.update_data(data)
                
        except json.JSONDecodeError as e:
            print(f"JSON ayrıştırma hatası: {e}")
        except Exception as e:
            print(f"Veri işleme hatası: {e}")

    def _update_connection_status(self, connected: bool):
        """Bağlantı durumunu günceller"""
        status = "Bağlı ✓" if connected else "Bağlantı Yok ✗"
        self.setWindowTitle(f"{APP_TITLE} - {status}")

    def _add_test_alarms(self):
        """Test için örnek alarmlar ekler"""
        QTimer.singleShot(2000, self._create_sample_alarms)
    
    def _create_sample_alarms(self):
        """Örnek alarmları oluşturur"""
        print("🧪 Test alarmları oluşturuluyor...")
        
        # Test alarmları ekle
        self.alarm_mgr.add_alarm(1, "Yüksek sıcaklık tespit edildi! (35°C)")
        self.alarm_mgr.add_alarm(2, "Düşük su seviyesi! (150 ml)")
        self.alarm_mgr.add_alarm(3, "Yüksek amonyak seviyesi! (40 ppm)")
        
        print(f"✓ {self.alarm_mgr.get_alarm_count()} test alarmı eklendi")
        print("📋 'Alarmlar' sekmesini kontrol edin!")

    def closeEvent(self, event):
        """Uygulama kapatılırken temizlik yapar"""
        try:
            if hasattr(self, 'updater') and self.updater:
                self.updater.stop()
            if hasattr(self, 'ws') and self.ws:
                self.ws.disconnect()
            if hasattr(self, 'db') and self.db:
                self.db.close()
        except Exception as e:
            print(f"Kapatma hatası: {e}")
        finally:
            event.accept()


def main():
    """Ana uygulama başlatıcı"""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = KumesOtomasyonMainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
    # .\venv\Scripts\Activate.ps1