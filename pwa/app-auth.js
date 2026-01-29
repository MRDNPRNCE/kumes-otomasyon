// app-auth.js - DÜZELTİLMİŞ VERSİYON
// Giriş butonu tıklanabilir hale getirildi

// ==================== GLOBAL AUTH DEĞİŞKENLERİ ====================
let isAuthenticated = false;
let currentUser = null;
let currentRole = null;
let authToken = null;

// ==================== LOGIN MODAL HTML ====================
function createLoginModal() {
    const modalHTML = `
    <div id="loginModal" class="login-modal">
        <div class="login-card">
            <div class="login-header">
                <h2>🐔 Kümes Otomasyon</h2>
                <p>Giriş Yapın</p>
            </div>
            
            <form class="login-form" onsubmit="handleLogin(event); return false;">
                <div class="input-group">
                    <label>👤 Kullanıcı Adı</label>
                    <input type="text" id="login-username" placeholder="admin" autocomplete="username">
                </div>
                
                <div class="input-group">
                    <label>🔒 Şifre</label>
                    <input type="password" id="login-password" placeholder="admin123" autocomplete="current-password">
                </div>
                
                <div class="remember-me">
                    <label>
                        <input type="checkbox" id="remember-me">
                        <span>Beni Hatırla</span>
                    </label>
                </div>
                
                <button type="submit" class="btn btn-login">
                    🔓 Giriş Yap
                </button>
                
                <div id="login-error" class="login-error"></div>
                
                <div class="login-info">
                    <p><strong>Varsayılan Hesaplar:</strong></p>
                    <p>👤 Admin: <code>admin</code> / <code>admin123</code></p>
                    <p>👤 User: <code>user</code> / <code>user123</code></p>
                </div>
            </form>
        </div>
    </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHTML);
}

// ==================== LOGIN MODAL CSS ====================
const loginStyles = `
<style>
.login-modal {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.8);
    backdrop-filter: blur(10px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9999;
}

.login-card {
    background: var(--card-bg);
    border-radius: 20px;
    padding: 40px;
    max-width: 400px;
    width: 90%;
    box-shadow: 0 20px 60px rgba(0,0,0,0.5);
    animation: slideIn 0.3s;
}

@keyframes slideIn {
    from {
        opacity: 0;
        transform: translateY(-50px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.login-header {
    text-align: center;
    margin-bottom: 30px;
}

.login-header h2 {
    font-size: 2em;
    color: var(--primary);
    margin-bottom: 10px;
}

.login-header p {
    color: var(--text-secondary);
    font-size: 1.1em;
}

.login-form {
    width: 100%;
}

.login-form .input-group {
    margin-bottom: 20px;
}

.login-form label {
    display: block;
    margin-bottom: 8px;
    font-weight: 600;
    color: var(--text-primary);
}

.login-form input[type="text"],
.login-form input[type="password"] {
    width: 100%;
    padding: 14px;
    border: 2px solid rgba(0,0,0,0.1);
    border-radius: 12px;
    font-size: 1em;
    background: var(--card-bg);
    color: var(--text-primary);
    transition: border 0.3s;
}

.login-form input:focus {
    outline: none;
    border-color: var(--primary);
}

.remember-me {
    margin-bottom: 20px;
    display: flex;
    align-items: center;
}

.remember-me label {
    display: flex;
    align-items: center;
    cursor: pointer;
    margin: 0;
    user-select: none;
}

.remember-me input[type="checkbox"] {
    width: 20px;
    height: 20px;
    margin-right: 8px;
    cursor: pointer;
}

.btn-login {
    width: 100%;
    padding: 16px;
    border: none;
    border-radius: 12px;
    font-size: 1em;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
    color: white;
}

.btn-login:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(0,0,0,0.2);
}

.btn-login:active {
    transform: translateY(0);
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.btn-login:disabled {
    opacity: 0.6;
    cursor: not-allowed;
}

.login-error {
    background: #f8d7da;
    color: #721c24;
    padding: 12px;
    border-radius: 8px;
    margin-top: 15px;
    display: none;
    text-align: center;
}

.login-error.show {
    display: block;
}

.login-info {
    margin-top: 20px;
    padding: 15px;
    background: rgba(102, 126, 234, 0.1);
    border-radius: 10px;
    font-size: 0.85em;
    color: var(--text-secondary);
}

.login-info p {
    margin: 5px 0;
}

.login-info code {
    background: rgba(0,0,0,0.1);
    padding: 2px 6px;
    border-radius: 4px;
    font-family: 'Courier New', monospace;
}

.user-info {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 16px;
    background: rgba(102, 126, 234, 0.1);
    border-radius: 20px;
    font-size: 0.9em;
}

.user-badge {
    background: var(--primary);
    color: white;
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 0.75em;
    font-weight: 600;
}

.logout-btn {
    width: auto;
    padding: 8px 16px;
    background: var(--danger);
    color: white;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-size: 0.9em;
}

.logout-btn:hover {
    opacity: 0.9;
}
</style>
`;

document.head.insertAdjacentHTML('beforeend', loginStyles);

// ==================== AUTH FONKSİYONLARI ====================
function checkAuth() {
    // LocalStorage'dan auth bilgisi kontrol et
    const savedAuth = localStorage.getItem('kumes_auth');
    
    if (savedAuth) {
        try {
            const auth = JSON.parse(savedAuth);
            currentUser = auth.username;
            currentRole = auth.role;
            authToken = auth.token;
            isAuthenticated = true;
            
            showMainApp();
            reconnectWithAuth();
        } catch (e) {
            console.error('Auth parse hatası:', e);
            localStorage.removeItem('kumes_auth');
            showLoginModal();
        }
    } else {
        showLoginModal();
    }
}

function showLoginModal() {
    createLoginModal();
    
    // Enter tuşu ile giriş
    document.getElementById('login-password').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleLogin(e);
        }
    });
}

function hideLoginModal() {
    const modal = document.getElementById('loginModal');
    if (modal) {
        modal.remove();
    }
}

function showMainApp() {
    hideLoginModal();
    updateUserUI();
}

function updateUserUI() {
    // Header'a kullanıcı bilgisi ekle
    const headerRight = document.querySelector('.header-right');
    if (!headerRight) return;
    
    // Eski user info varsa kaldır
    const oldUserInfo = document.querySelector('.user-info');
    if (oldUserInfo) oldUserInfo.remove();
    
    // Yeni user info ekle
    const userInfo = document.createElement('div');
    userInfo.className = 'user-info';
    userInfo.innerHTML = `
        <span>👤 ${currentUser}</span>
        <span class="user-badge">${currentRole === 'admin' ? 'Admin' : 'User'}</span>
        <button class="logout-btn" onclick="handleLogout()">🚪 Çıkış</button>
    `;
    
    // Status badge'den önce ekle
    const statusBadge = document.getElementById('status-badge');
    if (statusBadge) {
        headerRight.insertBefore(userInfo, statusBadge);
    } else {
        headerRight.appendChild(userInfo);
    }
}

function handleLogin(event) {
    if (event) {
        event.preventDefault();
    }
    
    const username = document.getElementById('login-username').value.trim();
    const password = document.getElementById('login-password').value.trim();
    const rememberMe = document.getElementById('remember-me').checked;
    
    console.log('🔑 Login denemesi:', username);
    
    if (!username || !password) {
        showLoginError('Kullanıcı adı ve şifre gerekli!');
        return;
    }
    
    // Buton disable et
    const loginBtn = document.querySelector('.btn-login');
    if (loginBtn) {
        loginBtn.disabled = true;
        loginBtn.textContent = '🔄 Giriş yapılıyor...';
    }
    
    // WebSocket'e auth mesajı gönder
    if (!ws || ws.readyState !== WebSocket.OPEN) {
        console.log('WebSocket bağlı değil, bağlanıyor...');
        
        // Önce WebSocket bağlan
        connectWebSocket().then(() => {
            // 1 saniye bekle
            setTimeout(() => {
                sendAuthRequest(username, password, rememberMe);
            }, 1000);
        }).catch((error) => {
            console.error('WebSocket bağlantı hatası:', error);
            showLoginError('WebSocket bağlantısı kurulamadı!');
            if (loginBtn) {
                loginBtn.disabled = false;
                loginBtn.textContent = '🔓 Giriş Yap';
            }
        });
    } else {
        sendAuthRequest(username, password, rememberMe);
    }
}

function sendAuthRequest(username, password, rememberMe) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        // Auth mesajı gönder
        const authMsg = {
            type: 'auth',
            username: username,
            password: password
        };
        
        console.log('📤 Auth mesajı gönderiliyor...');
        ws.send(JSON.stringify(authMsg));
        
        showLoginError('Giriş yapılıyor...', 'info');
        
        // Timeout ekle (10 saniye)
        setTimeout(() => {
            if (!isAuthenticated) {
                showLoginError('Zaman aşımı! Lütfen tekrar deneyin.');
                const loginBtn = document.querySelector('.btn-login');
                if (loginBtn) {
                    loginBtn.disabled = false;
                    loginBtn.textContent = '🔓 Giriş Yap';
                }
            }
        }, 10000);
    } else {
        showLoginError('WebSocket bağlı değil!');
        const loginBtn = document.querySelector('.btn-login');
        if (loginBtn) {
            loginBtn.disabled = false;
            loginBtn.textContent = '🔓 Giriş Yap';
        }
    }
}

function handleAuthResponse(data) {
    const loginBtn = document.querySelector('.btn-login');
    
    if (data.type === 'auth_success') {
        // Başarılı giriş
        currentUser = data.username;
        currentRole = data.role;
        authToken = Date.now().toString();
        isAuthenticated = true;
        
        console.log('✅ Giriş başarılı:', currentUser, currentRole);
        
        // Remember me
        const rememberMe = document.getElementById('remember-me');
        if (rememberMe && rememberMe.checked) {
            const auth = {
                username: currentUser,
                role: currentRole,
                token: authToken
            };
            localStorage.setItem('kumes_auth', JSON.stringify(auth));
        }
        
        showMainApp();
        
        if (typeof showNotification === 'function') {
            showNotification(`✅ Hoş geldin ${currentUser}!`);
        }
        
        if (typeof hapticFeedback === 'function') {
            hapticFeedback('success');
        }
    } 
    else if (data.type === 'auth_failed') {
        // Başarısız giriş
        console.error('❌ Giriş başarısız:', data.message);
        showLoginError(data.message || 'Kullanıcı adı veya şifre hatalı!');
        
        if (loginBtn) {
            loginBtn.disabled = false;
            loginBtn.textContent = '🔓 Giriş Yap';
        }
        
        if (typeof hapticFeedback === 'function') {
            hapticFeedback('error');
        }
    }
}

function handleLogout() {
    if (confirm('Çıkış yapmak istediğinize emin misiniz?')) {
        // Auth bilgilerini temizle
        isAuthenticated = false;
        currentUser = null;
        currentRole = null;
        authToken = null;
        
        localStorage.removeItem('kumes_auth');
        
        // WebSocket bağlantısını kes
        if (ws) {
            ws.close();
        }
        
        // Sayfayı yenile (login ekranı gösterir)
        location.reload();
    }
}

function showLoginError(message, type = 'error') {
    const errorDiv = document.getElementById('login-error');
    if (!errorDiv) return;
    
    errorDiv.textContent = message;
    errorDiv.className = 'login-error show';
    
    if (type === 'info') {
        errorDiv.style.background = '#d1ecf1';
        errorDiv.style.color = '#0c5460';
    } else {
        errorDiv.style.background = '#f8d7da';
        errorDiv.style.color = '#721c24';
    }
    
    // 5 saniye sonra gizle (error ise)
    if (type === 'error') {
        setTimeout(() => {
            errorDiv.classList.remove('show');
        }, 5000);
    }
}

// ==================== WEBSOCKET GÜNCELLEMESİ ====================
// NOT: connectWebSocket fonksiyonu app.js'de tanımlı!
// app.js dinamik port desteği ile WebSocket'i yönetiyor

// Auth ile yeniden bağlan
function reconnectWithAuth() {
    connectWebSocket().then(() => {
        console.log('✅ WebSocket yeniden bağlandı');
    }).catch(error => {
        console.error('❌ WebSocket yeniden bağlantı hatası:', error);
    });
}

// ==================== GÜNCELLENMİŞ KOMUT GÖNDERME ====================
function sendCmd(command) {
    if (!isAuthenticated) {
        if (typeof showNotification === 'function') {
            showNotification('❌ Önce giriş yapmalısınız!');
        }
        return;
    }
    
    if (ws && ws.readyState === WebSocket.OPEN) {
        const msg = {
            type: 'command',
            command: command
        };
        
        ws.send(JSON.stringify(msg));
        console.log('📤 Komut gönderildi:', command);
        
        if (typeof showNotification === 'function') {
            showNotification(`📤 ${command}`);
        }
    } else {
        console.error('❌ WebSocket bağlı değil!');
        if (typeof showNotification === 'function') {
            showNotification('❌ Bağlantı yok!');
        }
    }
}

// ==================== SAYFA YÜKLENDİĞİNDE ====================
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Auth sistemi başlatılıyor...');
    
    // IP adresini yükle
    const ipInput = document.getElementById('esp32-ip');
    if (ipInput && typeof esp32IP !== 'undefined') {
        ipInput.value = esp32IP;
    }
    
    // Dark mode'u yükle
    const darkModeToggle = document.getElementById('dark-mode-toggle');
    if (darkModeToggle && typeof darkMode !== 'undefined') {
        if (darkMode) {
            document.body.classList.add('dark-mode');
            darkModeToggle.checked = true;
        }
    }
    
    // Auth kontrol et
    checkAuth();
    
    // Service Worker'ı kaydet
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('sw.js')
            .then(reg => console.log('✅ Service Worker kaydedildi'))
            .catch(err => console.error('❌ Service Worker hatası:', err));
    }
    
    console.log('✅ Auth sistemi hazır!');
});

// ==================== YETKİ KONTROLÜ ====================
function checkPermission(action) {
    if (!isAuthenticated) {
        if (typeof showNotification === 'function') {
            showNotification('❌ Giriş yapmalısınız!');
        }
        return false;
    }
    
    // Admin her şeyi yapabilir
    if (currentRole === 'admin') {
        return true;
    }
    
    // User için kısıtlamalar
    const restrictedActions = ['RESET', 'CONFIG'];
    
    if (restrictedActions.includes(action)) {
        if (typeof showNotification === 'function') {
            showNotification('❌ Bu işlem için admin yetkisi gerekli!');
        }
        return false;
    }
    
    return true;
}

console.log('✅ Auth sistemi yüklendi (DÜZELTİLMİŞ)');