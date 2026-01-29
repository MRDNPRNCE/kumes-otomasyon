// app.js - PWA Ana JavaScript Dosyası
// ==================== GLOBAL DEĞİŞKENLER ====================
let ws = null;
let kumesData = null;
let esp32IP = localStorage.getItem('esp32_ip') || '192.168.1.117';
let darkMode = localStorage.getItem('dark_mode') === 'true';
let reconnectTimer = null;

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

// ==================== VERİ İŞLEME ====================
function handleData(data) {
    kumesData = data;
    
    // Özet kartları güncelle
    updateSummaryCards(data);
    
    // Kümes detaylarını güncelle
    updateKumesDetails(data);
}

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
    const runtimeEl = document.getElementById('runtime');
    if (runtimeEl && data.zaman) {
        const hours = Math.floor(data.zaman / 3600);
        const minutes = Math.floor((data.zaman % 3600) / 60);
        runtimeEl.textContent = `${hours}s ${minutes}d`;
    }
}

function updateKumesDetails(data) {
    const container = document.getElementById('kumes-details');
    if (!container || !data.kumesler) return;
    
    container.innerHTML = '';
    
    data.kumesler.forEach(kumes => {
        const card = document.createElement('div');
        card.className = 'detail-card';
        
        if (kumes.alarm) {
            card.style.borderLeft = '4px solid var(--danger)';
        }
        
        card.innerHTML = `
            <div class="detail-header">
                <div class="detail-title">
                    <span class="detail-icon">🐔</span>
                    Kümes #${kumes.id}
                </div>
                ${kumes.alarm ? '<span class="alarm-badge">⚠️ ALARM</span>' : '<span class="status-ok">✅ Normal</span>'}
            </div>
            
            <div class="detail-grid">
                <div class="detail-item">
                    <span class="detail-label">🌡️ Sıcaklık</span>
                    <span class="detail-value">${kumes.sicaklik.toFixed(1)}°C</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">💧 Nem</span>
                    <span class="detail-value">${kumes.nem.toFixed(0)}%</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">💡 LED</span>
                    <span class="detail-value">${kumes.led ? '✅ Açık' : '❌ Kapalı'}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">🌀 Fan</span>
                    <span class="detail-value">${kumes.fan ? '✅ Açık' : '❌ Kapalı'}</span>
                </div>
            </div>
            
            ${kumes.alarm && kumes.mesaj ? `
            <div class="alarm-message">
                ⚠️ ${kumes.mesaj}
            </div>
            ` : ''}
        `;
        
        container.appendChild(card);
    });
}

// ==================== BAĞLANTI DURUMU ====================
function updateConnectionStatus(connected) {
    const badge = document.getElementById('status-badge');
    if (!badge) return;
    
    if (connected) {
        badge.className = 'status-badge connected';
        badge.textContent = '🟢 Bağlı';
    } else {
        badge.className = 'status-badge disconnected';
        badge.textContent = '🔴 Bağlantı Yok';
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
        showNotification(`📤 ${command}`);
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
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
    });
    
    const targetPage = document.getElementById(`page-${pageName}`);
    if (targetPage) {
        targetPage.classList.add('active');
    }
    
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    
    const clickedNav = event ? event.target.closest('.nav-item') : null;
    if (clickedNav) {
        clickedNav.classList.add('active');
    }
}

// ==================== DARK MODE ====================
function toggleDarkMode() {
    darkMode = !darkMode;
    document.body.classList.toggle('dark-mode', darkMode);
    localStorage.setItem('dark_mode', darkMode);
    
    const toggle = document.getElementById('dark-mode-toggle');
    if (toggle) toggle.checked = darkMode;
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

.detail-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
}

.detail-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 1.1em;
    font-weight: 600;
}

.alarm-badge {
    background: var(--danger);
    color: white;
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 0.8em;
}

.status-ok {
    background: var(--success);
    color: white;
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 0.8em;
}

.detail-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
    margin-bottom: 12px;
}

.detail-item {
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.detail-label {
    font-size: 0.85em;
    color: var(--text-secondary);
}

.detail-value {
    font-size: 1.1em;
    font-weight: 600;
    color: var(--text-primary);
}

.alarm-message {
    background: rgba(244, 67, 54, 0.1);
    color: var(--danger);
    padding: 10px;
    border-radius: 8px;
    font-size: 0.9em;
    margin-top: 10px;
}
</style>
`;

document.head.insertAdjacentHTML('beforeend', toastStyles);

// ==================== SAYFA YÜKLENDİĞİNDE ====================
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Kümes Otomasyon PWA başlatılıyor...');
    
    // Dark mode
    if (darkMode) {
        document.body.classList.add('dark-mode');
    }
    
    // WebSocket bağlan
    connectWebSocket();
    
    // Service Worker
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('sw.js')
            .then(() => console.log('✅ Service Worker kaydedildi'))
            .catch(err => console.error('❌ SW hatası:', err));
    }
    
    console.log('✅ Uygulama hazır!');
});

console.log('✅ app.js yüklendi');