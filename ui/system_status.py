# ui/system_status.py
from PyQt6.QtWidgets import QGroupBox, QVBoxLayout, QLabel
from PyQt6.QtGui import QFont
from core.config import SUCCESS_COLOR

class SystemStatusPanel(QGroupBox):
    """Sistem genel durumu (yem, pompa, uptime, akımlar vb.)"""

    def __init__(self, parent=None):
        super().__init__("Sistem Durumu", parent)
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #4caf50;
                border-radius: 10px;
                margin-top: 12px;
                padding: 15px;
            }
        """)

        layout = QVBoxLayout()
        self.labels = {}

        fields = [
            ("Çalışma Süresi", "uptime", "--"),
            ("Yem Seviyesi", "yem", "-- cm"),
            ("Pompa", "pompa", "Kapalı"),
            ("Otomatik Mod", "auto_mode", "Aktif"),
            ("Fan Akımı", "akim_fan", "-- A"),
            ("Pompa Akımı", "akim_pompa", "-- A"),
            ("Isıtıcı Akımı", "akim_isitici", "-- A")
        ]

        for text, key, default in fields:
            lbl = QLabel(f"{text}: {default}")
            lbl.setFont(QFont("Segoe UI", 11))
            layout.addWidget(lbl)
            self.labels[key] = lbl

        self.setLayout(layout)

    def update_data(self, data: dict):
        if 'zaman' in data:
            total_sec = data['zaman']
            h = total_sec // 3600
            m = (total_sec % 3600) // 60
            self.labels["uptime"].setText(f"Çalışma Süresi: {h}s {m}d")

        if 'yem' in data:
            self.labels["yem"].setText(f"Yem Seviyesi: {data['yem']} cm")

        if 'pompa' in data:
            self.labels["pompa"].setText(f"Pompa: {'Açık' if data['pompa'] else 'Kapalı'}")

        if 'yemMotor' in data or 'otomatik' in data:
            auto = data.get('otomatik', True)
            self.labels["auto_mode"].setText(f"Otomatik Mod: {'Aktif' if auto else 'Manuel'}")

        # Akım değerleri
        for key in ['akimFan', 'akimPompa', 'akimIsitici']:
            if key in data:
                nice_key = key.lower().replace("akim", "akim_")
                self.labels[nice_key].setText(f"{key.replace('akim','Akım ')}: {data[key]:.2f} A")