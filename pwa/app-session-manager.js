// app-session-manager.js - Advanced Session Management
// ==================== SESSION MANAGER ====================

class SessionManager {
    constructor() {
        this.sessionId = null;
        this.username = null;
        this.role = null;
        this.adminMode = null;  // "active" veya "watching" (sadece admin için)
        this.canControl = false;
        this.permissions = {};
        this.clientType = 'pwa';
    }
    
    // ==================== LOGIN ====================
    login(username, password) {
        if (!ws || ws.readyState !== WebSocket.OPEN) {
            showNotification('❌ WebSocket bağlı değil!');
            return;
        }
        
        const msg = {
            type: 'auth',
            username: username,
            password: password,
            client_type: this.clientType
        };
        
        ws.send(JSON.stringify(msg));
        console.log('🔑 Login mesajı gönderildi:', username);
    }
    
    // ==================== AUTH BAŞARILI ====================
    onAuthSuccess(data) {
        this.sessionId = data.session_id;
        this.username = data.username;
        this.role = data.role;
        this.permissions = data.permissions;
        this.canControl = data.permissions.can_control;
        
        if (this.role === 'admin') {
            this.adminMode = data.admin_mode || 'active';
        }
        
        console.log('✅ Giriş başarılı:', {
            username: this.username,
            role: this.role,
            adminMode: this.adminMode,
            canControl: this.canControl
        });
        
        // UI'yi güncelle
        this.updateUI();
        
        // Başarı bildirimi
        if (this.role === 'admin') {
            showNotification(`✅ Admin olarak giriş yapıldı (${this.adminMode === 'active' ? 'Aktif Mod' : 'İzleme Modu'})`);
        } else {
            showNotification(`✅ Giriş başarılı (${this.canControl ? 'Kontrol edebilirsiniz' : 'Sadece izleme'})`);
        }
    }
    
    // ==================== ADMIN OVERRIDE ====================
    onAdminOverride(data) {
        console.log('⚠️ Admin override:', data);
        
        // Artık user olarak devam
        this.role = 'user';
        this.adminMode = null;
        this.canControl = false;
        
        // Uyarı göster
        showNotification(`⚠️ ${data.message}\n\nArtık sadece izleme modundasınız.`, 'warning');
        
        // UI'yi güncelle
        this.updateUI();
    }
    
    // ==================== KONTROL YETKİSİ VERİLDİ ====================
    onControlAvailable(data) {
        console.log('✅ Kontrol yetkisi verildi:', data);
        
        this.canControl = true;
        
        // Bildirim göster
        showNotification('✅ ' + data.message, 'success');
        
        // UI'yi güncelle
        this.updateUI();
    }
    
    // ==================== KONTROL YETKİSİ KALDIRILDI ====================
    onControlRevoked(data) {
        console.log('⚠️ Kontrol yetkisi kaldırıldı:', data);
        
        this.canControl = false;
        
        // Bildirim göster
        showNotification('⚠️ ' + data.message, 'warning');
        
        // UI'yi güncelle
        this.updateUI();
    }
    
    // ==================== ADMIN AYRILDI ====================
    onAdminLeft(data) {
        console.log('✅ Admin ayrıldı:', data);
        
        if (this.role === 'user') {
            this.canControl = true;
            
            // Bildirim göster
            showNotification('✅ ' + data.message, 'success');
            
            // UI'yi güncelle
            this.updateUI();
        }
    }
    
    // ==================== MOD DEĞİŞTİRME ====================
    switchMode(newMode) {
        if (this.role !== 'admin') {
            showNotification('❌ Sadece admin mod değiştirebilir!');
            return;
        }
        
        if (!ws || ws.readyState !== WebSocket.OPEN) {
            showNotification('❌ WebSocket bağlı değil!');
            return;
        }
        
        const msg = {
            type: 'change_mode',
            session_id: this.sessionId,
            mode: newMode  // "active" veya "watching"
        };
        
        ws.send(JSON.stringify(msg));
        console.log('🔄 Mod değiştirme isteği:', newMode);
    }
    
    onModeChanged(data) {
        console.log('✅ Mod değişti:', data);
        
        this.adminMode = data.mode;
        this.canControl = (data.mode === 'active');
        
        // Bildirim
        if (data.mode === 'active') {
            showNotification('👑 Aktif moda geçtiniz. Tam kontrol!', 'success');
        } else {
            showNotification('👁️ İzleme moduna geçtiniz. Kullanıcılar kontrol edebilir.', 'info');
        }
        
        // UI güncelle
        this.updateUI();
    }
    
    // ==================== KOMUT GÖNDERME ====================
    sendCommand(command) {
        if (!this.canControl) {
            showNotification('❌ Bu işlem için kontrol yetkisi gerekli!');
            return;
        }
        
        if (!ws || ws.readyState !== WebSocket.OPEN) {
            showNotification('❌ WebSocket bağlı değil!');
            return;
        }
        
        const msg = {
            type: 'command',
            command: command,
            session_id: this.sessionId
        };
        
        ws.send(JSON.stringify(msg));
        console.log('📤 Komut gönderildi:', command);
    }
    
    onPermissionDenied(data) {
        console.log('❌ Yetki reddedildi:', data);
        
        let msg = data.message;
        if (data.admin_username) {
            msg += `\n\nAktif Admin: ${data.admin_username} (${data.admin_mode})`;
        }
        
        showNotification('❌ ' + msg, 'error');
    }
    
    // ==================== UI GÜNCELLEME ====================
    updateUI() {
        this.updateHeader();
        this.updateButtons();
        this.updateInfoBanner();
    }
    
    updateHeader() {
        const headerRight = document.querySelector('.header-right');
        if (!headerRight) return;
        
        // Eski user-info'yu temizle
        const oldInfo = headerRight.querySelector('.user-info');
        if (oldInfo) oldInfo.remove();
        
        // Yeni user-info oluştur
        const userInfo = document.createElement('div');
        userInfo.className = 'user-info';
        
        // Icon
        let icon = this.role === 'admin' ? '👑' : '👤';
        if (this.role === 'admin' && this.adminMode === 'watching') {
            icon = '👁️';
        }
        
        // Badge
        let badgeText = '';
        let badgeClass = '';
        
        if (this.role === 'admin') {
            if (this.adminMode === 'active') {
                badgeText = 'Admin Aktif';
                badgeClass = 'badge-admin-active';
            } else {
                badgeText = 'İzleme Modu';
                badgeClass = 'badge-admin-watching';
            }
        } else {
            if (this.canControl) {
                badgeText = 'Kontrol';
                badgeClass = 'badge-user-control';
            } else {
                badgeText = 'Sadece İzleme';
                badgeClass = 'badge-user-watching';
            }
        }
        
        userInfo.innerHTML = `
            <span>${icon} ${this.username}</span>
            <span class="user-badge ${badgeClass}">${badgeText}</span>
            ${this.role === 'admin' ? this.getModeButton() : ''}
            <button class="logout-btn" onclick="sessionManager.logout()">🚪 Çıkış</button>
        `;
        
        // Status badge'den önce ekle
        const statusBadge = document.getElementById('status-badge');
        if (statusBadge) {
            headerRight.insertBefore(userInfo, statusBadge);
        } else {
            headerRight.appendChild(userInfo);
        }
    }
    
    getModeButton() {
        if (this.adminMode === 'active') {
            return '<button class="mode-btn" onclick="sessionManager.switchMode(\'watching\')">👁️ İzleme Modu</button>';
        } else {
            return '<button class="mode-btn mode-btn-control" onclick="sessionManager.switchMode(\'active\')">👑 Kontrolü Al</button>';
        }
    }
    
    updateButtons() {
        // Tüm kontrol butonlarını bul
        const controlButtons = document.querySelectorAll('.btn-control, .control-btn, button[onclick^="sendCmd"]');
        
        controlButtons.forEach(btn => {
            if (this.canControl) {
                btn.disabled = false;
                btn.classList.remove('btn-disabled');
                btn.classList.add('btn-primary');
            } else {
                btn.disabled = true;
                btn.classList.remove('btn-primary');
                btn.classList.add('btn-disabled');
            }
        });
        
        // Ayar butonları (sadece admin aktif modda)
        const settingButtons = document.querySelectorAll('.btn-settings, .settings-btn');
        const canChangeSettings = (this.role === 'admin' && this.adminMode === 'active');
        
        settingButtons.forEach(btn => {
            if (canChangeSettings) {
                btn.disabled = false;
            } else {
                btn.disabled = true;
            }
        });
        
        // Ayar inputları
        const settingInputs = document.querySelectorAll('.settings-card input, .settings-card select');
        settingInputs.forEach(input => {
            input.disabled = !canChangeSettings;
        });
    }
    
    updateInfoBanner() {
        let banner = document.getElementById('info-banner');
        
        if (!banner) {
            banner = document.createElement('div');
            banner.id = 'info-banner';
            banner.className = 'info-banner';
            
            const container = document.querySelector('.container');
            if (container && container.firstChild) {
                container.insertBefore(banner, container.firstChild);
            }
        }
        
        // Banner içeriği
        let message = '';
        let className = 'info-banner';
        
        if (this.role === 'admin') {
            if (this.adminMode === 'active') {
                message = '✅ Tam kontrol modundasınız';
                className += ' banner-success';
            } else {
                message = 'ℹ️ İzleme modundasınız. Kullanıcılar sistemi kontrol edebilir.';
                className += ' banner-info';
            }
        } else {
            if (this.canControl) {
                message = '✅ Kontrol edebilirsiniz!';
                className += ' banner-success';
            } else {
                message = 'ℹ️ Admin aktif modda. Sadece izleyebilirsiniz.';
                className += ' banner-warning';
            }
        }
        
        banner.className = className;
        banner.textContent = message;
    }
    
    // ==================== LOGOUT ====================
    logout() {
        if (confirm('Çıkış yapmak istediğinizden emin misiniz?')) {
            // Session'ı temizle
            this.sessionId = null;
            this.username = null;
            this.role = null;
            this.adminMode = null;
            this.canControl = false;
            this.permissions = {};
            
            // WebSocket kapat
            if (ws) {
                ws.close();
            }
            
            // Sayfayı yenile
            window.location.reload();
        }
    }
}

// Global instance
const sessionManager = new SessionManager();

// ==================== CSS STİLLERİ ====================
const sessionStyles = `
<style>
.user-badge {
    padding: 6px 12px;
    border-radius: 20px;
    font-size: 0.75em;
    font-weight: 600;
}

.badge-admin-active {
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
    box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

.badge-admin-watching {
    background: #2196F3;
    color: white;
}

.badge-user-control {
    background: #4CAF50;
    color: white;
}

.badge-user-watching {
    background: #FF9800;
    color: white;
}

.mode-btn {
    padding: 8px 16px;
    background: #2196F3;
    color: white;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-size: 0.9em;
    font-weight: 600;
    transition: all 0.3s;
}

.mode-btn:hover {
    opacity: 0.9;
    transform: translateY(-2px);
}

.mode-btn-control {
    background: linear-gradient(135deg, #667eea, #764ba2);
}

.info-banner {
    padding: 15px 20px;
    border-radius: 10px;
    margin-bottom: 20px;
    font-weight: 500;
    text-align: center;
}

.banner-success {
    background: rgba(76, 175, 80, 0.1);
    border: 2px solid #4CAF50;
    color: #2E7D32;
}

.banner-info {
    background: rgba(33, 150, 243, 0.1);
    border: 2px solid #2196F3;
    color: #1565C0;
}

.banner-warning {
    background: rgba(255, 152, 0, 0.1);
    border: 2px solid #FF9800;
    color: #E65100;
}

.btn-disabled {
    background: #ccc !important;
    cursor: not-allowed !important;
    opacity: 0.6 !important;
}

.btn-disabled:hover {
    transform: none !important;
}
</style>
`;

document.head.insertAdjacentHTML('beforeend', sessionStyles);

console.log('✅ SessionManager yüklendi');