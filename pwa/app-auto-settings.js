// app-auto-settings.js - Otomatik Mod Ayarlar Paneli
// ==================== GLOBAL DEĞİŞKENLER ====================
let currentSettings = null;

// ==================== SAYFA OLUŞTUR ====================
function createAutoSettingsPage() {
    const container = document.getElementById('page-settings');
    if (!container) return;
    
    const settingsHTML = `
    <div class="container">
        <h2 style="color: white; margin-bottom: 20px;">🤖 Otomatik Mod Ayarları</h2>
        
        <!-- Mevcut Mod -->
        <div class="settings-card">
            <h3>📊 Mevcut Durum</h3>
            <div class="status-info">
                <p>Mod: <span id="current-mode" class="badge">-</span></p>
                <p>Timeout: <span id="current-timeout">-</span></p>
            </div>
            <div class="button-group">
                <button class="btn btn-primary" onclick="sendCmd('MOD:AUTO')">🤖 Otomatik Moda Geç</button>
                <button class="btn btn-secondary" onclick="sendCmd('MOD:MANUAL')">👤 Manuel Moda Geç</button>
            </div>
        </div>
        
        <!-- Sıcaklık Ayarları -->
        <div class="settings-card">
            <h3>🌡️ Sıcaklık Kontrolü</h3>
            <div class="form-group">
                <label>Minimum Sıcaklık (°C)</label>
                <input type="number" id="temp-min" step="0.5" min="10" max="30" value="18">
                <small>Bu değerin altında fan kapatılır</small>
            </div>
            <div class="form-group">
                <label>Maksimum Sıcaklık (°C)</label>
                <input type="number" id="temp-max" step="0.5" min="15" max="40" value="28">
                <small>Bu değerin üstünde fan açılır</small>
            </div>
        </div>
        
        <!-- Nem Ayarları -->
        <div class="settings-card">
            <h3>💧 Nem Kontrolü</h3>
            <div class="form-group">
                <label>Minimum Nem (%)</label>
                <input type="number" id="humidity-min" step="5" min="20" max="60" value="40">
                <small>Bu değerin altında alarm oluşur</small>
            </div>
            <div class="form-group">
                <label>Maksimum Nem (%)</label>
                <input type="number" id="humidity-max" step="5" min="40" max="90" value="70">
                <small>Bu değerin üstünde alarm oluşur</small>
            </div>
        </div>
        
        <!-- Işık Ayarları -->
        <div class="settings-card">
            <h3>💡 Aydınlatma Kontrolü</h3>
            <div class="form-group">
                <label>LED Açılış Saati</label>
                <input type="number" id="led-start" min="0" max="23" value="6">
                <small>LED'ler bu saatte açılır</small>
            </div>
            <div class="form-group">
                <label>LED Kapanış Saati</label>
                <input type="number" id="led-end" min="0" max="23" value="20">
                <small>LED'ler bu saatte kapanır</small>
            </div>
            <div class="form-group">
                <label class="checkbox-label">
                    <input type="checkbox" id="auto-led" checked>
                    <span>Otomatik LED Kontrolü Aktif</span>
                </label>
            </div>
        </div>
        
        <!-- Genel Ayarlar -->
        <div class="settings-card">
            <h3>⚙️ Genel Ayarlar</h3>
            <div class="form-group">
                <label>Timeout Süresi (saniye)</label>
                <input type="number" id="timeout" min="30" max="600" step="30" value="60">
                <small>Bu süre boyunca komut gelmezse otomatik moda geçer</small>
            </div>
            <div class="form-group">
                <label>Kontrol Aralığı (saniye)</label>
                <input type="number" id="check-interval" min="5" max="60" step="5" value="10">
                <small>Otomatik modda bu sıklıkla kontrol yapılır</small>
            </div>
            <div class="form-group">
                <label class="checkbox-label">
                    <input type="checkbox" id="auto-fan" checked>
                    <span>Otomatik Fan Kontrolü Aktif</span>
                </label>
            </div>
        </div>
        
        <!-- Butonlar -->
        <div class="settings-card">
            <div class="button-group">
                <button class="btn btn-success" onclick="saveAutoSettings()">💾 Kaydet</button>
                <button class="btn btn-info" onclick="loadAutoSettings()">🔄 Yenile</button>
                <button class="btn btn-warning" onclick="resetAutoSettings()">⚠️ Sıfırla</button>
            </div>
        </div>
        
        <!-- Son Güncellenme -->
        <div class="settings-card">
            <p style="text-align: center; color: #888; font-size: 0.9em;">
                Son güncelleme: <span id="last-update">-</span>
            </p>
        </div>
    </div>
    `;
    
    // Eğer ayarlar sayfası boşsa ekle
    if (container.innerHTML.trim() === '') {
        container.innerHTML = settingsHTML;
    }
}

// ==================== AYARLARI YÜKLE ====================
function loadAutoSettings() {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
        showNotification('❌ WebSocket bağlı değil!');
        return;
    }
    
    console.log('📥 Ayarlar isteniyor...');
    
    // Arduino'dan ayarları iste
    const msg = {
        type: 'command',
        command: 'AYAR?'
    };
    
    ws.send(JSON.stringify(msg));
    showNotification('🔄 Ayarlar yükleniyor...');
}

// ==================== AYARLARI GÜNCELLESTİR ====================
function updateAutoSettingsUI(settings) {
    currentSettings = settings;
    
    console.log('📊 Ayarlar güncelleniyor:', settings);
    
    // Form alanlarını doldur
    document.getElementById('timeout').value = settings.timeout || 60;
    document.getElementById('temp-min').value = settings.sicaklik_min || 18;
    document.getElementById('temp-max').value = settings.sicaklik_max || 28;
    document.getElementById('humidity-min').value = settings.nem_min || 40;
    document.getElementById('humidity-max').value = settings.nem_max || 70;
    document.getElementById('led-start').value = settings.led_baslangic || 6;
    document.getElementById('led-end').value = settings.led_bitis || 20;
    document.getElementById('auto-fan').checked = settings.otomatik_fan !== false;
    document.getElementById('auto-led').checked = settings.otomatik_led !== false;
    document.getElementById('check-interval').value = settings.kontrol_araligi || 10;
    
    // Son güncelleme zamanı
    const now = new Date();
    document.getElementById('last-update').textContent = now.toLocaleTimeString('tr-TR');
    
    showNotification('✅ Ayarlar yüklendi');
}

// ==================== AYARLARI KAYDET ====================
function saveAutoSettings() {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
        showNotification('❌ WebSocket bağlı değil!');
        return;
    }
    
    if (!isAuthenticated) {
        showNotification('❌ Önce giriş yapmalısınız!');
        return;
    }
    
    if (currentRole !== 'admin') {
        showNotification('❌ Sadece admin ayarları değiştirebilir!');
        return;
    }
    
    // Form verilerini al
    const settings = {
        timeout: parseInt(document.getElementById('timeout').value),
        sicaklik_min: parseFloat(document.getElementById('temp-min').value),
        sicaklik_max: parseFloat(document.getElementById('temp-max').value),
        nem_min: parseFloat(document.getElementById('humidity-min').value),
        nem_max: parseFloat(document.getElementById('humidity-max').value),
        led_baslangic: parseInt(document.getElementById('led-start').value),
        led_bitis: parseInt(document.getElementById('led-end').value),
        otomatik_fan: document.getElementById('auto-fan').checked,
        otomatik_led: document.getElementById('auto-led').checked,
        kontrol_araligi: parseInt(document.getElementById('check-interval').value)
    };
    
    // Validasyon
    if (settings.sicaklik_min >= settings.sicaklik_max) {
        showNotification('❌ Min sıcaklık, max sıcaklıktan küçük olmalı!');
        return;
    }
    
    if (settings.nem_min >= settings.nem_max) {
        showNotification('❌ Min nem, max nemden küçük olmalı!');
        return;
    }
    
    if (settings.led_baslangic >= settings.led_bitis) {
        showNotification('❌ LED başlangıç saati, bitiş saatinden önce olmalı!');
        return;
    }
    
    console.log('💾 Ayarlar kaydediliyor:', settings);
    
    // Arduino'ya gönder
    const msg = {
        type: 'command',
        command: 'AYAR:' + JSON.stringify(settings)
    };
    
    ws.send(JSON.stringify(msg));
    showNotification('💾 Ayarlar kaydediliyor...');
}

// ==================== AYARLARI SIFIRLA ====================
function resetAutoSettings() {
    if (!confirm('Tüm ayarları varsayılana sıfırlamak istediğinizden emin misiniz?')) {
        return;
    }
    
    if (!ws || ws.readyState !== WebSocket.OPEN) {
        showNotification('❌ WebSocket bağlı değil!');
        return;
    }
    
    if (!isAuthenticated) {
        showNotification('❌ Önce giriş yapmalısınız!');
        return;
    }
    
    if (currentRole !== 'admin') {
        showNotification('❌ Sadece admin ayarları sıfırlayabilir!');
        return;
    }
    
    const msg = {
        type: 'command',
        command: 'AYAR:RESET'
    };
    
    ws.send(JSON.stringify(msg));
    showNotification('⚠️ Ayarlar sıfırlanıyor...');
    
    // 1 saniye sonra yeniden yükle
    setTimeout(loadAutoSettings, 1000);
}

// ==================== MOD DURUMUNU GÜNCELLE ====================
function updateModeStatus(data) {
    const modeBadge = document.getElementById('current-mode');
    const timeoutText = document.getElementById('current-timeout');
    
    if (modeBadge && data.mod) {
        modeBadge.textContent = data.mod === 'otomatik' ? '🤖 Otomatik' : '👤 Manuel';
        modeBadge.className = 'badge ' + (data.mod === 'otomatik' ? 'badge-auto' : 'badge-manual');
    }
    
    if (timeoutText && data.otomatik_ayarlar) {
        timeoutText.textContent = data.otomatik_ayarlar.timeout + ' saniye';
    }
}

// ==================== ARDUINO'DAN AYAR CEVABI ====================
function handleAutoSettingsResponse(data) {
    console.log('📥 Ayar cevabı alındı:', data);
    updateAutoSettingsUI(data);
}

// ==================== CSS STİLLERİ ====================
const autoSettingsStyles = `
<style>
.settings-card {
    background: white;
    padding: 20px;
    border-radius: 12px;
    margin-bottom: 20px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.settings-card h3 {
    margin-bottom: 15px;
    color: var(--primary);
    font-size: 1.2em;
}

.form-group {
    margin-bottom: 20px;
}

.form-group label {
    display: block;
    margin-bottom: 8px;
    font-weight: 600;
    color: var(--text-primary);
}

.form-group input[type="number"] {
    width: 100%;
    padding: 12px;
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    font-size: 1em;
    transition: border-color 0.3s;
}

.form-group input[type="number"]:focus {
    outline: none;
    border-color: var(--primary);
}

.form-group small {
    display: block;
    margin-top: 5px;
    color: var(--text-secondary);
    font-size: 0.85em;
}

.checkbox-label {
    display: flex;
    align-items: center;
    gap: 10px;
    cursor: pointer;
    user-select: none;
}

.checkbox-label input[type="checkbox"] {
    width: 20px;
    height: 20px;
    cursor: pointer;
}

.button-group {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
}

.btn {
    padding: 12px 24px;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s;
    font-size: 0.95em;
}

.btn-primary {
    background: linear-gradient(135deg, var(--primary), var(--secondary));
    color: white;
}

.btn-secondary {
    background: #6c757d;
    color: white;
}

.btn-success {
    background: var(--success);
    color: white;
}

.btn-info {
    background: var(--info);
    color: white;
}

.btn-warning {
    background: var(--warning);
    color: white;
}

.btn:hover {
    opacity: 0.9;
    transform: translateY(-2px);
}

.btn:active {
    transform: translateY(0);
}

.status-info {
    background: rgba(102, 126, 234, 0.1);
    padding: 15px;
    border-radius: 8px;
    margin-bottom: 15px;
}

.status-info p {
    margin: 8px 0;
    font-size: 0.95em;
}

.badge {
    padding: 6px 12px;
    border-radius: 20px;
    font-size: 0.85em;
    font-weight: 600;
}

.badge-auto {
    background: var(--success);
    color: white;
}

.badge-manual {
    background: var(--info);
    color: white;
}

@media (max-width: 600px) {
    .button-group {
        flex-direction: column;
    }
    
    .btn {
        width: 100%;
    }
}
</style>
`;

document.head.insertAdjacentHTML('beforeend', autoSettingsStyles);

// ==================== SAYFA YÜKLENDİĞİNDE ====================
document.addEventListener('DOMContentLoaded', () => {
    console.log('🤖 Otomatik mod ayarları yükleniyor...');
    
    // Ayarlar sayfasını oluştur
    createAutoSettingsPage();
    
    console.log('✅ Otomatik mod ayarları hazır!');
});

console.log('✅ app-auto-settings.js yüklendi');