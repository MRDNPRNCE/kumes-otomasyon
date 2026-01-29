from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, 
    QLineEdit, QPushButton, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor


class LoginWindow(QWidget):
    """Login ekranı - FINAL VERSİYON"""
    
    loginSuccessful = pyqtSignal(object)
    
    def __init__(self, user_manager, parent=None):
        super().__init__(parent)
        self.user_mgr = user_manager
        self._init_ui()
    
    def _init_ui(self):
        """Arayüzü oluştur - OPTIMIZE EDİLMİŞ"""
        self.setWindowTitle("🔐 Kümes Otomasyon - Giriş")
        self.setFixedSize(480, 680)  # Biraz daha küçük ve kompakt
        
        # Her zaman üstte
        self.setWindowFlags(
            Qt.WindowType.Window | 
            Qt.WindowType.WindowStaysOnTopHint
        )
        
        # Arka plan
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#0d1117"))
        self.setPalette(palette)
        
        # ============================================
        # ANA LAYOUT
        # ============================================
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 25, 40, 25)  # Daha dar kenarlık
        main_layout.setSpacing(15)
        
        # Üst boşluk (küçük)
        main_layout.addSpacing(15)
        
        # ============================================
        # LOGO - KÜÇÜLTÜLMÜŞ
        # ============================================
        logo = QLabel("🏠")
        logo.setFont(QFont("Segoe UI", 55))  # 70 → 55
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(logo)
        
        main_layout.addSpacing(8)
        
        # ============================================
        # BAŞLIK - KÜÇÜLTÜLMÜŞ
        # ============================================
        title = QLabel("Kümes Otomasyon Sistemi")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))  # 20 → 18
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #58a6ff;")
        main_layout.addWidget(title)
        
        subtitle = QLabel("Lütfen giriş yapın")
        subtitle.setFont(QFont("Segoe UI", 11))  # 12 → 11
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #8b949e;")
        main_layout.addWidget(subtitle)
        
        main_layout.addSpacing(20)
        
        # ============================================
        # FORM FRAME
        # ============================================
        form_frame = QFrame()
        form_frame.setStyleSheet("""
            QFrame {
                background: #161b22;
                border: 2px solid #30363d;
                border-radius: 12px;
            }
        """)
        
        form_layout = QVBoxLayout(form_frame)
        form_layout.setContentsMargins(25, 25, 25, 25)  # 30 → 25
        form_layout.setSpacing(18)  # 25 → 18
        
        # ============================================
        # KULLANICI ADI
        # ============================================
        username_label = QLabel("👤 Kullanıcı Adı")
        username_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))  # 11 → 10
        username_label.setStyleSheet("""
            color: #c9d1d9; 
            background: transparent;
            padding: 0;
            margin: 0;
        """)
        form_layout.addWidget(username_label)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("admin")
        self.username_input.setFont(QFont("Segoe UI", 12))  # 13 → 12
        self.username_input.setMinimumHeight(45)  # 50 → 45
        self.username_input.setMaximumHeight(45)
        self.username_input.setStyleSheet("""
            QLineEdit {
                background: #0d1117;
                border: 2px solid #30363d;
                border-radius: 8px;
                padding: 0 15px;
                color: #ffffff;
                font-weight: 600;
            }
            QLineEdit:focus {
                border-color: #58a6ff;
                background: #161b22;
            }
            QLineEdit::placeholder {
                color: #6e7681;
            }
        """)
        self.username_input.returnPressed.connect(self._on_login)
        form_layout.addWidget(self.username_input)
        
        form_layout.addSpacing(12)  # 15 → 12
        
        # ============================================
        # ŞİFRE
        # ============================================
        password_label = QLabel("🔒 Şifre")
        password_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))  # 11 → 10
        password_label.setStyleSheet("""
            color: #c9d1d9; 
            background: transparent;
            padding: 0;
            margin: 0;
        """)
        form_layout.addWidget(password_label)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("admin123")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setFont(QFont("Segoe UI", 12))  # 13 → 12
        self.password_input.setMinimumHeight(45)  # 50 → 45
        self.password_input.setMaximumHeight(45)
        self.password_input.setStyleSheet("""
            QLineEdit {
                background: #0d1117;
                border: 2px solid #30363d;
                border-radius: 8px;
                padding: 0 15px;
                color: #ffffff;
                font-weight: 600;
                letter-spacing: 2px;
            }
            QLineEdit:focus {
                border-color: #58a6ff;
                background: #161b22;
            }
            QLineEdit::placeholder {
                color: #6e7681;
                letter-spacing: normal;
            }
        """)
        self.password_input.returnPressed.connect(self._on_login)
        form_layout.addWidget(self.password_input)
        
        form_layout.addSpacing(15)  # 20 → 15
        
        # ============================================
        # GİRİŞ BUTONU
        # ============================================
        login_btn = QPushButton("🚀 Giriş Yap")
        login_btn.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))  # 14 → 13
        login_btn.setMinimumHeight(50)  # 55 → 50
        login_btn.setMaximumHeight(50)
        login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        login_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #238636, stop:1 #196c2e
                );
                color: white;
                border: none;
                border-radius: 8px;
                padding: 5px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2ea043, stop:1 #238636
                );
            }
            QPushButton:pressed {
                background: #196c2e;
            }
        """)
        login_btn.clicked.connect(self._on_login)
        form_layout.addWidget(login_btn)
        
        main_layout.addWidget(form_frame)
        
        main_layout.addSpacing(15)  # 20 → 15
        
        # ============================================
        # BİLGİ KUTUSU - KÜÇÜLTÜLMÜŞ
        # ============================================
        info = QLabel(
            "ℹ️ Varsayılan hesaplar:\n\n"
            "👤 admin / admin123 (Yönetici)\n"
            "👤 user / user123 (Kullanıcı)"
        )
        info.setFont(QFont("Segoe UI", 9))  # 10 → 9
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setStyleSheet("""
            QLabel {
                color: #8b949e;
                background: rgba(88, 166, 255, 0.08);
                border: 1px solid rgba(88, 166, 255, 0.2);
                border-radius: 8px;
                padding: 12px;
                line-height: 1.5;
            }
        """)
        main_layout.addWidget(info)
        
        # Alt boşluk (küçük)
        main_layout.addSpacing(15)
        
        # İlk fokus
        self.username_input.setFocus()
    
    def _on_login(self):
        """Giriş işlemi"""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        if not username:
            QMessageBox.warning(self, "⚠️ Uyarı", "Lütfen kullanıcı adı girin!")
            self.username_input.setFocus()
            return
        
        if not password:
            QMessageBox.warning(self, "⚠️ Uyarı", "Lütfen şifre girin!")
            self.password_input.setFocus()
            return
        
        success = self.user_mgr.login(username, password)
        
        if success:
            user = self.user_mgr.get_current_user()
            role_text = "Yönetici" if user.role == 'admin' else "Kullanıcı"
            
            QMessageBox.information(
                self,
                "✅ Başarılı",
                f"Hoş geldiniz, {user.full_name}!\n\nRol: {role_text}"
            )
            
            self.loginSuccessful.emit(user)
            self.close()
        else:
            QMessageBox.critical(
                self,
                "❌ Hata",
                "Kullanıcı adı veya şifre yanlış!\n\nLütfen tekrar deneyin."
            )
            
            self.password_input.clear()
            self.password_input.setFocus()
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, 
    QLineEdit, QPushButton, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor


class LoginWindow(QWidget):
    """Login ekranı - ULTRA KOMPAKT"""
    
    loginSuccessful = pyqtSignal(object)
    
    def __init__(self, user_manager, parent=None):
        super().__init__(parent)
        self.user_mgr = user_manager
        self._init_ui()
    
    def _init_ui(self):
        """Arayüzü oluştur - ULTRA KÜÇÜK FONTLAR"""
        self.setWindowTitle("🔐 Kümes Otomasyon - Giriş")
        self.setFixedSize(450, 620)  # Daha da küçük
        
        # Her zaman üstte
        self.setWindowFlags(
            Qt.WindowType.Window | 
            Qt.WindowType.WindowStaysOnTopHint
        )
        
        # Arka plan
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#0d1117"))
        self.setPalette(palette)
        
        # ============================================
        # ANA LAYOUT
        # ============================================
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(35, 20, 35, 20)
        main_layout.setSpacing(12)
        
        # Küçük üst boşluk
        main_layout.addSpacing(10)
        
        # ============================================
        # LOGO - ÇOK KÜÇÜK
        # ============================================
        logo = QLabel("🏠")
        logo.setFont(QFont("Segoe UI", 45))  # 55 → 45
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(logo)
        
        main_layout.addSpacing(5)
        
        # ============================================
        # BAŞLIK - ÇOK KÜÇÜK
        # ============================================
        title = QLabel("Kümes Otomasyon Sistemi")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))  # 18 → 16
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #58a6ff;")
        main_layout.addWidget(title)
        
        subtitle = QLabel("Lütfen giriş yapın")
        subtitle.setFont(QFont("Segoe UI", 9))  # 11 → 9
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #8b949e;")
        main_layout.addWidget(subtitle)
        
        main_layout.addSpacing(15)
        
        # ============================================
        # FORM FRAME
        # ============================================
        form_frame = QFrame()
        form_frame.setStyleSheet("""
            QFrame {
                background: #161b22;
                border: 2px solid #30363d;
                border-radius: 10px;
            }
        """)
        
        form_layout = QVBoxLayout(form_frame)
        form_layout.setContentsMargins(20, 20, 20, 20)  # 25 → 20
        form_layout.setSpacing(12)  # 18 → 12
        
        # ============================================
        # KULLANICI ADI - ÇOK KÜÇÜK
        # ============================================
        username_label = QLabel("👤 Kullanıcı Adı")
        username_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))  # 10 → 9
        username_label.setStyleSheet("""
            color: #c9d1d9; 
            background: transparent;
            padding: 0;
            margin: 0;
        """)
        form_layout.addWidget(username_label)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("admin")
        self.username_input.setFont(QFont("Segoe UI", 10))  # 12 → 10
        self.username_input.setMinimumHeight(38)  # 45 → 38
        self.username_input.setMaximumHeight(38)
        self.username_input.setStyleSheet("""
            QLineEdit {
                background: #0d1117;
                border: 2px solid #30363d;
                border-radius: 7px;
                padding: 0 12px;
                color: #ffffff;
                font-weight: 600;
            }
            QLineEdit:focus {
                border-color: #58a6ff;
                background: #161b22;
            }
            QLineEdit::placeholder {
                color: #6e7681;
            }
        """)
        self.username_input.returnPressed.connect(self._on_login)
        form_layout.addWidget(self.username_input)
        
        form_layout.addSpacing(8)  # 12 → 8
        
        # ============================================
        # ŞİFRE - ÇOK KÜÇÜK
        # ============================================
        password_label = QLabel("🔒 Şifre")
        password_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))  # 10 → 9
        password_label.setStyleSheet("""
            color: #c9d1d9; 
            background: transparent;
            padding: 0;
            margin: 0;
        """)
        form_layout.addWidget(password_label)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("admin123")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setFont(QFont("Segoe UI", 10))  # 12 → 10
        self.password_input.setMinimumHeight(38)  # 45 → 38
        self.password_input.setMaximumHeight(38)
        self.password_input.setStyleSheet("""
            QLineEdit {
                background: #0d1117;
                border: 2px solid #30363d;
                border-radius: 7px;
                padding: 0 12px;
                color: #ffffff;
                font-weight: 600;
                letter-spacing: 2px;
            }
            QLineEdit:focus {
                border-color: #58a6ff;
                background: #161b22;
            }
            QLineEdit::placeholder {
                color: #6e7681;
                letter-spacing: normal;
            }
        """)
        self.password_input.returnPressed.connect(self._on_login)
        form_layout.addWidget(self.password_input)
        
        form_layout.addSpacing(10)  # 15 → 10
        
        # ============================================
        # GİRİŞ BUTONU - ÇOK KÜÇÜK
        # ============================================
        login_btn = QPushButton("🚀 Giriş Yap")
        login_btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))  # 13 → 11
        login_btn.setMinimumHeight(42)  # 50 → 42
        login_btn.setMaximumHeight(42)
        login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        login_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #238636, stop:1 #196c2e
                );
                color: white;
                border: none;
                border-radius: 7px;
                padding: 5px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2ea043, stop:1 #238636
                );
            }
            QPushButton:pressed {
                background: #196c2e;
            }
        """)
        login_btn.clicked.connect(self._on_login)
        form_layout.addWidget(login_btn)
        
        main_layout.addWidget(form_frame)
        
        main_layout.addSpacing(12)
        
        # ============================================
        # BİLGİ KUTUSU - AYNI BOYUT
        # ============================================
        info = QLabel(
            "ℹ️ Varsayılan hesaplar:\n\n"
            "👤 admin / admin123 (Yönetici)\n"
            "👤 user / user123 (Kullanıcı)"
        )
        info.setFont(QFont("Segoe UI", 9))  # Aynı kalıyor
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setStyleSheet("""
            QLabel {
                color: #8b949e;
                background: rgba(88, 166, 255, 0.08);
                border: 1px solid rgba(88, 166, 255, 0.2);
                border-radius: 8px;
                padding: 10px;
                line-height: 1.5;
            }
        """)
        main_layout.addWidget(info)
        
        # Alt boşluk
        main_layout.addSpacing(10)
        
        # İlk fokus
        self.username_input.setFocus()
    
    def _on_login(self):
        """Giriş işlemi"""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        if not username:
            QMessageBox.warning(self, "⚠️ Uyarı", "Lütfen kullanıcı adı girin!")
            self.username_input.setFocus()
            return
        
        if not password:
            QMessageBox.warning(self, "⚠️ Uyarı", "Lütfen şifre girin!")
            self.password_input.setFocus()
            return
        
        success = self.user_mgr.login(username, password)
        
        if success:
            user = self.user_mgr.get_current_user()
            role_text = "Yönetici" if user.role == 'admin' else "Kullanıcı"
            
            QMessageBox.information(
                self,
                "✅ Başarılı",
                f"Hoş geldiniz, {user.full_name}!\n\nRol: {role_text}"
            )
            
            self.loginSuccessful.emit(user)
            self.close()
        else:
            QMessageBox.critical(
                self,
                "❌ Hata",
                "Kullanıcı adı veya şifre yanlış!\n\nLütfen tekrar deneyin."
            )
            
            self.password_input.clear()
            self.password_input.setFocus()