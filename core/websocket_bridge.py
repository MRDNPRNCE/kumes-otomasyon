from PyQt6.QtCore import QObject, pyqtSignal, QTimer
import websocket
import threading
import time
import json
from typing import Optional
from .config import DEFAULT_ESP_IP, WS_PORT


class WebSocketBridge(QObject):
    """ESP32 ile gerçek zamanlı haberleşme köprüsü"""

    # Sinyaller
    dataReceived = pyqtSignal(str)          # Ham JSON string
    connectionChanged = pyqtSignal(bool)    # Bağlantı durumu
    errorOccurred = pyqtSignal(str)         # Hata mesajı
    messageToUI = pyqtSignal(str)           # UI'a bilgi mesajı

    def __init__(self, ip: str = DEFAULT_ESP_IP, port: int = WS_PORT):
        super().__init__()
        self.ip = ip
        self.port = port
        self.ws: Optional[websocket.WebSocketApp] = None
        self.connected = False
        self._running = False
        self._reconnect_timer: Optional[QTimer] = None
        self._connection_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()  # Thread-safe işlemler için

    def connect(self):
        """Güncel IP ve Port üzerinden bağlantı kurar"""
        with self._lock:
            if self.connected:
                print("Zaten bağlı, yeni bağlantı açılmıyor.")
                return

            self._running = True
            url = f"ws://{self.ip}:{self.port}"
            
            # DEBUG ÇIKTISI
            print("\n" + "=" * 70)
            print("🔌 WEBSOCKET BAĞLANTI GİRİŞİMİ")
            print("=" * 70)
            print(f"   IP Adresi    : {self.ip}")
            print(f"   Port         : {self.port}")
            print(f"   WebSocket URL: {url}")
            print(f"   Running      : {self._running}")
            print(f"   Connected    : {self.connected}")
            print("=" * 70 + "\n")
            
            try:
                self.ws = websocket.WebSocketApp(
                    url,
                    on_open=self._on_open,
                    on_message=self._on_message,
                    on_error=self._on_error,
                    on_close=self._on_close
                )

                # Bağlantı thread'ini başlat
                self._connection_thread = threading.Thread(
                    target=self._run_websocket,
                    daemon=True
                )
                self._connection_thread.start()
                
            except Exception as e:
                self.errorOccurred.emit(f"Bağlantı başlatma hatası: {str(e)}")
                print(f"WebSocket başlatma hatası: {e}")

    def _run_websocket(self):
        """WebSocket'i ayrı thread'de çalıştırır"""
        try:
            # ping_interval ve ping_timeout ile bağlantı sağlığını kontrol et
            self.ws.run_forever(
                ping_interval=5,
                ping_timeout=3,
                skip_utf8_validation=True  # Performans için
            )
        except Exception as e:
            print(f"WebSocket run_forever hatası: {e}")
            self.errorOccurred.emit(f"Bağlantı hatası: {str(e)}")

    def _on_open(self, ws):
        """Bağlantı başarıyla açıldığında"""
        with self._lock:
            self.connected = True
        
        self.connectionChanged.emit(True)
        self.messageToUI.emit(f"ESP32'ye bağlandı ({self.ip}:{self.port})")
        print(f"✓ WebSocket bağlantısı açıldı: {self.ip}:{self.port}")

    def _on_message(self, ws, message):
        """Mesaj alındığında"""
        try:
            # Bytes'ı string'e çevir
            if isinstance(message, bytes):
                message = message.decode('utf-8')

            # JSON olarak parse et ve doğrula
            data = json.loads(message)

            # Session manager'a yönlendir
            if hasattr(self, 'session_manager') and self.session_manager:
                self.session_manager.handle_message(data)

            self.dataReceived.emit(message)
        except json.JSONDecodeError as e:
            print(f"Geçersiz JSON alındı: {message[:100]}... Hata: {e}")
            self.errorOccurred.emit(f"Geçersiz veri formatı alındı")
        except Exception as e:
            print(f"Mesaj işleme hatası: {e}")

    def _on_error(self, ws, error):
        """Hata oluştuğunda"""
        error_msg = str(error)
        self.errorOccurred.emit(error_msg)
        print(f"❌ WebSocket Hatası: {error_msg}")

    def _on_close(self, ws, close_status_code, close_msg):
        """Bağlantı kapandığında"""
        with self._lock:
            was_connected = self.connected
            self.connected = False
        
        if was_connected:
            self.connectionChanged.emit(False)
        
        reason = close_msg or "Bilinmeyen sebep"
        print(f"⚠ Bağlantı kapandı: {reason} (Kod: {close_status_code})")
        
        # Otomatik yeniden bağlanma
        if self._running:
            print("4 saniye sonra yeniden bağlanılacak...")
            self._schedule_reconnect(4.0)

    def _schedule_reconnect(self, delay_seconds: float):
        """Belirli bir süre sonra yeniden bağlanmayı planlar"""
        # Threading.Timer yerine QTimer kullan (Qt thread-safe)
        if self._reconnect_timer:
            self._reconnect_timer.stop()
        
        self._reconnect_timer = QTimer()
        self._reconnect_timer.setSingleShot(True)
        self._reconnect_timer.timeout.connect(self._attempt_reconnect)
        self._reconnect_timer.start(int(delay_seconds * 1000))

    def _attempt_reconnect(self):
        """Yeniden bağlanma girişimi"""
        if self._running and not self.connected:
            print("Yeniden bağlanma deneniyor...")
            self.connect()

    def send_command(self, command: str) -> bool:
        """
        ESP32'ye komut gönderir
        
        Args:
            command: Gönderilecek komut (JSON string veya eski format)
            
        Returns:
            bool: Başarılı ise True
        """
        with self._lock:
            if not self.connected or not self.ws:
                print("Bağlantı yok! Komut gönderilemedi.")
                return False

        try:
            # Önce JSON olup olmadığını kontrol et
            try:
                json.loads(command)  # Validate JSON
                is_json = True
            except json.JSONDecodeError:
                is_json = False
            
            # JSON ise direkt gönder
            if is_json:
                self.ws.send(command)
                print(f"→ JSON Komut gönderildi: {command[:100]}...")
                return True
            
            # Eski format ise JSON'a çevir
            else:
                print(f"⚠️ ESKİ FORMAT ALGILANDI: {command}")
                converted = self._convert_old_command(command)
                if converted:
                    json_str = json.dumps(converted)
                    self.ws.send(json_str)
                    print(f"→ Dönüştürüldü ve gönderildi: {json_str}")
                    return True
                else:
                    print(f"❌ Bilinmeyen komut formatı: {command}")
                    return False
            
        except Exception as e:
            self.errorOccurred.emit(f"Komut gönderilemedi: {str(e)}")
            print(f"❌ Komut gönderme hatası: {e}")
            return False
    
    def _convert_old_command(self, command: str) -> dict:
        """
        Eski format komutları yeni JSON formatına çevirir
        
        Eski → Yeni:
        FAN1:1 → {"action": "fan_on", "kumes": 1}
        FAN1:0 → {"action": "fan_off", "kumes": 1}
        LED:1 → {"action": "led_on"}
        LED:0 → {"action": "led_off"}
        STATUS → {"action": "get_status"}
        """
        command = command.strip().upper()
        
        # STATUS komutu
        if command == "STATUS":
            return {"action": "get_status"}
       
        if command.startswith("AUTO:"):
            state = command.endswith("1")
            return {
                "action": "set_auto_mode",
                "value": state
            }
        # FAN komutları (FAN1:1, FAN2:0, vb.)
        if command.startswith("FAN"):
            parts = command.split(":")
            if len(parts) == 2:
                fan_num = int(parts[0][3:])  # FAN1 -> 1
                state = parts[1] == "1"
                return {
                    "action": "fan_on" if state else "fan_off",
                    "kumes": fan_num
                }
        if command.startswith("YEM:"):
            parts = command.split(":")
            if len(parts) == 2:
                try:
                    miktar = int(parts[1])
                    return {
                        "action": "yem_ver",
                        "miktar": miktar
                    }
                except ValueError:
                    return None
        if command.startswith("KAPI:"):
            parts = command.split(":")
            if len(parts) == 2:
                try:
                    derece = int(parts[1])
                    return {
                        "action": "kapi_kontrol",
                        "derece": derece
                    }
                except ValueError:
                    return None
                
        # LED komutları (LED:1, LED:0)
        if command.startswith("LED:"):
            state = command.endswith("1")
            return {"action": "led_on" if state else "led_off"}
        
        # POMPA komutları
        if command.startswith("POMPA:"):
            state = command.endswith("1")
            return {"action": "pump_on" if state else "pump_off"}
        
        return None  # Bilinmeyen komut

    def send_json(self, data: dict) -> bool:
        """
        Dictionary'yi JSON'a çevirip gönderir
        
        Args:
            data: Gönderilecek dictionary
            
        Returns:
            bool: Başarılı ise True
        """
        try:
            json_str = json.dumps(data)
            return self.send_command(json_str)
        except Exception as e:
            self.errorOccurred.emit(f"JSON dönüştürme hatası: {str(e)}")
            return False

    def disconnect(self):
        """Bağlantıyı tamamen durdurur"""
        print("Bağlantı kapatılıyor...")
        
        with self._lock:
            self._running = False
        
        # Yeniden bağlanma timer'ını durdur
        if self._reconnect_timer:
            self._reconnect_timer.stop()
            self._reconnect_timer = None
        
        # WebSocket'i kapat
        if self.ws:
            try:
                self.ws.close()
            except Exception as e:
                print(f"WebSocket kapatma hatası: {e}")
        
        # Thread'in bitmesini bekle
        if self._connection_thread and self._connection_thread.is_alive():
            self._connection_thread.join(timeout=2.0)
        
        with self._lock:
            self.connected = False
        
        print("✓ Bağlantı kapatıldı")

    def update_ip(self, new_ip: str, new_port: Optional[int] = None):
        """
        IP (ve opsiyonel port) değiştiğinde bağlantıyı yeniden başlatır
        
        Args:
            new_ip: Yeni IP adresi
            new_port: Yeni port (opsiyonel)
        """
        print(f"IP Güncelleniyor: {new_ip}" + (f":{new_port}" if new_port else ""))
        
        # Önce mevcut bağlantıyı kapat
        self.disconnect()
        
        # Kısa bekleme (Socket'in temiz kapanması için)
        time.sleep(0.5)
        
        # Yeni ayarları uygula
        self.ip = new_ip
        if new_port is not None:
            self.port = new_port
        
        # Yeniden bağlan
        with self._lock:
            self._running = True
        
        self.connect()

    def is_connected(self) -> bool:
        """Bağlantı durumunu döndürür"""
        with self._lock:
            return self.connected

    def get_connection_info(self) -> dict:
        """Bağlantı bilgilerini döndürür"""
        with self._lock:
            return {
                "ip": self.ip,
                "port": self.port,
                "connected": self.connected,
                "running": self._running
            }