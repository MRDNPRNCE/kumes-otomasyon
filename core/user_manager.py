# -*- coding: utf-8 -*-
"""
Kullanıcı Yönetimi Sistemi
- Admin ve User rolleri
- Login/Logout
- Yetki kontrolü
- Şifre hash'leme
"""

import json
import hashlib
import os
from datetime import datetime
from typing import Optional, Dict, List


class User:
    """Kullanıcı sınıfı"""
    
    def __init__(self, username: str, password_hash: str, role: str, full_name: str = ""):
        self.username = username
        self.password_hash = password_hash
        self.role = role  # 'admin' veya 'user'
        self.full_name = full_name or username
        self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.last_login = None
    
    def to_dict(self) -> dict:
        """Kullanıcıyı dict'e çevir"""
        return {
            'username': self.username,
            'password_hash': self.password_hash,
            'role': self.role,
            'full_name': self.full_name,
            'created_at': self.created_at,
            'last_login': self.last_login
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'User':
        """Dict'ten kullanıcı oluştur"""
        user = User(
            username=data['username'],
            password_hash=data['password_hash'],
            role=data['role'],
            full_name=data.get('full_name', data['username'])
        )
        user.created_at = data.get('created_at', user.created_at)
        user.last_login = data.get('last_login')
        return user


class UserManager:
    """Kullanıcı yöneticisi"""
    
    def __init__(self, users_file: str = 'users.json'):
        self.users_file = users_file
        self.users: Dict[str, User] = {}
        self.current_user: Optional[User] = None
        self._load_users()
        self._ensure_default_users()
    
    def _hash_password(self, password: str) -> str:
        """Şifreyi hash'le"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _load_users(self):
        """Kullanıcıları dosyadan yükle"""
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for username, user_data in data.items():
                        self.users[username] = User.from_dict(user_data)
                print(f"✅ {len(self.users)} kullanıcı yüklendi")
            except Exception as e:
                print(f"⚠️ Kullanıcı yükleme hatası: {e}")
    
    def _save_users(self):
        """Kullanıcıları dosyaya kaydet"""
        try:
            data = {username: user.to_dict() for username, user in self.users.items()}
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"💾 {len(self.users)} kullanıcı kaydedildi")
        except Exception as e:
            print(f"❌ Kullanıcı kaydetme hatası: {e}")
    
    def _ensure_default_users(self):
        """Varsayılan kullanıcıları oluştur"""
        if not self.users:
            # Admin kullanıcı
            admin = User(
                username='admin',
                password_hash=self._hash_password('admin123'),
                role='admin',
                full_name='Sistem Yöneticisi'
            )
            self.users['admin'] = admin
            
            # Normal kullanıcı
            user = User(
                username='user',
                password_hash=self._hash_password('user123'),
                role='user',
                full_name='Standart Kullanıcı'
            )
            self.users['user'] = user
            
            self._save_users()
            print("✅ Varsayılan kullanıcılar oluşturuldu:")
            print("   👤 admin / admin123 (Yönetici)")
            print("   👤 user / user123 (Kullanıcı)")
    
    def login(self, username: str, password: str) -> bool:
        """Kullanıcı girişi"""
        if username not in self.users:
            print(f"❌ Kullanıcı bulunamadı: {username}")
            return False
        
        user = self.users[username]
        password_hash = self._hash_password(password)
        
        if user.password_hash != password_hash:
            print("❌ Yanlış şifre!")
            return False
        
        # Giriş başarılı
        self.current_user = user
        user.last_login = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._save_users()
        
        print(f"✅ Giriş başarılı: {user.full_name} ({user.role})")
        return True
    
    def logout(self):
        """Kullanıcı çıkışı"""
        if self.current_user:
            print(f"👋 Çıkış yapıldı: {self.current_user.full_name}")
            self.current_user = None
        else:
            print("⚠️ Zaten çıkış yapılmış")
    
    def is_logged_in(self) -> bool:
        """Kullanıcı giriş yapmış mı?"""
        return self.current_user is not None
    
    def is_admin(self) -> bool:
        """Kullanıcı admin mi?"""
        return self.current_user and self.current_user.role == 'admin'
    
    def is_user(self) -> bool:
        """Kullanıcı standart kullanıcı mı?"""
        return self.current_user and self.current_user.role == 'user'
    
    def get_current_user(self) -> Optional[User]:
        """Aktif kullanıcıyı getir"""
        return self.current_user
    
    def add_user(self, username: str, password: str, role: str, full_name: str = "") -> bool:
        """Yeni kullanıcı ekle (sadece admin)"""
        if not self.is_admin():
            print("❌ Yetki yok! Sadece admin kullanıcı ekleyebilir.")
            return False
        
        if username in self.users:
            print(f"❌ Kullanıcı zaten mevcut: {username}")
            return False
        
        if role not in ['admin', 'user']:
            print(f"❌ Geçersiz rol: {role}")
            return False
        
        user = User(
            username=username,
            password_hash=self._hash_password(password),
            role=role,
            full_name=full_name or username
        )
        
        self.users[username] = user
        self._save_users()
        
        print(f"✅ Kullanıcı eklendi: {full_name} ({role})")
        return True
    
    def delete_user(self, username: str) -> bool:
        """Kullanıcı sil (sadece admin)"""
        if not self.is_admin():
            print("❌ Yetki yok! Sadece admin kullanıcı silebilir.")
            return False
        
        if username not in self.users:
            print(f"❌ Kullanıcı bulunamadı: {username}")
            return False
        
        if username == 'admin':
            print("❌ Admin kullanıcısı silinemez!")
            return False
        
        if username == self.current_user.username:
            print("❌ Kendi hesabınızı silemezsiniz!")
            return False
        
        del self.users[username]
        self._save_users()
        
        print(f"✅ Kullanıcı silindi: {username}")
        return True
    
    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """Şifre değiştir"""
        if username not in self.users:
            print(f"❌ Kullanıcı bulunamadı: {username}")
            return False
        
        # Kendi şifresini değiştiriyor mu, admin mi değiştiriyor?
        if username != self.current_user.username and not self.is_admin():
            print("❌ Yetki yok! Sadece kendi şifrenizi veya admin olarak değiştirebilirsiniz.")
            return False
        
        user = self.users[username]
        
        # Admin değilse eski şifreyi kontrol et
        if username == self.current_user.username:
            if user.password_hash != self._hash_password(old_password):
                print("❌ Eski şifre yanlış!")
                return False
        
        # Yeni şifreyi kaydet
        user.password_hash = self._hash_password(new_password)
        self._save_users()
        
        print(f"✅ Şifre değiştirildi: {username}")
        return True
    
    def list_users(self) -> List[Dict]:
        """Kullanıcı listesi (sadece admin)"""
        if not self.is_admin():
            print("❌ Yetki yok! Sadece admin kullanıcı listesini görebilir.")
            return []
        
        users_list = []
        for username, user in self.users.items():
            users_list.append({
                'username': username,
                'full_name': user.full_name,
                'role': user.role,
                'created_at': user.created_at,
                'last_login': user.last_login or 'Hiç giriş yapmadı'
            })
        
        return users_list
    
    def get_permissions(self) -> Dict[str, bool]:
        """Kullanıcının yetkilerini getir"""
        print(f"DEBUG: get_permissions() çağrıldı")
        print(f"DEBUG: Giriş yapılmış mı? {self.is_logged_in()}")
    
        if not self.is_logged_in():
           print("DEBUG: Giriş yapılmamış - tüm yetkiler False")
           return {
            'can_view': False,
            'can_control': False,
            'can_edit_settings': False,
            'can_manage_users': False,
            'can_edit_kumes_info': False,
            'can_clear_alarms': False
        }
    
        user = self.get_current_user()
        print(f"DEBUG: Kullanıcı: {user.username}, Rol: {user.role}")
    
        if self.is_admin():
           print("DEBUG: Admin - tüm yetkiler True")
           return {
            'can_view': True,
            'can_control': True,
            'can_edit_settings': True,
            'can_manage_users': True,
            'can_edit_kumes_info': True,
            'can_clear_alarms': True
        }
        else:  # user
           print("DEBUG: User - sınırlı yetkiler")
           perms = {
            'can_view': True,
            'can_control': True,              # ← ÖNEMLİ!
            'can_edit_settings': False,
            'can_manage_users': False,
            'can_edit_kumes_info': False,
            'can_clear_alarms': True           # ← ÖNEMLİ!
        }
           print(f"DEBUG: Yetkiler: {perms}")
           return perms


# =============================================================================
# TEST KODU
# =============================================================================
if __name__ == "__main__":
    print("="*80)
    print("🔐 KULLANICI YÖNETİMİ SİSTEMİ - TEST")
    print("="*80)
    print()
    
    # UserManager oluştur
    user_mgr = UserManager('test_users.json')
    
    print("\n" + "="*80)
    print("TEST 1: Admin Girişi")
    print("="*80)
    
    # Admin giriş
    success = user_mgr.login('admin', 'admin123')
    print(f"Giriş durumu: {success}")
    print(f"Admin mi? {user_mgr.is_admin()}")
    print(f"Yetkiler: {user_mgr.get_permissions()}")
    
    print("\n" + "="*80)
    print("TEST 2: Yeni Kullanıcı Ekleme")
    print("="*80)
    
    # Yeni kullanıcı ekle
    user_mgr.add_user('test', 'test123', 'user', 'Test Kullanıcı')
    
    print("\n" + "="*80)
    print("TEST 3: Kullanıcı Listesi")
    print("="*80)
    
    users = user_mgr.list_users()
    for user in users:
        print(f"  👤 {user['username']:<10} | {user['full_name']:<20} | {user['role']:<10} | Son giriş: {user['last_login']}")
    
    print("\n" + "="*80)
    print("TEST 4: Çıkış ve User Girişi")
    print("="*80)
    
    # Çıkış
    user_mgr.logout()
    
    # User giriş
    success = user_mgr.login('user', 'user123')
    print(f"Giriş durumu: {success}")
    print(f"User mi? {user_mgr.is_user()}")
    print(f"Yetkiler: {user_mgr.get_permissions()}")
    
    print("\n" + "="*80)
    print("TEST 5: Yetki Kontrolü")
    print("="*80)
    
    # User olarak kullanıcı eklemeye çalış (başarısız olmalı)
    user_mgr.add_user('hacker', 'hack123', 'admin', 'Hacker')
    
    print("\n" + "="*80)
    print("TEST 6: Şifre Değiştirme")
    print("="*80)
    
    # Şifre değiştir
    user_mgr.change_password('user', 'user123', 'yenisifre123')
    
    # Eski şifreyle giriş dene (başarısız olmalı)
    user_mgr.logout()
    print("Eski şifreyle giriş deneniyor...")
    user_mgr.login('user', 'user123')
    
    # Yeni şifreyle giriş dene (başarılı olmalı)
    print("Yeni şifreyle giriş deneniyor...")
    user_mgr.login('user', 'yenisifre123')
    
    print("\n" + "="*80)
    print("✅ TÜM TESTLER TAMAMLANDI")
    print("="*80)
    
    # Test dosyasını temizle
    if os.path.exists('test_users.json'):
        os.remove('test_users.json')
        print("🗑️  Test dosyası temizlendi")