// app.js - PWA Ana JavaScript Dosyası
// Versiyon: 2.1.0 - Tam Entegre (Mod Badge + Kümes ID + Tüm Özellikler)

// ==================== GLOBAL DEĞİŞKENLER ====================
let ws = null;
let kumesData = null;
let sensorData = null;
let esp32IP = localStorage.getItem('esp32_ip') || '192.168.1.117';
let darkMode = localStorage.getItem('dark_mode') === 'true';
let reconnectTimer = null;
let reconnectInterval = null;

// ==================== WEBSOCKET URL ====================
function getWebSocketURL() {
    // ESP32'ye direkt bağlan
    return `ws://192.168.1.117:81`;  // ← SENİN ESP32 IP'N
}

// ==================== WEBSOCKET BAĞLANTISI ====================
function connectWebSocket() {
    return new Promise((resolve, reject) => {
        const wsUrl = getWebSocketURL();
        console.log(`🔌 WebSocket bağlanıyor: ${wsUrl}`);
        
        updateConnectionStatus(false);
        
        try {
            ws = new WebSocket(wsUrl);
            
            ws.onopen = () => {
                console.log('✅ WebSocket bağlandı');
                updateConnectionStatus(true);
                resolve();
            };
            
            ws.onmessage = (event) => {
                console.log('📥 Veri alındı:', event.data);
                
                try {
                    const data = JSON.parse(event.data);
                    
                    // Auth mesajları
                    if (data.type === 'auth_required') {
                        console.log('🔒 Auth gerekli');
                        if (typeof handleAuthRequired === 'function') {
                            handleAuthRequired();
                        }
                    }
                    else if (data.type === 'auth_success') {
                        if (typeof sessionManager !== 'undefined') {
                            sessionManager.onAuthSuccess(data);
                        }
                        if (typeof handleAuthResponse === 'function') {
                            handleAuthResponse(data);
                        }
                    }
                    else if (data.type === 'auth_failed') {
                        if (typeof handleAuthResponse === 'function') {
                            handleAuthResponse(data);
                        }
                    }
                    // Session yönetimi mesajları
                    else if (data.type === 'admin_override') {
                        if (typeof sessionManager !== 'undefined') {
                            sessionManager.onAdminOverride(data);
                        }
                    }
                    else if (data.type === 'control_available') {
                        if (typeof sessionManager !== 'undefined') {
                            sessionManager.onControlAvailable(data);
                        }
                    }
                    else if (data.type === 'control_revoked') {
                        if (typeof sessionManager !== 'undefined') {
                            sessionManager.onControlRevoked(data);
                        }
                    }
                    else if (data.type === 'admin_left') {
                        if (typeof sessionManager !== 'undefined') {
                            sessionManager.onAdminLeft(data);
                        }
                    }
                    else if (data.type === 'mode_changed') {
                        if (typeof sessionManager !== 'undefined') {
                            sessionManager.onModeChanged(data);
                        }
                    }
                    else if (data.type === 'permission_denied') {
                        if (typeof sessionManager !== 'undefined') {
                            sessionManager.onPermissionDenied(data);
                        }
                    }
                    else if (data.type === 'user_joined') {
                        console.log('👤 Kullanıcı katıldı:', data.username);
                    }
                    // Normal kümes verisi
                    else if (data.sistem === 'kumes') {
                        handleData(data);
                        handleSensorData(data); // ✨ YENİ - Mod badge için
                        
                        // Otomatik ayarları güncelle (eğer varsa)
                        if (data.otomatik_ayarlar && typeof updateAutoSettingsUI === 'function') {
                            updateAutoSettingsUI(data.otomatik_ayarlar);
                        }
                        
                        // Mod durumunu güncelle
                        if (typeof updateModeStatus === 'function') {
                            updateModeStatus(data);
                        }
                    }
                } catch (e) {
                    // JSON değilse, AYAR cevabı olabilir
                    if (event.data.startsWith('AYAR:')) {
                        try {
                            const settingsJson = event.data.substring(5);
                            const settings = JSON.parse(settingsJson);
                            if (typeof handleAutoSettingsResponse === 'function') {
                                handleAutoSettingsResponse(settings);
                            }
                        } catch (err) {
                            console.error('Ayar parse hatası:', err);
                        }
                    } else if (event.data.startsWith('OK:')) {
                        const cmd = event.data.substring(3);
                        console.log('✅ Komut başarılı:', cmd);
                        if (cmd === 'AYAR') {
                            showNotification('✅ Ayarlar kaydedildi!');
                            setTimeout(() => {
                                if (typeof loadAutoSettings === 'function') {
                                    loadAutoSettings();
                                }
                            }, 1000);
                        } else if (cmd === 'RESET') {
                            showNotification('✅ Ayarlar sıfırlandı!');
                        }
                    } else {
                        console.error('❌ JSON parse hatası:', e);
                    }
                }
            };
            
            ws.onerror = (error) => {
                console.error('❌ WebSocket hatası:', error);
                updateConnectionStatus(false);
                reject(error);
            };
            
            ws.onclose = () => {
                console.log('⚠️ WebSocket bağlantısı kesildi');
                updateConnectionStatus(false);
                
                // 5 saniye sonra tekrar bağlan
                if (reconnectTimer) clearTimeout(reconnectTimer);
                reconnectTimer = setTimeout(() => {
                    console.log('🔄 Yeniden bağlanıyor...');
                    connectWebSocket();
                }, 5000);
            };
        } catch (error) {
            console.error('❌ WebSocket oluşturma hatası:', error);
            updateConnectionStatus(false);
            reject(error);
        }
    });
}

// ==================== VERİ İŞLEME (MEVCUT) ====================
function handleData(data) {
    kumesData = data;
    
    // Özet kartları güncelle
    updateSummaryCards(data);
    
    // Kümes detaylarını güncelle (eski versiyon)
    updateKumesDetailsOld(data);
}

// ==================== YENİ SENSÖR VERİ İŞLEME (MOD BADGE İÇİN) ====================
function handleSensorData(data) {
    sensorData = data;
    
    // ✨ MOD BADGE GÜNCELLE
    updateModeBadge(data.mod);
    
    // Özet kartlar
    updateSummaryCards(data);
    
    // Kümes detayları (yeni versiyon)
    updateKumesDetails(data.kumesler);
    
    // Alarm sayısı
    const alarmCount = data.kumesler ? data.kumesler.filter(k => k.alarm).length : 0;
    const alarmCountEl = document.getElementById('alarm-count');
    if (alarmCountEl) alarmCountEl.textContent = alarmCount;
}

// ✨ MOD BADGE GÜNCELLEME - YENİ FONKSIYON
function updateModeBadge(mode) {
    const badge = document.getElementById('mode-badge');
    const text = document.getElementById('mode-text');
    
    if (!badge || !text) return;
    
    if (mode === 'otomatik') {
        badge.className = 'mode-badge otomatik';
        text.innerHTML = '🤖 Otomatik Mod';
    } else {
        badge.className = 'mode-badge manuel';
        text.innerHTML = '✋ Manuel Mod';
    }
}

// ==================== ÖZET KARTLARI ====================
function updateSummaryCards(data) {
    if (!data.kumesler || data.kumesler.length === 0) return;
    
    // Ortalama sıcaklık
    const avgTemp = data.kumesler.reduce((sum, k) => sum + k.sicaklik, 0) / data.kumesler.length;
    const avgTempEl = document.getElementById('avg-temp');
    if (avgTempEl) avgTempEl.textContent = avgTemp.toFixed(1) + '°C';
    
    // Ortalama nem
    const avgHum = data.kumesler.reduce((sum, k) => sum + k.nem, 0) / data.kumesler.length;
    const avgHumEl = document.getElementById('avg-humidity');
    if (avgHumEl) avgHumEl.textContent = avgHum.toFixed(0) + '%';
    
    // Alarm sayısı
    const alarmCount = data.kumesler.filter(k => k.alarm).length;
    const alarmCountEl = document.getElementById('alarm-count');
    if (alarmCountEl) alarmCountEl.textContent = alarmCount;
    
    // Çalışma süresi
    let runtimeEl = document.getElementById('runtime');
    if (!runtimeEl) runtimeEl = document.getElementById('uptime-summary');
    
    if (runtimeEl && data.zaman) {
        const hours = Math.floor(data.zaman / 3600);
        const minutes = Math.floor((data.zaman % 3600) / 60);
        runtimeEl.textContent = `${hours}s ${minutes}d`;
    }
}

// ==================== ESKİ KÜMES DETAYLARI (UYUMLULUK İÇİN) ====================
function updateKumesDetailsOld(data) {
    const container = document.getElementById('kumes-details');
    if (!container || !data.kumesler) return;
    
    // Yeni fonksiyonu kullan
    updateKumesDetails(data.kumesler);
}

// ✨ YENİ KÜMES DETAYLARI - ID + ALARM + DEBUG
function updateKumesDetails(kumesler) {
    const container = document.getElementById('kumes-details');
    if (!container) return;
    
    container.innerHTML = '';
    
    if (!kumesler || kumesler.length === 0) {
        container.innerHTML = '<div class="detail-card"><p style="text-align:center; color: var(--text-secondary);">Veri bekleniyor...</p></div>';
        return;
    }
    
    kumesler.forEach(kumes => {
        const card = document.createElement('div');
        card.className = 'detail-card';
        
        if (kumes.alarm) {
            card.style.borderLeft = '4px solid var(--danger)';
        }
        
        // ✨ ALARM KUTUSU
        const alarmHtml = kumes.alarm ? `
            <div class="alarm-box">
                <div class="alarm-icon">⚠️</div>
                <div class="alarm-text">${kumes.mesaj || 'Alarm aktif!'}</div>
            </div>
        ` : '';
        
        // ✨ DEBUG BİLGİSİ (650Ω sensör için)
        const debugHtml = kumes.debug ? `
            <div style="margin-top: 12px; padding: 12px; background: rgba(0,0,0,0.03); border-radius: 8px; font-size: 0.75em; color: var(--text-secondary);">
                <strong>🔍 Debug:</strong><br>
                Arduino: ${kumes.debug.arduino_v_temp?.toFixed(2) || '--'}V (Sıc) | ${kumes.debug.arduino_v_hum?.toFixed(2) || '--'}V (Nem)<br>
                Şönt: ${kumes.debug.shunt_v_temp?.toFixed(2) || '--'}V (Sıc) | ${kumes.debug.shunt_v_hum?.toFixed(2) || '--'}V (Nem)<br>
                Akım: ${kumes.debug.akim_temp_ma?.toFixed(1) || '--'}mA (Sıc) | ${kumes.debug.akim_hum_ma?.toFixed(1) || '--'}mA (Nem)
            </div>
        ` : '';
        
        card.innerHTML = `
            <div class="detail-header">
                <div class="detail-title">
                    <span class="kumes-number">${kumes.id}</span>
                    🐔 Kümes ${kumes.id}
                </div>
                <div class="detail-badge ${kumes.alarm ? 'alert' : 'ok'}">
                    ${kumes.alarm ? '⚠️ Alarm' : '✅ Normal'}
                </div>
            </div>
            
            ${alarmHtml}
            
            <div class="detail-grid">
                <div class="detail-item">
                    <div class="detail-item-label">🌡️ Sıcaklık</div>
                    <div class="detail-item-value">${kumes.sicaklik?.toFixed(1) || '--'}°C</div>
                </div>
                <div class="detail-item">
                    <div class="detail-item-label">💧 Nem</div>
                    <div class="detail-item-value">${kumes.nem?.toFixed(1) || '--'}%</div>
                </div>
                <div class="detail-item">
                    <div class="detail-item-label">💡 Işık</div>
                    <div class="detail-item-value">${kumes.led ? '🟢 Açık' : '⚫ Kapalı'}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-item-label">🌀 Fan</div>
                    <div class="detail-item-value">${kumes.fan ? '🟢 Açık' : '⚫ Kapalı'}</div>
                </div>
            </div>
            
            ${debugHtml}
            
            <div class="kumes-controls">
                <button class="kumes-btn ${kumes.led ? 'led-on' : 'led-off'}" 
                        onclick="sendCmd('LED:${kumes.led ? '0' : '1'}')">
                    ${kumes.led ? '🌑 Işık Kapat' : '💡 Işık Aç'}
                </button>
                <button class="kumes-btn ${kumes.fan ? 'fan-on' : 'fan-off'}" 
                        onclick="sendCmd('FAN${kumes.id}:${kumes.fan ? '0' : '1'}')">
                    ${kumes.fan ? '⏸️ Fan Kapat' : '🌀 Fan Aç'}
                </button>
            </div>
        `;
        
        container.appendChild(card);
    });
}

// ==================== BAĞLANTI DURUMU ====================
function updateConnectionStatus(connected) {
    const badge = document.getElementById('status-badge');
    if (!badge) return;
    
    if (connected) {
        badge.className = 'status-badge online';
        badge.innerHTML = '<div class="status-dot"></div><span>Bağlı</span>';
    } else {
        badge.className = 'status-badge offline';
        badge.innerHTML = '<div class="status-dot"></div><span>Bağlantı Yok</span>';
    }
}

// ==================== KOMUT GÖNDERME ====================
function sendCmd(command) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        const msg = {
            type: 'command',
            command: command
        };
        
        ws.send(JSON.stringify(msg));
        console.log('📤 Komut gönderildi:', command);
        
        // Feedback mesajları
        if (command.startsWith('LED:1')) showNotification('💡 Işıklar açıldı');
        if (command.startsWith('LED:0')) showNotification('🌑 Işıklar kapandı');
        if (command.startsWith('POMPA:1')) showNotification('💧 Pompa çalıştırıldı');
        if (command.startsWith('FAN')) showNotification('🌀 Fan kontrolü yapıldı');
        if (command.startsWith('YEM:')) showNotification('🌾 Yem dağıtılıyor');
        if (command.startsWith('KAPI:')) showNotification('🚪 Kapı ayarlandı');
        if (command.startsWith('MOD:MANUAL')) showNotification('✋ Manuel moda geçildi');
        if (command.startsWith('MOD:AUTO')) showNotification('🤖 Otomatik moda geçildi');
        
        // 500ms sonra STATUS komutu gönder (güncelleme için)
        setTimeout(() => {
            if (ws && ws.readyState === WebSocket.OPEN) {
                const statusMsg = { type: 'command', command: 'STATUS' };
                ws.send(JSON.stringify(statusMsg));
            }
        }, 500);
    } else {
        console.error('❌ WebSocket bağlı değil!');
        showNotification('❌ Bağlantı yok!');
    }
}

// ==================== BİLDİRİM ====================
function showNotification(message) {
    const toast = document.createElement('div');
    toast.className = 'toast-notification';
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => toast.classList.add('show'), 10);
    
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ==================== SAYFA GEÇİŞLERİ ====================
function showPage(pageName) {
    // Tüm sayfaları gizle
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
    });
    
    // Seçili sayfayı göster
    document.getElementById('page-' + pageName).classList.add('active');
    
    // Nav itemları güncelle
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    
    if (event && event.currentTarget) {
        event.currentTarget.classList.add('active');
    }
}

// ==================== KAPI KONTROLÜ ====================
function setDoor(angle) {
    const slider = document.getElementById('door-slider');
    const angleDisplay = document.getElementById('door-angle');
    
    if (slider) slider.value = angle;
    if (angleDisplay) angleDisplay.textContent = angle + '°';
    
    sendCmd('KAPI:' + angle);
}

// ==================== DARK MODE ====================
function toggleTheme() {
    darkMode = !darkMode;
    document.body.classList.toggle('dark-mode', darkMode);
    localStorage.setItem('dark_mode', darkMode);
    
    const toggle = document.getElementById('dark-mode-toggle');
    if (toggle) toggle.checked = darkMode;
}

function toggleDarkMode() {
    toggleTheme();
}

function checkDarkMode() {
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        if (!localStorage.getItem('dark_mode')) {
            document.body.classList.add('dark-mode');
            const toggle = document.getElementById('dark-mode-toggle');
            if (toggle) toggle.checked = true;
        }
    }
}

// ==================== IP GÜNCELLEME ====================
function updateIP() {
    const ipInput = document.getElementById('esp32-ip');
    if (!ipInput) return;
    
    const ip = ipInput.value;
    localStorage.setItem('esp32_ip', ip);
    esp32IP = ip;
    
    showNotification('💾 IP adresi kaydedildi! Bağlanılıyor...');
    
    if (ws) ws.close();
    setTimeout(connectWebSocket, 1000);
}

// ==================== AYARLARI YÜKLE ====================
function loadSettings() {
    const savedIP = localStorage.getItem('esp32_ip');
    const ipInput = document.getElementById('esp32-ip');
    if (savedIP && ipInput) {
        ipInput.value = savedIP;
    }
    
    const darkModeStored = localStorage.getItem('dark_mode') === 'true';
    if (darkModeStored) {
        document.body.classList.add('dark-mode');
        const toggle = document.getElementById('dark-mode-toggle');
        if (toggle) toggle.checked = true;
    }
}

// ==================== TOAST CSS ====================
const toastStyles = `
<style>
.toast-notification {
    position: fixed;
    bottom: 100px;
    left: 50%;
    transform: translateX(-50%) translateY(100px);
    background: rgba(0, 0, 0, 0.8);
    color: white;
    padding: 12px 24px;
    border-radius: 25px;
    font-size: 0.9em;
    z-index: 10000;
    opacity: 0;
    transition: all 0.3s;
}

.toast-notification.show {
    transform: translateX(-50%) translateY(0);
    opacity: 1;
}
</style>
`;

document.head.insertAdjacentHTML('beforeend', toastStyles);

// ==================== PWA KURULUM ====================
let deferredPrompt;

window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    console.log('PWA kurulumu hazır');
});

// ==================== KESİNTİSİZ BAĞLANTI ====================
window.addEventListener('online', () => {
    showNotification('🟢 İnternet bağlantısı geri geldi');
    connectWebSocket();
});

window.addEventListener('offline', () => {
    showNotification('🔴 İnternet bağlantısı kesildi');
});

// ==================== PERİYODİK GÜNCELLEME ====================
setInterval(() => {
    if (ws && ws.readyState === WebSocket.OPEN) {
        const statusMsg = { type: 'command', command: 'STATUS' };
        ws.send(JSON.stringify(statusMsg));
    }
}, 5000); // Her 5 saniyede bir güncelleme

// ==================== SAYFA YÜKLENDİĞİNDE ====================
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Kümes Otomasyon PWA başlatılıyor...');
    
    // Ayarları yükle
    loadSettings();
    
    // Dark mode kontrolü
    if (darkMode) {
        document.body.classList.add('dark-mode');
    }
    checkDarkMode();
    
    // WebSocket bağlan
    connectWebSocket();
    
    // Service Worker
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('sw.js')
            .then(() => console.log('✅ Service Worker kaydedildi'))
            .catch(err => console.error('❌ SW hatası:', err));
    }
    
    // Auto-reconnect
    setInterval(() => {
        if (!ws || ws.readyState !== WebSocket.OPEN) {
            connectWebSocket();
        }
    }, 5000);
    
    console.log('✅ Uygulama hazır!');
});

console.log('✅ app.js v2.1.0 yüklendi - Tam Entegre (Mod + ID + Auth + Alarm)');
