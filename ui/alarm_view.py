from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
    QTableWidgetItem, QPushButton, QLabel, QHeaderView, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from core.alarm_manager import AlarmManager


class AlarmView(QWidget):
    """Aktif alarmları gösteren tablo ve yönetim paneli"""

    def __init__(self, alarm_manager: AlarmManager, parent=None):
        super().__init__(parent)
        self.alarm_mgr = alarm_manager
        self._init_ui()
        self._connect_signals()
        
        # Başlangıçta mevcut alarmları yükle
        self.update_table()

    def _init_ui(self):
        """Arayüz bileşenlerini oluşturur"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Üst bilgi paneli
        self._create_info_panel(layout)
        
        # Alarm tablosu
        self._create_table(layout)
        
        # Kontrol butonları
        self._create_buttons(layout)

    def _create_info_panel(self, parent_layout):
        """Üst bilgi panelini oluşturur"""
        info_layout = QHBoxLayout()
        
        self.count_label = QLabel("Aktif Alarm: 0")
        self.count_label.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #2e7d32; padding: 8px;"
        )
        info_layout.addWidget(self.count_label)
        info_layout.addStretch()
        
        parent_layout.addLayout(info_layout)

    def _create_table(self, parent_layout):
        """Alarm tablosunu oluşturur"""
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Kümes No", "Durum/Mesaj", "Kayıt Zamanı"])
        
        # Sütun genişlikleri
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        
        # Tablo özellikleri
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        
        # Stil
        self.table.setStyleSheet("""
            QTableWidget { 
                gridline-color: #e2e8f0; 
                border: 1px solid #cbd5e0;
                background-color: white;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: black;
            }
        """)
        
        parent_layout.addWidget(self.table)

    def _create_buttons(self, parent_layout):
        """Kontrol butonlarını oluşturur"""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # Seçili alarmı sil butonu
        remove_btn = QPushButton("Seçili Alarmı Sil")
        remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        remove_btn.setStyleSheet("""
            QPushButton { 
                background-color: #ff9800; 
                color: white; 
                padding: 12px; 
                font-weight: bold; 
                border-radius: 5px; 
            }
            QPushButton:hover { 
                background-color: #f57c00; 
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        remove_btn.clicked.connect(self._remove_selected)
        button_layout.addWidget(remove_btn)
        
        # Tümünü temizle butonu
        clear_btn = QPushButton("Tüm Alarmları Temizle")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.setStyleSheet("""
            QPushButton { 
                background-color: #f44336; 
                color: white; 
                padding: 12px; 
                font-weight: bold; 
                border-radius: 5px; 
            }
            QPushButton:hover { 
                background-color: #d32f2f; 
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        clear_btn.clicked.connect(self._clear_all)
        button_layout.addWidget(clear_btn)
        
        parent_layout.addLayout(button_layout)

    def _connect_signals(self):
        """AlarmManager sinyallerini bağlar"""
        # Sinyal varlığını kontrol et ve bağla
        if hasattr(self.alarm_mgr, 'alarmAdded'):
            self.alarm_mgr.alarmAdded.connect(self.update_table)
        
        if hasattr(self.alarm_mgr, 'alarmCleared'):
            self.alarm_mgr.alarmCleared.connect(self.update_table)
        
        if hasattr(self.alarm_mgr, 'alarmRemoved'):
            self.alarm_mgr.alarmRemoved.connect(self.update_table)
        
        if hasattr(self.alarm_mgr, 'alarmCountChanged'):
            self.alarm_mgr.alarmCountChanged.connect(self._update_count)

    def update_table(self):
        """
        Alarm tablosunu günceller
        NOT: Bu metod public olmalı (main.py'den çağrılıyor)
        """
        try:
            alarms = self.alarm_mgr.get_active_alarms()
            
            self.table.setRowCount(len(alarms))
            
            for row, alarm in enumerate(alarms):
                # Kümes sütunu (ID)
                kumes_id = alarm.get('kumes_id') or alarm.get('id', '?')
                kumes_item = QTableWidgetItem(f"Kümes {kumes_id}")
                kumes_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 0, kumes_item)
                
                # Mesaj sütunu
                mesaj = alarm.get('mesaj', 'Bilinmeyen hata')
                msg_item = QTableWidgetItem(mesaj)
                msg_item.setForeground(QColor("#d32f2f"))  # Kırmızı
                msg_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, 1, msg_item)
                
                # Zaman sütunu
                zaman = alarm.get('zaman') or alarm.get('timestamp', '')
                if hasattr(zaman, 'strftime'):
                    zaman_str = zaman.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    zaman_str = str(zaman)
                
                time_item = QTableWidgetItem(zaman_str)
                time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 2, time_item)
            
            # Sayacı güncelle
            self._update_count(len(alarms))
            
        except Exception as e:
            print(f"Tablo güncelleme hatası: {e}")

    def _update_count(self, count: int):
        """Alarm sayısı etiketini günceller"""
        self.count_label.setText(f"Aktif Alarm: {count}")
        
        # Renk değiştir (alarm varsa kırmızı, yoksa yeşil)
        color = '#d32f2f' if count > 0 else '#2e7d32'
        self.count_label.setStyleSheet(
            f"font-size: 16px; font-weight: bold; color: {color}; padding: 8px;"
        )

    def _remove_selected(self):
        """Seçili satırdaki alarmı siler"""
        current_row = self.table.currentRow()
        
        if current_row < 0:
            QMessageBox.warning(
                self, 
                "Uyarı", 
                "Lütfen silmek istediğiniz alarmı seçin."
            )
            return
        
        # Onay iste
        reply = QMessageBox.question(
            self,
            "Alarm Silme",
            "Seçili alarmı silmek istediğinizden emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.alarm_mgr.remove_alarm_by_index(current_row):
                self.update_table()

    def _clear_all(self):
        """Tüm alarmları temizler"""
        if self.alarm_mgr.get_alarm_count() == 0:
            QMessageBox.information(
                self, 
                "Bilgi", 
                "Temizlenecek alarm bulunmuyor."
            )
            return
        
        # Onay iste
        reply = QMessageBox.question(
            self,
            "Tüm Alarmları Temizle",
            f"Toplam {self.alarm_mgr.get_alarm_count()} alarm silinecek. Emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.alarm_mgr.clear_all()
            self.update_table()