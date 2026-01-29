// app-enhanced.js - Geliştirilmiş PWA özellikleri
// Önceki app.js üzerine eklenecek yeni özellikler

// ==================== HAPTIC FEEDBACK (VİBRASYON) ====================
function hapticFeedback(type = 'light') {
    if (!navigator.vibrate) return;
    
    switch(type) {
        case 'light':
            navigator.vibrate(10);
            break;
        case 'medium':
            navigator.vibrate(20);
            break;
        case 'heavy':
            navigator.vibrate(50);
            break;
        case 'success':
            navigator.vibrate([10, 50, 10]);
            break;
        case 'error':
            navigator.vibrate([50, 100, 50]);
            break;
        case 'double':
            navigator.vibrate([20, 50, 20]);
            break;
    }
}

// ==================== PULL-TO-REFRESH ====================
let startY = 0;
let pulling = false;
let pullDistance = 0;
const pullThreshold = 100;

document.addEventListener('touchstart', (e) => {
    if (window.scrollY === 0) {
        startY = e.touches[0].clientY;
        pulling = true;
    }
});

document.addEventListener('touchmove', (e) => {
    if (!pulling) return;
    
    const currentY = e.touches[0].clientY;
    pullDistance = currentY - startY;
    
    if (pullDistance > 0 && pullDistance < pullThreshold * 2) {
        // Görsel feedback
        const header = document.querySelector('.header');
        if (header) {
            header.style.transform = `translateY(${pullDistance / 3}px)`;
            header.style.transition = 'none';
        }
    }
});

document.addEventListener('touchend', () => {
    if (!pulling) return;
    
    const header = document.querySelector('.header');
    
    if (pullDistance > pullThreshold) {
        // Yenile
        hapticFeedback('success');
        showNotification('🔄 Yenileniyor...');
        
        if (ws && ws.readyState === WebSocket.OPEN) {
            sendCmd('STATUS');
        } else {
            connectWebSocket();
        }
    }
    
    // Reset
    if (header) {
        header.style.transform = '';
        header.style.transition = 'transform 0.3s';
    }
    
    pulling = false;
    pullDistance = 0;
});

// ==================== LONG PRESS (UZUN BASMA) ====================
function addLongPress(element, callback) {
    let pressTimer;
    
    element.addEventListener('touchstart', (e) => {
        pressTimer = setTimeout(() => {
            hapticFeedback('heavy');
            callback(e);
        }, 500); // 500ms
    });
    
    element.addEventListener('touchend', () => {
        clearTimeout(pressTimer);
    });
    
    element.addEventListener('touchmove', () => {
        clearTimeout(pressTimer);
    });
}

// Örnek kullanım: Kümes kartlarına long press ekle
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
        const kumesCards = document.querySelectorAll('.detail-card');
        kumesCards.forEach((card, index) => {
            addLongPress(card, () => {
                showNotification(`🐔 Kümes #${index + 1} detayları`);
                // Detay modal'ı göster veya başka aksiyon
            });
        });
    }, 1000);
});

// ==================== NETWORK STATUS DETECTION ====================
window.addEventListener('online', () => {
    showNotification('✅ İnternet bağlantısı kuruldu');
    hapticFeedback('success');
    
    // WebSocket'e tekrar bağlan
    if (!ws || ws.readyState !== WebSocket.OPEN) {
        connectWebSocket();
    }
});

window.addEventListener('offline', () => {
    showNotification('⚠️ İnternet bağlantısı kesildi');
    hapticFeedback('error');
});

// ==================== BATTERY STATUS ====================
if ('getBattery' in navigator) {
    navigator.getBattery().then(battery => {
        function updateBatteryStatus() {
            const level = Math.round(battery.level * 100);
            const charging = battery.charging;
            
            console.log(`🔋 Batarya: ${level}% ${charging ? '(Şarj oluyor)' : ''}`);
            
            // Düşük batarya uyarısı
            if (level < 20 && !charging) {
                showNotification(`⚠️ Batarya düşük: ${level}%`);
            }
        }
        
        updateBatteryStatus();
        
        battery.addEventListener('levelchange', updateBatteryStatus);
        battery.addEventListener('chargingchange', updateBatteryStatus);
    });
}

// ==================== SCREEN WAKE LOCK (Ekranı Açık Tut) ====================
let wakeLock = null;

async function requestWakeLock() {
    if ('wakeLock' in navigator) {
        try {
            wakeLock = await navigator.wakeLock.request('screen');
            console.log('✅ Ekran kilidi aktif');
            
            wakeLock.addEventListener('release', () => {
                console.log('⚠️ Ekran kilidi kaldırıldı');
            });
        } catch (err) {
            console.error('❌ Ekran kilidi hatası:', err);
        }
    }
}

async function releaseWakeLock() {
    if (wakeLock !== null) {
        await wakeLock.release();
        wakeLock = null;
    }
}

// Uygulama açıldığında ekranı açık tut
document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') {
        requestWakeLock();
    } else {
        releaseWakeLock();
    }
});

// ==================== SHARE API (Paylaşma) ====================
async function shareData(title, text, url) {
    if (!navigator.share) {
        console.log('❌ Share API desteklenmiyor');
        return;
    }
    
    try {
        await navigator.share({
            title: title,
            text: text,
            url: url
        });
        console.log('✅ Paylaşıldı');
        hapticFeedback('success');
    } catch (err) {
        console.log('❌ Paylaşım iptal edildi');
    }
}

// Örnek kullanım
function shareKumesStatus() {
    if (kumesData.kumesler) {
        const avgTemp = kumesData.kumesler.reduce((sum, k) => sum + k.sicaklik, 0) / kumesData.kumesler.length;
        shareData(
            '🐔 Kümes Durumu',
            `Ortalama Sıcaklık: ${avgTemp.toFixed(1)}°C`,
            window.location.href
        );
    }
}

// ==================== SCREENSHOT (Ekran Görüntüsü) ====================
async function takeScreenshot() {
    try {
        const stream = await navigator.mediaDevices.getDisplayMedia({
            video: { mediaSource: 'screen' }
        });
        
        const video = document.createElement('video');
        video.srcObject = stream;
        video.play();
        
        video.addEventListener('loadedmetadata', () => {
            const canvas = document.createElement('canvas');
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            
            const ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0);
            
            stream.getTracks().forEach(track => track.stop());
            
            canvas.toBlob(blob => {
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `kumes-${Date.now()}.png`;
                a.click();
                
                showNotification('✅ Ekran görüntüsü kaydedildi');
                hapticFeedback('success');
            });
        });
    } catch (err) {
        console.error('❌ Ekran görüntüsü hatası:', err);
    }
}

// ==================== GEOLOCATION (Konum) ====================
function getLocation() {
    if (!navigator.geolocation) {
        showNotification('❌ Konum desteklenmiyor');
        return;
    }
    
    navigator.geolocation.getCurrentPosition(
        position => {
            const lat = position.coords.latitude;
            const lon = position.coords.longitude;
            console.log(`📍 Konum: ${lat}, ${lon}`);
            // Konumu kaydet veya göster
        },
        error => {
            console.error('❌ Konum hatası:', error);
        }
    );
}

// ==================== CLIPBOARD (Kopyalama) ====================
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showNotification('✅ Kopyalandı');
        hapticFeedback('light');
    } catch (err) {
        console.error('❌ Kopyalama hatası:', err);
    }
}

// ESP32 IP'yi kopyalama
function copyESP32IP() {
    copyToClipboard(esp32IP);
}

// ==================== DEVICE ORIENTATION (Cihaz Yönü) ====================
if (window.DeviceOrientationEvent) {
    window.addEventListener('deviceorientation', (event) => {
        const alpha = event.alpha; // Z ekseni (0-360)
        const beta = event.beta;   // X ekseni (-180 to 180)
        const gamma = event.gamma; // Y ekseni (-90 to 90)
        
        // Opsiyonel: Yönelime göre UI değiştir
        // console.log(`Yön: α=${alpha}° β=${beta}° γ=${gamma}°`);
    });
}

// ==================== SMOOTH SCROLL ====================
function smoothScrollTo(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'start' });
        hapticFeedback('light');
    }
}

// ==================== BUTON GELİŞTİRMELERİ ====================
// Tüm butonlara haptic feedback ekle
document.addEventListener('DOMContentLoaded', () => {
    const buttons = document.querySelectorAll('button, .action-btn, .btn');
    buttons.forEach(button => {
        button.addEventListener('click', () => {
            hapticFeedback('light');
        });
    });
});

// ==================== GELIŞMIŞ BİLDİRİM ====================
function showNotificationWithActions(title, message, actions = []) {
    if (!('Notification' in window)) {
        console.log('❌ Notification API desteklenmiyor');
        return;
    }
    
    if (Notification.permission === 'granted') {
        const notification = new Notification(title, {
            body: message,
            icon: '/icon-192.png',
            badge: '/icon-192.png',
            vibrate: [100, 50, 100],
            actions: actions
        });
        
        notification.onclick = () => {
            window.focus();
            notification.close();
        };
    } else if (Notification.permission !== 'denied') {
        Notification.requestPermission().then(permission => {
            if (permission === 'granted') {
                showNotificationWithActions(title, message, actions);
            }
        });
    }
}

// Alarm bildirimi örneği
function notifyAlarm(kumesId, message) {
    showNotificationWithActions(
        `⚠️ Kümes #${kumesId} Alarm`,
        message,
        [
            { action: 'view', title: 'Görüntüle' },
            { action: 'dismiss', title: 'Kapat' }
        ]
    );
    
    hapticFeedback('error');
}

// ==================== DEBUG MODU ====================
let debugMode = localStorage.getItem('debug_mode') === 'true';

function toggleDebugMode() {
    debugMode = !debugMode;
    localStorage.setItem('debug_mode', debugMode);
    showNotification(debugMode ? '🐛 Debug modu açık' : '🐛 Debug modu kapalı');
}

// 5 kez logo'ya tıklayınca debug modu
let logoClickCount = 0;
document.addEventListener('DOMContentLoaded', () => {
    const logo = document.querySelector('.header h1');
    if (logo) {
        logo.addEventListener('click', () => {
            logoClickCount++;
            if (logoClickCount >= 5) {
                toggleDebugMode();
                logoClickCount = 0;
            }
            setTimeout(() => { logoClickCount = 0; }, 2000);
        });
    }
});

// Debug log
function debugLog(...args) {
    if (debugMode) {
        console.log('🐛', ...args);
    }
}

// ==================== EXPORT FONKSİYONLAR ====================
window.kumesApp = {
    hapticFeedback,
    shareKumesStatus,
    takeScreenshot,
    getLocation,
    copyESP32IP,
    smoothScrollTo,
    toggleDebugMode,
    requestWakeLock,
    releaseWakeLock
};

console.log('✅ Gelişmiş PWA özellikleri yüklendi');