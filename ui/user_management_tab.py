# -*- coding: utf-8 -*-
"""
Kullanıcı Yönetimi Sekmesi
- Sadece admin erişebilir
- Kullanıcı listesi
- Kullanıcı ekleme/silme
- Şifre değiştirme
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTableWidget, QTableWidgetItem,
    QLineEdit, QComboBox, QMessageBox, QDialog,
    QFormLayout, QFrame, QHeaderView, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class UserManagementTab(QWidget):
    """Kullanıcı yönetimi sekmesi"""
    
    def __init__(self, user_manager, parent=None):
        super().__init__(parent)
        self.user_mgr = user_manager
        self._init_ui()
        self._refresh_users()
    
    def _init_ui(self):
        """Arayüzü oluştur"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Başlık
        title = QLabel("👥 KULLANICI YÖNETİMİ")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #58a6ff; padding: 15px; background: rgba(88,166,255,0.1); border-radius: 8px;")
        layout.addWidget(title)
        
        # Butonlar
        btn_layout = QHBoxLayout()
        
        add_btn = QPushButton("➕ Yeni Kullanıcı Ekle")
        add_btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setStyleSheet("""
            QPushButton {
                background: #48bb78;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: #38a169;
            }
        """)
        add_btn.clicked.connect(self._add_user)
        btn_layout.addWidget(add_btn)
        
        refresh_btn = QPushButton("🔄 Yenile")
        refresh_btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: #30363d;
                color: #c9d1d9;
                border: 2px solid #484f58;
                padding: 12px 24px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: #484f58;
                border-color: #58a6ff;
            }
        """)
        refresh_btn.clicked.connect(self._refresh_users)
        btn_layout.addWidget(refresh_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Kullanıcı Adı", "Tam Ad", "Rol", "Oluşturulma", "Son Giriş", "İşlemler"
        ])
        
        # Tablo stili
        self.table.setStyleSheet("""
            QTableWidget {
                background: #161b22;
                border: 2px solid #30363d;
                border-radius: 8px;
                color: #c9d1d9;
                gridline-color: #30363d;
            }
            QTableWidget::item {
                padding: 10px;
            }
            QTableWidget::item:selected {
                background: #1f6feb;
            }
            QHeaderView::section {
                background: #21262d;
                color: #58a6ff;
                padding: 12px;
                border: none;
                font-weight: bold;
                font-size: 12px;
            }
        """)
        
        # Başlık ayarları
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(5, 200)
        
        # Satır yüksekliği
        self.table.verticalHeader().setDefaultSectionSize(50)
        self.table.verticalHeader().setVisible(False)
        
        layout.addWidget(self.table)
        
        # Bilgi
        info = QLabel("ℹ️ Admin kullanıcısı silinemez. Kendi hesabınızı silemezsiniz.")
        info.setStyleSheet("color: #8b949e; padding: 10px; background: rgba(88,166,255,0.05); border-radius: 6px;")
        layout.addWidget(info)
    
    def _refresh_users(self):
        """Kullanıcı listesini yenile"""
        users = self.user_mgr.list_users()
        
        self.table.setRowCount(len(users))
        
        for row, user in enumerate(users):
            # Kullanıcı adı
            self.table.setItem(row, 0, QTableWidgetItem(user['username']))
            
            # Tam ad
            self.table.setItem(row, 1, QTableWidgetItem(user['full_name']))
            
            # Rol
            role_text = "🔑 Admin" if user['role'] == 'admin' else "👤 Kullanıcı"
            role_item = QTableWidgetItem(role_text)
            if user['role'] == 'admin':
                role_item.setForeground(Qt.GlobalColor.yellow)
            self.table.setItem(row, 2, role_item)
            
            # Oluşturulma
            self.table.setItem(row, 3, QTableWidgetItem(user['created_at']))
            
            # Son giriş
            self.table.setItem(row, 4, QTableWidgetItem(user['last_login']))
            
            # İşlemler
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(5, 5, 5, 5)
            btn_layout.setSpacing(5)
            
            # Şifre değiştir butonu
            pwd_btn = QPushButton("🔒 Şifre")
            pwd_btn.setStyleSheet("""
                QPushButton {
                    background: #1f6feb;
                    color: white;
                    border: none;
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-size: 10px;
                }
                QPushButton:hover {
                    background: #58a6ff;
                }
            """)
            pwd_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            pwd_btn.clicked.connect(lambda checked, u=user['username']: self._change_password(u))
            btn_layout.addWidget(pwd_btn)
            
            # Sil butonu (admin ve kendi hesabı değilse)
            if user['username'] != 'admin' and user['username'] != self.user_mgr.current_user.username:
                del_btn = QPushButton("🗑️ Sil")
                del_btn.setStyleSheet("""
                    QPushButton {
                        background: #ff4444;
                        color: white;
                        border: none;
                        padding: 6px 12px;
                        border-radius: 4px;
                        font-size: 10px;
                    }
                    QPushButton:hover {
                        background: #cc0000;
                    }
                """)
                del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                del_btn.clicked.connect(lambda checked, u=user['username']: self._delete_user(u))
                btn_layout.addWidget(del_btn)
            
            self.table.setCellWidget(row, 5, btn_widget)
    
    def _add_user(self):
        """Yeni kullanıcı ekle dialog"""
        dialog = AddUserDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            username, password, role, full_name = dialog.get_data()
            
            success = self.user_mgr.add_user(username, password, role, full_name)
            
            if success:
                QMessageBox.information(
                    self,
                    "Başarılı",
                    f"✅ Kullanıcı eklendi: {full_name}"
                )
                self._refresh_users()
            else:
                QMessageBox.warning(
                    self,
                    "Hata",
                    "❌ Kullanıcı eklenemedi!"
                )
    
    def _delete_user(self, username):
        """Kullanıcı sil"""
        reply = QMessageBox.question(
            self,
            "Kullanıcı Sil",
            f"⚠️ '{username}' kullanıcısını silmek istediğinizden emin misiniz?\n\n"
            "Bu işlem geri alınamaz!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success = self.user_mgr.delete_user(username)
            
            if success:
                QMessageBox.information(
                    self,
                    "Başarılı",
                    f"✅ Kullanıcı silindi: {username}"
                )
                self._refresh_users()
            else:
                QMessageBox.warning(
                    self,
                    "Hata",
                    "❌ Kullanıcı silinemedi!"
                )
    
    def _change_password(self, username):
        """Şifre değiştir dialog"""
        dialog = ChangePasswordDialog(username, self.user_mgr, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            old_pwd, new_pwd = dialog.get_data()
            
            success = self.user_mgr.change_password(username, old_pwd, new_pwd)
            
            if success:
                QMessageBox.information(
                    self,
                    "Başarılı",
                    f"✅ Şifre değiştirildi: {username}"
                )
            else:
                QMessageBox.warning(
                    self,
                    "Hata",
                    "❌ Şifre değiştirilemedi!"
                )


class AddUserDialog(QDialog):
    """Kullanıcı ekleme dialog'u"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Yeni Kullanıcı Ekle")
        self.setFixedWidth(400)
        self._init_ui()
    
    def _init_ui(self):
        """Arayüz"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Form
        form = QFormLayout()
        form.setSpacing(10)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Kullanıcı adı...")
        form.addRow("👤 Kullanıcı Adı:", self.username_input)
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Şifre...")
        form.addRow("🔒 Şifre:", self.password_input)
        
        self.full_name_input = QLineEdit()
        self.full_name_input.setPlaceholderText("Tam ad...")
        form.addRow("📝 Tam Ad:", self.full_name_input)
        
        self.role_combo = QComboBox()
        self.role_combo.addItems(["user", "admin"])
        form.addRow("🔑 Rol:", self.role_combo)
        
        layout.addLayout(form)
        
        # Butonlar
        btn_layout = QHBoxLayout()
        
        ok_btn = QPushButton("✅ Ekle")
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("❌ İptal")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
    
    def get_data(self):
        """Verileri döndür"""
        return (
            self.username_input.text().strip(),
            self.password_input.text(),
            self.role_combo.currentText(),
            self.full_name_input.text().strip()
        )


class ChangePasswordDialog(QDialog):
    """Şifre değiştirme dialog'u"""
    
    def __init__(self, username, user_mgr, parent=None):
        super().__init__(parent)
        self.username = username
        self.user_mgr = user_mgr
        self.setWindowTitle(f"Şifre Değiştir - {username}")
        self.setFixedWidth(400)
        self._init_ui()
    
    def _init_ui(self):
        """Arayüz"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Bilgi
        info = QLabel(f"🔒 {self.username} kullanıcısının şifresini değiştiriyorsunuz")
        info.setStyleSheet("color: #58a6ff; padding: 10px; background: rgba(88,166,255,0.1); border-radius: 6px;")
        layout.addWidget(info)
        
        # Form
        form = QFormLayout()
        form.setSpacing(10)
        
        # Sadece kendi şifresini değiştiriyorsa eski şifre iste
        if self.username == self.user_mgr.current_user.username:
            self.old_password_input = QLineEdit()
            self.old_password_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.old_password_input.setPlaceholderText("Mevcut şifre...")
            form.addRow("🔓 Eski Şifre:", self.old_password_input)
        else:
            self.old_password_input = None
        
        self.new_password_input = QLineEdit()
        self.new_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_password_input.setPlaceholderText("Yeni şifre...")
        form.addRow("🔒 Yeni Şifre:", self.new_password_input)
        
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_input.setPlaceholderText("Yeni şifre tekrar...")
        form.addRow("🔒 Tekrar:", self.confirm_password_input)
        
        layout.addLayout(form)
        
        # Butonlar
        btn_layout = QHBoxLayout()
        
        ok_btn = QPushButton("✅ Değiştir")
        ok_btn.clicked.connect(self._validate_and_accept)
        btn_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("❌ İptal")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
    
    def _validate_and_accept(self):
        """Validasyon ve kabul"""
        new_pwd = self.new_password_input.text()
        confirm_pwd = self.confirm_password_input.text()
        
        if new_pwd != confirm_pwd:
            QMessageBox.warning(
                self,
                "Hata",
                "❌ Yeni şifreler eşleşmiyor!"
            )
            return
        
        if len(new_pwd) < 6:
            QMessageBox.warning(
                self,
                "Hata",
                "❌ Şifre en az 6 karakter olmalı!"
            )
            return
        
        self.accept()
    
    def get_data(self):
        """Verileri döndür"""
        old_pwd = self.old_password_input.text() if self.old_password_input else ""
        new_pwd = self.new_password_input.text()
        return (old_pwd, new_pwd)