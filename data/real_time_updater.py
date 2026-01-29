# data/real_time_updater.py
from PyQt6.QtCore import QObject, QTimer
from core.websocket_bridge import WebSocketBridge


class RealTimeDataUpdater(QObject):
    """Periyodik olarak ESP32'den durum verisi ister ve bağlantıyı kontrol eder"""

    def __init__(self, ws_bridge: WebSocketBridge, interval_ms: int = 5000):
        super().__init__()
        self.ws = ws_bridge
        self.interval = interval_ms
        self.timer = QTimer()
        self.timer.timeout.connect(self._update)
        self._update_count = 0

    def start(self):
        """Güncellemeyi başlat"""
        print(f"📡 RealTimeDataUpdater başlatıldı (Her {self.interval/1000} saniyede)")
        self.timer.start(self.interval)

    def stop(self):
        """Güncellemeyi durdur"""
        print("⏹️ RealTimeDataUpdater durduruldu")
        self.timer.stop()

    def _update(self):
        """
        Timer tetiklendiğinde çalışır
        
        NOT: ESP32 simülatörü zaten otomatik veri gönderiyor (her 2 saniyede)
        Bu yüzden ekstra durum sorgulama gerekmeyebilir.
        """
        if self.ws.is_connected():
            # JSON formatında durum sorgula
            # self.ws.send_json({"action": "get_status"})
            # print(f"📊 Durum güncellemesi istendi ({self._update_count})")
            
            # ESP32 simülatörü zaten otomatik veri gönderiyor
            # Bu satırı yorum satırı yapabilirsiniz
            self._update_count += 1
            
            # Her 10 güncellemede bir log (spam önleme)
            if self._update_count % 10 == 0:
                print(f"✓ Bağlantı aktif ({self._update_count} güncelleme)")
        else:
            print("⚠️ Bağlantı yok - güncelleme atlandı")

    def set_interval(self, interval_ms: int):
        """Güncelleme aralığını değiştir"""
        was_active = self.timer.isActive()
        self.timer.stop()
        self.interval = interval_ms
        if was_active:
            self.timer.start(self.interval)
            print(f"⏱️ Güncelleme aralığı değiştirildi: {interval_ms/1000} saniye")