import sys
import json
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QStackedWidget, QFrame, QLabel, QGridLayout, QInputDialog, QMessageBox
)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont

from core.config import APP_TITLE, DEFAULT_ESP_IP, WS_PORT
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
        
        # Orijinal terminal çıktıların
        print("\n" + "=" * 70)
        print("KUMES OTOMASYON SISTEMI - FULL DINAMIK & RENKLI ALARM")
        print("=" * 70)
        print(f"   IP  : {DEFAULT_ESP_IP}")
        print(f"   Port: {WS_PORT}")
        print("=" * 70 + "\n")
        
        self.setWindowTitle(APP_TITLE)
        self.resize(1600, 900)
        
        self.db = DatabaseManager()
        self.ws = WebSocketBridge(initial_ip)
        self.alarm_mgr = AlarmManager(self.db)
        self.updater = RealTimeDataUpdater(self.ws)
        
        self.kumes_widgets = {}
        self.kumes_data = {}
        self.selected_kumes_id = 1 # Takip için
        
        # İSTEDİĞİN DİNAMİK YAPILANDIRMA
        self.kumes_configs = {
            1: {"isim": "ANA KÜMES", "tavuk_sayisi": 500, "gun": 12},
            2: {"isim": "YAVRU KÜMESİ", "tavuk_sayisi": 300, "gun": 4},
            3: {"isim": "KARANTİNA", "tavuk_sayisi": 50, "gun": 20}
        }
        
        self._init_ui()
        self._connect_signals()
        
        self.ws.connect()
        self.updater.start()
        self._add_test_alarms() # Orijinal test alarmların burada
    
    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(20)
        
        # SOL PANEL
        left_panel = QVBoxLayout()
        
        # Kümes Kareleri Gridi
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(15)
        
        self._render_kumes_cards() # Kartları çizen fonksiyon
        
        left_panel.addWidget(self.grid_container)

        # YENİ: Bilgi Düzenleme Butonu (İsimleri buradan değiştireceksin)
        self.edit_info_btn = QLabel("⚙️ Kümes İsim ve Bilgilerini Düzenle")
        self.edit_info_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.edit_info_btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.edit_info_btn.setStyleSheet("""
            QLabel { color: #58a6ff; background-color: #21262d; border: 1px solid #30363d; 
                     border-radius: 8px; padding: 10px; font-weight: bold; }
            QLabel:hover { background-color: #30363d; border-color: #58a6ff; }
        """)
        self.edit_info_btn.mousePressEvent = self._open_edit_dialog
        left_panel.addWidget(self.edit_info_btn)
        
        left_panel.addStretch()
        
        # İSTEDİĞİN GELİŞMİŞ STATUS PANELİ
        self.system_panel = self._create_enhanced_status_panel()
        left_panel.addWidget(self.system_panel)
        
        main_layout.addLayout(left_panel, stretch=1)
        
        # SAĞ PANEL - Sekmeler
        self.tabs = QTabWidget()
        
        self.detail_tab = QStackedWidget()
        welcome = QLabel("Sol taraftan bir kümes seçin")
        welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome.setStyleSheet("font-size: 16px; color: #8b949e;")
        self.detail_tab.addWidget(welcome)
        self.tabs.addTab(self.detail_tab, "Kümes Detay")
        
        self.control_panel = ControlPanel(self.ws)
        self.tabs.addTab(self.control_panel, "Kontrol")
        
        self.alarm_view = AlarmView(self.alarm_mgr)
        self.tabs.addTab(self.alarm_view, "Alarmlar")
        
        self.settings_tab = SettingsTab(self.ws)
        self.tabs.addTab(self.settings_tab, "Ayarlar")
        
        main_layout.addWidget(self.tabs, stretch=3)

    def _render_kumes_cards(self):
        """Kartları mevcut konfigürasyona göre sıfırdan çizer (İsim değişikliği için)"""
        for i in reversed(range(self.grid_layout.count())): 
            w = self.grid_layout.itemAt(i).widget()
            if w: w.setParent(None)

        for i in range(1, 4):
            card = self._create_kumes_card(i)
            self.grid_layout.addWidget(card, (i-1)//2, (i-1)%2)
            self.kumes_widgets[i] = {
                'frame': card, 'icon': card.findChild(QLabel, 'icon'),
                'name': card.findChild(QLabel, 'name'), 'temp': card.findChild(QLabel, 'temp'),
                'status': card.findChild(QLabel, 'status')
            }

    def _create_kumes_card(self, kumes_id):
        config = self.kumes_configs.get(kumes_id, {"isim": f"KÜMES {kumes_id}"})
        card = QFrame()
        card.setFixedSize(180, 200)
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.setObjectName(f"kumes_{kumes_id}")
        card.setStyleSheet("""
            QFrame { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #21262d, stop:1 #161b22);
                     border: 3px solid #30363d; border-radius: 15px; }
            QFrame:hover { border-color: #58a6ff; }
        """)
        
        layout = QVBoxLayout(card)
        icon = QLabel("🏠"); icon.setObjectName("icon"); icon.setFont(QFont("Segoe UI", 40)); icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon)
        
        name = QLabel(config["isim"]); name.setObjectName("name"); name.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold)); name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name)
        
        temp = QLabel("-- °C"); temp.setObjectName("temp"); temp.setFont(QFont("Segoe UI", 11)); temp.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(temp)
        
        status = QLabel("●"); status.setObjectName("status"); status.setFont(QFont("Segoe UI", 14)); status.setAlignment(Qt.AlignmentFlag.AlignCenter); status.setStyleSheet("color: #58a6ff;")
        layout.addWidget(status)
        
        card.mousePressEvent = lambda e, kid=kumes_id: self._on_kumes_clicked(kid)
        return card

    def _create_enhanced_status_panel(self):
        panel = QFrame()
        panel.setFixedWidth(390)
        panel.setStyleSheet("QFrame { background-color: #161b22; border: 2px solid #30363d; border-radius: 12px; padding: 15px; }")
        layout = QVBoxLayout(panel)
        
        title = QLabel("📊 SİSTEM VE KÜMES DURUMU")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold)); title.setStyleSheet("color: #58a6ff; border: none;")
        layout.addWidget(title)

        # İSTEDİĞİN STATUS ÖĞELERİ
        self.stat_kumes_adi = self._create_status_item("📍", "Seçili Kümes", "---")
        self.stat_tavuk_sayisi = self._create_status_item("🐔", "Tavuk Sayısı", "0")
        self.stat_kumes_gun = self._create_status_item("📅", "Kaç Günlük", "0")
        self.connection_status = self._create_status_item("🔌", "Bağlantı", "Bekleniyor...")
        self.uptime = self._create_status_item("⏱️", "Çalışma Süresi", "00:00:00")
        self.avg_temp = self._create_status_item("🌡️", "Ort. Sıcaklık", "-- °C")
        self.avg_hum = self._create_status_item("💧", "Ort. Nem", "-- %")
        self.feed_level = self._create_status_item("🌾", "Yem Seviyesi", "-- cm")
        self.water_level = self._create_status_item("🥣", "Su Seviyesi", "-- ml")
        self.outside_temp = self._create_status_item("☁️", "Dış Sıcaklık", "-- °C")
        self.total_alarms = self._create_status_item("🚨", "Aktif Alarm", "0")
        
        items = [self.stat_kumes_adi, self.stat_tavuk_sayisi, self.stat_kumes_gun, self.connection_status, 
                 self.uptime, self.avg_temp, self.avg_hum, self.feed_level, self.water_level, self.outside_temp, self.total_alarms]
        
        for item in items: layout.addWidget(item)
        layout.addStretch()
        return panel
    
    def _create_status_item(self, icon, label, value):
        container = QFrame()
        container.setStyleSheet("QFrame { background-color: #21262d; border-radius: 8px; padding: 10px; border: none; }")
        layout = QHBoxLayout(container)
        l_icon = QLabel(icon); l_icon.setFont(QFont("Segoe UI", 16)); layout.addWidget(l_icon)
        l_label = QLabel(label); l_label.setFont(QFont("Segoe UI", 10)); l_label.setStyleSheet("color: #8b949e;"); layout.addWidget(l_label)
        layout.addStretch()
        l_value = QLabel(value); l_value.setObjectName("value"); l_value.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold)); l_value.setStyleSheet("color: #c9d1d9;"); layout.addWidget(l_value)
        return container

    def _update_kumes_card_alarm(self, kumes_id, has_alarm):
        """ALARM DURUMUNDA HEM KARTIN HEM PANELİN RENGİNİ DEĞİŞTİRİR"""
        if kumes_id not in self.kumes_widgets: return
        card = self.kumes_widgets[kumes_id]['frame']
        status_lbl = self.kumes_widgets[kumes_id]['status']
        icon_lbl = self.kumes_widgets[kumes_id]['icon']
        
        if has_alarm:
            card.setStyleSheet("QFrame { background: #3d1a1a; border: 4px solid #ff4444; border-radius: 15px; }")
            icon_lbl.setText("⚠️"); status_lbl.setText("● ALARM"); status_lbl.setStyleSheet("color: #ff4444; font-weight: bold;")
            if kumes_id == self.selected_kumes_id:
                self.stat_kumes_adi.findChild(QLabel, "value").setStyleSheet("color: #ff4444; font-weight: bold;")
        else:
            card.setStyleSheet("QFrame { background: #161b22; border: 3px solid #30363d; border-radius: 15px; }")
            icon_lbl.setText("🏠"); status_lbl.setText("● Normal"); status_lbl.setStyleSheet("color: #48bb78;")
            if kumes_id == self.selected_kumes_id:
                self.stat_kumes_adi.findChild(QLabel, "value").setStyleSheet("color: #c9d1d9;")

    def _on_kumes_clicked(self, kumes_id):
        self.selected_kumes_id = kumes_id
        config = self.kumes_configs.get(kumes_id, {})
        
        # Status Panel Güncelleme
        name_val = self.stat_kumes_adi.findChild(QLabel, "value")
        name_val.setText(config.get("isim", "---"))
        
        # Seçilen kümes alarmda mı kontrolü (Kırmızılık için)
        is_alarm = self.kumes_data.get(kumes_id, {}).get('alarm', False)
        name_val.setStyleSheet(f"color: {'#ff4444' if is_alarm else '#c9d1d9'}; font-weight: bold;")
        
        self.stat_tavuk_sayisi.findChild(QLabel, "value").setText(str(config.get("tavuk_sayisi", 0)))
        self.stat_kumes_gun.findChild(QLabel, "value").setText(f"{config.get('gun', 0)}. Gün")

        # Sağ Taraf Detay Sekmesi
        while self.detail_tab.count() > 1:
            w = self.detail_tab.widget(1); self.detail_tab.removeWidget(w); w.deleteLater()
        
        detail = KumesCard(kumes_id)
        if kumes_id in self.kumes_data: detail.update_data(self.kumes_data[kumes_id])
        self.detail_tab.addWidget(detail); self.detail_tab.setCurrentWidget(detail)
        self.tabs.setCurrentIndex(0)

    def _handle_data(self, raw_json: str):
        try:
            data = json.loads(raw_json)
            if 'kumesler' in data:
                temps = []; hums = []
                for k in data['kumesler']:
                    kid = k.get('id')
                    self.kumes_data[kid] = k
                    if kid in self.kumes_widgets:
                        t = k.get('sicaklik', 0); temps.append(t)
                        self.kumes_widgets[kid]['temp'].setText(f"{t:.1f} °C")
                        hums.append(k.get('nem', 0))
                        self._update_kumes_card_alarm(kid, k.get('alarm', False))
                
                if temps: self.avg_temp.findChild(QLabel, "value").setText(f"{sum(temps)/len(temps):.1f} °C")
                if hums: self.avg_hum.findChild(QLabel, "value").setText(f"{sum(hums)/len(hums):.1f} %")
            
            if 'yem' in data: self.feed_level.findChild(QLabel, "value").setText(f"{data['yem']} cm")
            if 'su' in data: self.water_level.findChild(QLabel, "value").setText(f"{data['su']} ml")
            if 'dis_sicaklik' in data: self.outside_temp.findChild(QLabel, "value").setText(f"{data['dis_sicaklik']:.1f} °C")
            if 'zaman' in data:
                s = data['zaman']; self.uptime.findChild(QLabel, "value").setText(f"{s//3600:02d}:{(s%3600)//60:02d}:{s%60:02d}")
        except: pass

    def _open_edit_dialog(self, event):
        """Kullanıcıdan isim, adet ve yaş alan bölüm"""
        kumes_id, ok = QInputDialog.getInt(self, "Kümes Seç", "Düzenlenecek Kümes No (1-3):", 1, 1, 3)
        if ok:
            config = self.kumes_configs[kumes_id]
            yeni_isim, ok1 = QInputDialog.getText(self, "Düzenle", f"Kümes {kumes_id} Yeni İsmi:", text=config["isim"])
            if ok1:
                yeni_adet, ok2 = QInputDialog.getInt(self, "Tavuk", "Sayı:", config["tavuk_sayisi"])
                if ok2:
                    yeni_gun, ok3 = QInputDialog.getInt(self, "Yaş", "Gün:", config["gun"])
                    if ok3:
                        self.kumes_configs[kumes_id] = {"isim": yeni_isim, "tavuk_sayisi": yeni_adet, "gun": yeni_gun}
                        self._render_kumes_cards()
                        QMessageBox.information(self, "Başarılı", "Bilgiler güncellendi ve kartlar yenilendi.")

    def _on_connection_changed(self, conn):
        val = self.connection_status.findChild(QLabel, "value")
        val.setText("Bağlı ✓" if conn else "Bağlantı Yok ✗")
        val.setStyleSheet(f"color: {'#48bb78' if conn else '#ff4444'}; font-weight: bold;")

    def _update_alarm_display(self):
        count = self.alarm_mgr.get_alarm_count()
        val = self.total_alarms.findChild(QLabel, "value")
        val.setText(str(count))
        val.setStyleSheet(f"color: {'#ff4444' if count > 0 else '#8b949e'}; font-weight: bold;")

    def _add_test_alarms(self):
        # 4 saniye sonra test alarmı fırlatır (Orijinal fonksiyonun)
        QTimer.singleShot(4000, self._create_test_alarm)
    
    def _create_test_alarm(self):
        print("\n🧪 Test alarmı oluşturuluyor...")
        self.alarm_mgr.add_alarm(2, "TEST: Yüksek sıcaklık!")
        self._update_kumes_card_alarm(2, True)

    def _connect_signals(self):
        self.ws.dataReceived.connect(self._handle_data)
        self.ws.connectionChanged.connect(self._on_connection_changed)
        self.alarm_mgr.alarmAdded.connect(self._update_alarm_display)
        self.alarm_mgr.alarmCleared.connect(self._update_alarm_display)

    def closeEvent(self, event):
        try: self.updater.stop(); self.ws.disconnect(); self.db.close()
        except: pass
        event.accept()

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # SENİN TEMA AYARLARIN
    dark_theme = """
        QMainWindow { background-color: #0d1117; }
        QWidget { background-color: #0d1117; color: #c9d1d9; }
        QTabWidget::pane { border: 2px solid #30363d; background: #161b22; border-radius: 8px; }
        QTabBar::tab { background: #21262d; color: #8b949e; padding: 12px 24px; border: 1px solid #30363d; font-weight: bold; }
        QTabBar::tab:selected { background: #1f6feb; color: white; }
    """
    app.setStyleSheet(dark_theme)
    
    window = KumesOtomasyonMainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()