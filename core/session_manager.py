# session_manager.py - Advanced Session Management for PyQt6

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QMessageBox
import json
import random
import string

class SessionManager(QObject):
    # Signals
    auth_success = pyqtSignal(dict)
    auth_failed = pyqtSignal(str)
    admin_override = pyqtSignal(dict)
    control_available = pyqtSignal(dict)
    control_revoked = pyqtSignal(dict)
    admin_left = pyqtSignal(dict)
    mode_changed = pyqtSignal(dict)
    permission_denied = pyqtSignal(dict)
    ui_update_required = pyqtSignal()
    
    def __init__(self, websocket_client=None):
        super().__init__()
        
        self.session_id = None
        self.username = None
        self.role = None
        self.admin_mode = None  # "active" veya "watching" (sadece admin için)
        self.can_control = False
        self.permissions = {}
        self.client_type = 'desktop'
        self.ws_client = websocket_client
    
    def set_websocket_client(self, ws_client):
        """WebSocket client'ı ayarla"""
        self.ws_client = ws_client
    
    # ==================== LOGIN ====================
    def login(self, username, password):
        """Login mesajı gönder"""
        if not self.ws_client or not self.ws_client.connected:
            QMessageBox.warning(None, "Bağlantı Hatası", "WebSocket bağlı değil!")
            return
        
        msg = {
            'type': 'auth',
            'username': username,
            'password': password,
            'client_type': self.client_type
        }
        
        self.ws_client.send_message(msg)
        print(f"🔑 Login mesajı gönderildi: {username}")
    
    # ==================== MESSAGE HANDLING ====================
    def handle_message(self, data):
        """WebSocket'ten gelen mesajları işle"""
        msg_type = data.get('type')
        
        if msg_type == 'auth_success':
            self._on_auth_success(data)
        elif msg_type == 'auth_failed':
            self._on_auth_failed(data)
        elif msg_type == 'admin_override':
            self._on_admin_override(data)
        elif msg_type == 'control_available':
            self._on_control_available(data)
        elif msg_type == 'control_revoked':
            self._on_control_revoked(data)
        elif msg_type == 'admin_left':
            self._on_admin_left(data)
        elif msg_type == 'mode_changed':
            self._on_mode_changed(data)
        elif msg_type == 'permission_denied':
            self._on_permission_denied(data)
        elif msg_type == 'user_joined':
            print(f"👤 Kullanıcı katıldı: {data.get('username')}")
    
    # ==================== AUTH SUCCESS ====================
    def _on_auth_success(self, data):
        """Giriş başarılı"""
        self.session_id = data.get('session_id')
        self.username = data.get('username')
        self.role = data.get('role')
        self.permissions = data.get('permissions', {})
        self.can_control = self.permissions.get('can_control', False)
        
        if self.role == 'admin':
            self.admin_mode = data.get('admin_mode', 'active')
        
        print(f"✅ Giriş başarılı: {self.username} ({self.role})")
        print(f"   Admin Mod: {self.admin_mode}")
        print(f"   Kontrol: {self.can_control}")
        
        # Signal emit et
        self.auth_success.emit(data)
        self.ui_update_required.emit()
        
        # Bildirim göster
        if self.role == 'admin':
            mode_text = 'Aktif Mod' if self.admin_mode == 'active' else 'İzleme Modu'
            QMessageBox.information(None, "Giriş Başarılı", 
                f"Admin olarak giriş yapıldı ({mode_text})")
        else:
            control_text = 'Kontrol edebilirsiniz' if self.can_control else 'Sadece izleme'
            QMessageBox.information(None, "Giriş Başarılı", 
                f"Giriş başarılı ({control_text})")
    
    def _on_auth_failed(self, data):
        """Giriş başarısız"""
        message = data.get('message', 'Giriş başarısız')
        print(f"❌ Giriş başarısız: {message}")
        
        self.auth_failed.emit(message)
        QMessageBox.warning(None, "Giriş Hatası", message)
    
    # ==================== ADMIN OVERRIDE ====================
    def _on_admin_override(self, data):
        """Admin yetkisi elinden alındı"""
        print(f"⚠️ Admin override: {data}")
        
        # Artık user olarak devam
        self.role = 'user'
        self.admin_mode = None
        self.can_control = False
        
        # Signal emit et
        self.admin_override.emit(data)
        self.ui_update_required.emit()
        
        # Uyarı göster
        QMessageBox.warning(None, "Yetki Değişikliği", 
            f"{data.get('message')}\n\nArtık sadece izleme modundasınız.")
    
    # ==================== CONTROL AVAILABLE ====================
    def _on_control_available(self, data):
        """Kontrol yetkisi verildi"""
        print(f"✅ Kontrol yetkisi verildi: {data}")
        
        self.can_control = True
        
        # Signal emit et
        self.control_available.emit(data)
        self.ui_update_required.emit()
        
        # Bildirim göster
        QMessageBox.information(None, "Kontrol Yetkisi", data.get('message'))
    
    # ==================== CONTROL REVOKED ====================
    def _on_control_revoked(self, data):
        """Kontrol yetkisi kaldırıldı"""
        print(f"⚠️ Kontrol yetkisi kaldırıldı: {data}")
        
        self.can_control = False
        
        # Signal emit et
        self.control_revoked.emit(data)
        self.ui_update_required.emit()
        
        # Uyarı göster
        QMessageBox.warning(None, "Kontrol Kaldırıldı", data.get('message'))
    
    # ==================== ADMIN LEFT ====================
    def _on_admin_left(self, data):
        """Admin ayrıldı"""
        print(f"✅ Admin ayrıldı: {data}")
        
        if self.role == 'user':
            self.can_control = True
            
            # Signal emit et
            self.admin_left.emit(data)
            self.ui_update_required.emit()
            
            # Bildirim göster
            QMessageBox.information(None, "Admin Ayrıldı", data.get('message'))
    
    # ==================== MODE CHANGED ====================
    def _on_mode_changed(self, data):
        """Mod değişti (admin)"""
        print(f"✅ Mod değişti: {data}")
        
        self.admin_mode = data.get('mode')
        self.can_control = (self.admin_mode == 'active')
        
        # Signal emit et
        self.mode_changed.emit(data)
        self.ui_update_required.emit()
        
        # Bildirim göster
        if self.admin_mode == 'active':
            QMessageBox.information(None, "Mod Değişti", 
                "👑 Aktif moda geçtiniz. Tam kontrol!")
        else:
            QMessageBox.information(None, "Mod Değişti", 
                "👁️ İzleme moduna geçtiniz. Kullanıcılar kontrol edebilir.")
    
    # ==================== PERMISSION DENIED ====================
    def _on_permission_denied(self, data):
        """Yetki reddedildi"""
        print(f"❌ Yetki reddedildi: {data}")
        
        message = data.get('message', 'Yetki reddedildi')
        
        if data.get('admin_username'):
            message += f"\n\nAktif Admin: {data.get('admin_username')} ({data.get('admin_mode')})"
        
        # Signal emit et
        self.permission_denied.emit(data)
        
        # Hata göster
        QMessageBox.critical(None, "Yetki Hatası", message)
    
    # ==================== MOD DEĞİŞTİRME ====================
    def switch_mode(self, new_mode):
        """Mod değiştir (sadece admin)"""
        if self.role != 'admin':
            QMessageBox.warning(None, "Yetki Hatası", 
                "Sadece admin mod değiştirebilir!")
            return
        
        if not self.ws_client or not self.ws_client.connected:
            QMessageBox.warning(None, "Bağlantı Hatası", "WebSocket bağlı değil!")
            return
        
        msg = {
            'type': 'change_mode',
            'session_id': self.session_id,
            'mode': new_mode  # "active" veya "watching"
        }
        
        self.ws_client.send_message(msg)
        print(f"🔄 Mod değiştirme isteği: {new_mode}")
    
    # ==================== KOMUT GÖNDERME ====================
    def send_command(self, command):
        """Komut gönder"""
        if not self.can_control:
            QMessageBox.warning(None, "Yetki Hatası", 
                "Bu işlem için kontrol yetkisi gerekli!")
            return
        
        if not self.ws_client or not self.ws_client.connected:
            QMessageBox.warning(None, "Bağlantı Hatası", "WebSocket bağlı değil!")
            return
        
        msg = {
            'type': 'command',
            'command': command,
            'session_id': self.session_id
        }
        
        self.ws_client.send_message(msg)
        print(f"📤 Komut gönderildi: {command}")
    
    # ==================== UI HELPER ====================
    def get_user_info_text(self):
        """Header için kullanıcı bilgisi"""
        if not self.username:
            return "Giriş Yapın"
        
        icon = '👑' if self.role == 'admin' else '👤'
        if self.role == 'admin' and self.admin_mode == 'watching':
            icon = '👁️'
        
        return f"{icon} {self.username}"
    
    def get_badge_text(self):
        """Badge metni"""
        if not self.role:
            return ""
        
        if self.role == 'admin':
            if self.admin_mode == 'active':
                return 'Admin Aktif'
            else:
                return 'İzleme Modu'
        else:
            if self.can_control:
                return 'Kontrol'
            else:
                return 'Sadece İzleme'
    
    def get_mode_button_text(self):
        """Mod butonu metni (sadece admin)"""
        if self.role != 'admin':
            return None
        
        if self.admin_mode == 'active':
            return '👁️ İzleme Modu'
        else:
            return '👑 Kontrolü Al'
    
    def get_info_banner_text(self):
        """Bilgi banner metni"""
        if self.role == 'admin':
            if self.admin_mode == 'active':
                return '✅ Tam kontrol modundasınız'
            else:
                return 'ℹ️ İzleme modundasınız. Kullanıcılar sistemi kontrol edebilir.'
        else:
            if self.can_control:
                return '✅ Kontrol edebilirsiniz!'
            else:
                return 'ℹ️ Admin aktif modda. Sadece izleyebilirsiniz.'
    
    # ==================== LOGOUT ====================
    def logout(self):
        """Çıkış yap"""
        # Session temizle
        self.session_id = None
        self.username = None
        self.role = None
        self.admin_mode = None
        self.can_control = False
        self.permissions = {}
        
        # WebSocket kapat
        if self.ws_client:
            self.ws_client.disconnect()
        
        print("👋 Çıkış yapıldı")