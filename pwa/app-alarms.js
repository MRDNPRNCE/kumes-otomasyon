// app-alarms.js - PWA Alarm Sistemi
// app.js'e eklenecek veya entegre edilecek

// ==================== ALARM YÖNETİMİ ====================
let alarmList = [];
let alarmHistory = [];
let unreadAlarmCount = 0;

// ==================== ALARM SAYFA HTML'İ ====================
function createAlarmsPage() {
    const alarmsHTML = `
    <div id="page-alarms" class="page">
        <div class="container">
            <!-- Alarm Özeti -->
            <div class="alarm-summary">
                <div class="summary-item">
                    <div class="summary-value" id="total-alarms">0</div>
                    <div class="summary-label">Toplam Alarm</div>
                </div>
                <div class="summary-item">
                    <div class="summary-value active-alarm" id="active-alarms">0</div>
                    <div class="summary-label">Aktif Alarm</div>
                </div>
                <div class="summary-item">
                    <div class="summary-value" id="resolved-alarms">0</div>
                    <div class="summary-label">Çözülmüş</div>
                </div>
            </div>
            
            <!-- Filtre Butonları -->
            <div class="alarm-filters">
                <button class="filter-btn active" onclick="filterAlarms('all')">
                    🔔 Tümü
                </button>
                <button class="filter-btn" onclick="filterAlarms('active')">
                    ⚠️ Aktif
                </button>
                <button class="filter-btn" onclick="filterAlarms('resolved')">
                    ✅ Çözülmüş
                </button>
                <button class="filter-btn" onclick="filterAlarms('critical')">
                    🔴 Kritik
                </button>
            </div>
            
            <!-- Alarm Listesi -->
            <div id="alarm-list-container">
                <div id="alarm-empty" class="empty-state">
                    <div class="empty-icon">🎉</div>
                    <div class="empty-title">Aktif Alarm Yok!</div>
                    <div class="empty-text">Tüm sistemler normal çalışıyor.</div>
                </div>
            </div>
            
            <!-- Aksiyon Butonları -->
            <div class="alarm-actions">
                <button class="btn btn-primary" onclick="clearAllAlarms()">
                    🗑️ Tüm Alarmları Temizle
                </button>
                <button class="btn btn-primary" onclick="exportAlarms()" style="background: var(--success);">
                    📥 Excel'e Aktar
                </button>
            </div>
        </div>
    </div>
    `;
    
    // Page-settings'ten sonra ekle
    const settingsPage = document.getElementById('page-settings');
    settingsPage.insertAdjacentHTML('afterend', alarmsHTML);
    
    // Bottom nav'a alarm sekmesi ekle
    const bottomNav = document.querySelector('.bottom-nav');
    const controlItem = bottomNav.children[1]; // Kontrol sekmesi
    
    const alarmNavItem = document.createElement('div');
    alarmNavItem.className = 'nav-item';
    alarmNavItem.onclick = () => showPage('alarms');
    alarmNavItem.innerHTML = `
        <div class="nav-icon">
            🔔
            <span class="alarm-badge" id="alarm-badge">0</span>
        </div>
        <div>Alarmlar</div>
    `;
    
    // Kontrol ile Ayarlar arasına ekle
    bottomNav.insertBefore(alarmNavItem, bottomNav.children[2]);
}

// ==================== ALARM SAYFA CSS ====================
const alarmStyles = `
<style>
/* Alarm Özet Kartları */
.alarm-summary {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    margin-bottom: 20px;
}

.alarm-summary .summary-item {
    background: var(--card-bg);
    padding: 20px;
    border-radius: var(--border-radius);
    text-align: center;
    box-shadow: var(--shadow);
}

.alarm-summary .summary-value {
    font-size: 2em;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 8px;
}

.alarm-summary .summary-value.active-alarm {
    color: var(--danger);
}

.alarm-summary .summary-label {
    font-size: 0.85em;
    color: var(--text-secondary);
}

/* Filtre Butonları */
.alarm-filters {
    display: flex;
    gap: 8px;
    margin-bottom: 16px;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
}

.filter-btn {
    padding: 10px 20px;
    background: var(--card-bg);
    border: 2px solid rgba(0,0,0,0.1);
    border-radius: 20px;
    font-size: 0.9em;
    font-weight: 600;
    cursor: pointer;
    white-space: nowrap;
    transition: all 0.3s;
    color: var(--text-primary);
}

.filter-btn.active {
    background: var(--primary);
    color: white;
    border-color: var(--primary);
}

.filter-btn:active {
    transform: scale(0.95);
}

/* Alarm Kartı */
.alarm-card {
    background: var(--card-bg);
    border-radius: var(--border-radius);
    padding: 16px;
    margin-bottom: 12px;
    box-shadow: var(--shadow);
    border-left: 4px solid var(--danger);
    animation: slideIn 0.3s;
}

.alarm-card.resolved {
    border-left-color: var(--success);
    opacity: 0.7;
}

.alarm-card.warning {
    border-left-color: var(--warning);
}

.alarm-card.info {
    border-left-color: var(--info);
}

.alarm-header {
    display: flex;
    justify-content: space-between;
    align-items: start;
    margin-bottom: 12px;
}

.alarm-title {
    flex: 1;
}

.alarm-icon {
    font-size: 1.5em;
    margin-right: 10px;
}

.alarm-kumes {
    font-size: 1.1em;
    font-weight: 700;
    color: var(--text-primary);
}

.alarm-message {
    font-size: 0.95em;
    color: var(--text-secondary);
    margin-top: 4px;
}

.alarm-meta {
    display: flex;
    gap: 15px;
    font-size: 0.85em;
    color: var(--text-secondary);
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px solid rgba(0,0,0,0.05);
}

.alarm-meta-item {
    display: flex;
    align-items: center;
    gap: 4px;
}

.alarm-priority {
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 0.75em;
    font-weight: 600;
}

.alarm-priority.critical {
    background: rgba(244, 67, 54, 0.15);
    color: var(--danger);
}

.alarm-priority.high {
    background: rgba(255, 152, 0, 0.15);
    color: var(--warning);
}

.alarm-priority.medium {
    background: rgba(33, 150, 243, 0.15);
    color: var(--info);
}

.alarm-priority.low {
    background: rgba(76, 175, 80, 0.15);
    color: var(--success);
}

.alarm-actions-inline {
    display: flex;
    gap: 8px;
    margin-top: 12px;
}

.alarm-btn {
    padding: 8px 16px;
    border: none;
    border-radius: 8px;
    font-size: 0.85em;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s;
}

.alarm-btn.resolve {
    background: var(--success);
    color: white;
}

.alarm-btn.delete {
    background: var(--danger);
    color: white;
}

.alarm-btn:active {
    transform: scale(0.95);
}

/* Empty State */
.empty-state {
    text-align: center;
    padding: 60px 20px;
}

.empty-icon {
    font-size: 4em;
    margin-bottom: 20px;
}

.empty-title {
    font-size: 1.3em;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 10px;
}

.empty-text {
    color: var(--text-secondary);
}

/* Alarm Badge */
.alarm-badge {
    position: absolute;
    top: 0;
    right: -8px;
    background: var(--danger);
    color: white;
    font-size: 0.6em;
    padding: 2px 6px;
    border-radius: 10px;
    font-weight: 700;
    min-width: 18px;
    display: none;
}

.alarm-badge.show {
    display: block;
    animation: pulse 2s infinite;
}

/* Alarm Actions */
.alarm-actions {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    margin-top: 20px;
}

/* Sıralama */
.alarm-sort {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;
    font-size: 0.9em;
    color: var(--text-secondary);
}

.sort-select {
    padding: 6px 12px;
    border: 2px solid rgba(0,0,0,0.1);
    border-radius: 8px;
    background: var(--card-bg);
    color: var(--text-primary);
}

/* Loading */
.alarm-loading {
    text-align: center;
    padding: 40px;
    color: var(--text-secondary);
}

.spinner-small {
    width: 30px;
    height: 30px;
    border: 3px solid rgba(0,0,0,0.1);
    border-top-color: var(--primary);
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 0 auto 15px;
}
</style>
`;

document.head.insertAdjacentHTML('beforeend', alarmStyles);

// ==================== ALARM FONKSİYONLARI ====================
function addAlarm(alarm) {
    // Alarm objesi: {id, kumes, message, priority, type, timestamp, resolved}
    const alarmObj = {
        id: Date.now(),
        kumes: alarm.kumes || 1,
        message: alarm.message || 'Bilinmeyen alarm',
        priority: alarm.priority || 'medium', // critical, high, medium, low
        type: alarm.type || 'error', // error, warning, info
        timestamp: alarm.timestamp || new Date().toISOString(),
        resolved: false
    };
    
    // Listeye ekle
    alarmList.unshift(alarmObj);
    alarmHistory.push(alarmObj);
    
    // Okunmamış sayacı artır
    unreadAlarmCount++;
    
    // UI güncelle
    updateAlarmUI();
    updateAlarmBadge();
    
    // Bildirim göster
    showAlarmNotification(alarmObj);
    
    // Haptic feedback
    if (typeof hapticFeedback === 'function') {
        hapticFeedback('error');
    }
    
    console.log('🚨 Yeni alarm:', alarmObj);
}

function resolveAlarm(alarmId) {
    const alarm = alarmList.find(a => a.id === alarmId);
    if (alarm) {
        alarm.resolved = true;
        alarm.resolvedAt = new Date().toISOString();
        
        updateAlarmUI();
        updateAlarmBadge();
        showNotification('✅ Alarm çözüldü');
        
        if (typeof hapticFeedback === 'function') {
            hapticFeedback('success');
        }
    }
}

function deleteAlarm(alarmId) {
    alarmList = alarmList.filter(a => a.id !== alarmId);
    updateAlarmUI();
    updateAlarmBadge();
    showNotification('🗑️ Alarm silindi');
    
    if (typeof hapticFeedback === 'function') {
        hapticFeedback('light');
    }
}

function clearAllAlarms() {
    if (confirm('Tüm alarmları temizlemek istediğinize emin misiniz?')) {
        const activeCount = alarmList.filter(a => !a.resolved).length;
        
        alarmList = [];
        unreadAlarmCount = 0;
        
        updateAlarmUI();
        updateAlarmBadge();
        showNotification(`✅ ${activeCount} alarm temizlendi`);
        
        if (typeof hapticFeedback === 'function') {
            hapticFeedback('success');
        }
    }
}

function updateAlarmUI() {
    const container = document.getElementById('alarm-list-container');
    if (!container) return;
    
    // Aktif filtreyi al
    const activeFilter = document.querySelector('.filter-btn.active');
    const filter = activeFilter ? activeFilter.textContent.trim().split(' ')[1].toLowerCase() : 'tümü';
    
    // Filtrelenmiş alarmlar
    let filteredAlarms = alarmList;
    
    if (filter === 'aktif') {
        filteredAlarms = alarmList.filter(a => !a.resolved);
    } else if (filter === 'çözülmüş') {
        filteredAlarms = alarmList.filter(a => a.resolved);
    } else if (filter === 'kritik') {
        filteredAlarms = alarmList.filter(a => a.priority === 'critical');
    }
    
    // Boşsa empty state göster
    if (filteredAlarms.length === 0) {
        container.innerHTML = `
            <div id="alarm-empty" class="empty-state">
                <div class="empty-icon">${filter === 'aktif' ? '🎉' : '📭'}</div>
                <div class="empty-title">${filter === 'aktif' ? 'Aktif Alarm Yok!' : 'Alarm Bulunamadı'}</div>
                <div class="empty-text">${filter === 'aktif' ? 'Tüm sistemler normal çalışıyor.' : 'Bu filtrede gösterilecek alarm yok.'}</div>
            </div>
        `;
        return;
    }
    
    // Alarm kartlarını oluştur
    let html = '<div class="alarm-sort">';
    html += '<span>📊 Sıralama:</span>';
    html += '<select class="sort-select" onchange="sortAlarms(this.value)">';
    html += '<option value="newest">En Yeni</option>';
    html += '<option value="oldest">En Eski</option>';
    html += '<option value="priority">Öncelik</option>';
    html += '<option value="kumes">Kümes</option>';
    html += '</select>';
    html += '</div>';
    
    filteredAlarms.forEach(alarm => {
        const icon = getAlarmIcon(alarm.type);
        const priorityClass = alarm.priority;
        const resolvedClass = alarm.resolved ? 'resolved' : '';
        const typeClass = alarm.type;
        
        html += `
        <div class="alarm-card ${resolvedClass} ${typeClass}">
            <div class="alarm-header">
                <div class="alarm-title">
                    <span class="alarm-icon">${icon}</span>
                    <span class="alarm-kumes">Kümes #${alarm.kumes}</span>
                    <div class="alarm-message">${alarm.message}</div>
                </div>
                <div class="alarm-priority ${priorityClass}">
                    ${getPriorityText(alarm.priority)}
                </div>
            </div>
            
            <div class="alarm-meta">
                <div class="alarm-meta-item">
                    🕐 ${formatAlarmTime(alarm.timestamp)}
                </div>
                ${alarm.resolved ? `
                <div class="alarm-meta-item">
                    ✅ Çözüldü
                </div>
                ` : ''}
            </div>
            
            ${!alarm.resolved ? `
            <div class="alarm-actions-inline">
                <button class="alarm-btn resolve" onclick="resolveAlarm(${alarm.id})">
                    ✅ Çöz
                </button>
                <button class="alarm-btn delete" onclick="deleteAlarm(${alarm.id})">
                    🗑️ Sil
                </button>
            </div>
            ` : ''}
        </div>
        `;
    });
    
    container.innerHTML = html;
    
    // Özet güncelle
    updateAlarmSummary();
}

function updateAlarmSummary() {
    const totalAlarms = alarmList.length;
    const activeAlarms = alarmList.filter(a => !a.resolved).length;
    const resolvedAlarms = alarmList.filter(a => a.resolved).length;
    
    const totalEl = document.getElementById('total-alarms');
    const activeEl = document.getElementById('active-alarms');
    const resolvedEl = document.getElementById('resolved-alarms');
    
    if (totalEl) totalEl.textContent = totalAlarms;
    if (activeEl) activeEl.textContent = activeAlarms;
    if (resolvedEl) resolvedEl.textContent = resolvedAlarms;
}

function updateAlarmBadge() {
    const badge = document.getElementById('alarm-badge');
    if (!badge) return;
    
    const activeCount = alarmList.filter(a => !a.resolved).length;
    
    if (activeCount > 0) {
        badge.textContent = activeCount > 99 ? '99+' : activeCount;
        badge.classList.add('show');
    } else {
        badge.classList.remove('show');
    }
}

function filterAlarms(filter) {
    // Aktif buton stilini değiştir
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // UI güncelle
    updateAlarmUI();
    
    if (typeof hapticFeedback === 'function') {
        hapticFeedback('light');
    }
}

function sortAlarms(sortBy) {
    switch(sortBy) {
        case 'newest':
            alarmList.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
            break;
        case 'oldest':
            alarmList.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
            break;
        case 'priority':
            const priorityOrder = { critical: 0, high: 1, medium: 2, low: 3 };
            alarmList.sort((a, b) => priorityOrder[a.priority] - priorityOrder[b.priority]);
            break;
        case 'kumes':
            alarmList.sort((a, b) => a.kumes - b.kumes);
            break;
    }
    
    updateAlarmUI();
}

function showAlarmNotification(alarm) {
    const icon = getAlarmIcon(alarm.type);
    const message = `${icon} Kümes #${alarm.kumes}: ${alarm.message}`;
    
    // PWA bildirimi
    if (typeof showNotification === 'function') {
        showNotification(message);
    }
    
    // Browser notification
    if ('Notification' in window && Notification.permission === 'granted') {
        new Notification('🚨 Kümes Alarm', {
            body: message,
            icon: '/icon-192.png',
            badge: '/icon-192.png',
            vibrate: [200, 100, 200]
        });
    }
}

function exportAlarms() {
    // CSV formatında dışa aktar
    let csv = 'Kümes,Mesaj,Öncelik,Durum,Zaman\n';
    
    alarmList.forEach(alarm => {
        csv += `${alarm.kumes},`;
        csv += `"${alarm.message}",`;
        csv += `${getPriorityText(alarm.priority)},`;
        csv += `${alarm.resolved ? 'Çözüldü' : 'Aktif'},`;
        csv += `${formatAlarmTime(alarm.timestamp)}\n`;
    });
    
    // İndir
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', `kumes_alarmlar_${Date.now()}.csv`);
    link.style.visibility = 'hidden';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    showNotification('📥 Alarmlar Excel\'e aktarıldı');
    
    if (typeof hapticFeedback === 'function') {
        hapticFeedback('success');
    }
}

// ==================== YARDIMCI FONKSİYONLAR ====================
function getAlarmIcon(type) {
    switch(type) {
        case 'error': return '🔴';
        case 'warning': return '⚠️';
        case 'info': return 'ℹ️';
        default: return '🔔';
    }
}

function getPriorityText(priority) {
    switch(priority) {
        case 'critical': return 'KRİTİK';
        case 'high': return 'Yüksek';
        case 'medium': return 'Orta';
        case 'low': return 'Düşük';
        default: return 'Orta';
    }
}

function formatAlarmTime(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;
    
    // Dakika cinsinden
    const minutes = Math.floor(diff / 60000);
    
    if (minutes < 1) return 'Az önce';
    if (minutes < 60) return `${minutes} dakika önce`;
    
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours} saat önce`;
    
    const days = Math.floor(hours / 24);
    if (days < 7) return `${days} gün önce`;
    
    // Tam tarih
    return date.toLocaleDateString('tr-TR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// ==================== VERİ İŞLEME ENTEGRASYONU ====================
// handleData fonksiyonunu güncelle (app.js'teki)
function handleDataWithAlarms(data) {
    try {
        const json = (typeof data === 'string') ? JSON.parse(data) : data;
        kumesData = json;
        
        // Özet kartları güncelle
        updateSummaryCards(json);
        
        // Kümes detaylarını güncelle
        updateKumesDetails(json);
        
        // ALARM KONTROLÜ - YENİ!
        if (json.kumesler) {
            json.kumesler.forEach(kumes => {
                if (kumes.alarm && kumes.mesaj) {
                    // Bu alarm zaten var mı kontrol et
                    const existingAlarm = alarmList.find(a => 
                        a.kumes === kumes.id && 
                        a.message === kumes.mesaj && 
                        !a.resolved
                    );
                    
                    // Yoksa ekle
                    if (!existingAlarm) {
                        const priority = getPriorityFromMessage(kumes.mesaj);
                        const type = getTypeFromMessage(kumes.mesaj);
                        
                        addAlarm({
                            kumes: kumes.id,
                            message: kumes.mesaj,
                            priority: priority,
                            type: type
                        });
                    }
                }
            });
        }
        
    } catch (error) {
        console.error('❌ JSON parse hatası:', error);
    }
}

function getPriorityFromMessage(message) {
    message = message.toLowerCase();
    
    if (message.includes('kritik') || message.includes('acil')) {
        return 'critical';
    } else if (message.includes('yüksek') || message.includes('tehlike')) {
        return 'high';
    } else if (message.includes('düşük') || message.includes('uyarı')) {
        return 'medium';
    } else {
        return 'low';
    }
}

function getTypeFromMessage(message) {
    message = message.toLowerCase();
    
    if (message.includes('hata') || message.includes('arıza')) {
        return 'error';
    } else if (message.includes('uyarı') || message.includes('dikkat')) {
        return 'warning';
    } else {
        return 'info';
    }
}

// ==================== SAYFA YÜKLENDIĞINDE ====================
document.addEventListener('DOMContentLoaded', () => {
    // Alarm sayfasını oluştur
    createAlarmsPage();
    
    // Test alarmları (geliştirme için)
    if (localStorage.getItem('debug_mode') === 'true') {
        addAlarm({
            kumes: 1,
            message: 'Yüksek sıcaklık tespit edildi',
            priority: 'critical',
            type: 'error'
        });
        
        addAlarm({
            kumes: 2,
            message: 'Su seviyesi düşük',
            priority: 'high',
            type: 'warning'
        });
        
        addAlarm({
            kumes: 3,
            message: 'Nem seviyesi normal',
            priority: 'low',
            type: 'info'
        });
    }
    
    // Bildirim izni iste
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }
});

// handleData'yı değiştir
if (typeof handleData !== 'undefined') {
    const originalHandleData = handleData;
    handleData = function(data) {
        originalHandleData(data);
        handleDataWithAlarms(data);
    };
}

console.log('✅ Alarm sistemi yüklendi');