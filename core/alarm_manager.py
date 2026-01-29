from PyQt6.QtCore import QObject, pyqtSignal
from datetime import datetime

class AlarmManager(QObject):
    """
    Bu sınıf sistemdeki aktif alarmları yönetir.
    UI tarafı bu sınıftaki sinyalleri dinleyerek otomatik güncellenir.
    """
    
    # Sinyaller (UI tarafının dinleyebilmesi için)
    alarmAdded = pyqtSignal()
    alarmCleared = pyqtSignal(int)  # ← DEĞİŞTİ: artık kumes_id gönderiyor
    alarmCountChanged = pyqtSignal(int)

    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        # Liste ismini 'active_alarms' olarak sabitledik
        self.active_alarms = []  

    def get_active_alarms(self):
        """Aktif alarmların listesini döndürür"""
        return self.active_alarms.copy()

    def get_alarm_count(self):
        """Aktif alarm sayısını döndürür"""
        return len(self.active_alarms)

    def add_alarm(self, kumes_id, mesaj):
        """Yeni bir alarm oluşturur ve listeye ekler"""
        # Aynı kümes için aynı mesajlı mükerrer alarmı önle
        for alarm in self.active_alarms:
            if alarm.get('kumes_id') == kumes_id and alarm.get('mesaj') == mesaj:
                return False 
        
        alarm_data = {
            "kumes_id": kumes_id,
            "id": kumes_id,
            "mesaj": mesaj,
            "zaman": datetime.now(),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.active_alarms.append(alarm_data)
        
        # Sinyalleri gönder
        self.alarmAdded.emit()
        self.alarmCountChanged.emit(len(self.active_alarms))
        return True

    def remove_alarm_by_index(self, index):
        """Belirli indexteki alarmı siler"""
        if 0 <= index < len(self.active_alarms):
            removed_alarm = self.active_alarms.pop(index)
            kumes_id = removed_alarm.get('kumes_id')
            
            # Signal gönder
            if kumes_id is not None:
                self.alarmCleared.emit(kumes_id)  # ← EKLEME: kumes_id gönder
            
            self.alarmCountChanged.emit(len(self.active_alarms))
            return True
        return False

    def clear_all(self):
        """Tüm aktif alarmları temizler"""
        if not self.active_alarms:
            return 
        
        # Her kümes için signal gönder
        cleared_kumes_ids = set(alarm['kumes_id'] for alarm in self.active_alarms)
        
        self.active_alarms.clear()
        
        # Her temizlenen kümes için signal gönder
        for kumes_id in cleared_kumes_ids:
            self.alarmCleared.emit(kumes_id)  # ← EKLEME
        
        self.alarmCountChanged.emit(0)

    def has_active_alarm(self, kumes_id: int) -> bool:
        """
        Belirli bir kümes için aktif alarm var mı kontrol eder.
        """
        for alarm in self.active_alarms:
            if alarm["kumes_id"] == kumes_id:
                return True
        return False
    
    # ============ YENİ FONKSİYON ============
    def clear_alarm_by_kumes(self, kumes_id: int) -> bool:
        """
        Belirli bir kümesin tüm alarmlarını temizler
        
        Args:
            kumes_id: Kümes ID'si
            
        Returns:
            bool: Alarm temizlendi mi?
        """
        had_alarm = False
        
        # Kümesin alarmlarını bul ve sil
        to_remove = [
            alarm for alarm in self.active_alarms 
            if alarm.get('kumes_id') == kumes_id
        ]
        
        for alarm in to_remove:
            self.active_alarms.remove(alarm)
            had_alarm = True
        
        # Signal gönder
        if had_alarm:
            self.alarmCleared.emit(kumes_id)
            self.alarmCountChanged.emit(len(self.active_alarms))
        
        return had_alarm