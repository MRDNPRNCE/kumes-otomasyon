import os

# =============================================================================
# 1. TEMEL AYARLAR
# =============================================================================
APP_TITLE = "Kümes Otomasyon Sistemi"
DEFAULT_ESP_IP = "127.0.0.1"
WS_PORT = 81
KUMLER_COUNT = 3
DEFAULT_KUMES_NAMES = ["Kümes 1", "Kümes 2", "Kümes 3"]
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"

# =============================================================================
# 2. VERİTABANI VE YOLLAR
# =============================================================================
DB_NAME = "kumes_verileri.db"
DB_PATH = os.path.join(os.getcwd(), DB_NAME)
BACKUP_DIR = os.path.join(os.getcwd(), "backups")

if not os.path.exists(BACKUP_DIR):
    os.makedirs(BACKUP_DIR)

# =============================================================================
# 3. RENK VE GÖRSEL TASARIM
# =============================================================================
class Colors:
    """Renk paleti tanımları"""
    PRIMARY   = "#667eea"
    SUCCESS   = "#48bb78"
    WARNING   = "#f6ad55"  # Eklendi
    ERROR     = "#f56565"
    BORDER    = "#cbd5e0"
    TEXT_DARK = "#2d3748"

# Alias tanımlamaları (Sınıf özelliklerine güvenli referans)
CARD_BORDER_COLOR = Colors.BORDER     # Düzeltildi: Colors.CARD_BORDER yerine BORDER
ALARM_COLOR       = Colors.ERROR      # Colors.ERROR
SUCCESS_COLOR     = Colors.SUCCESS    # Colors.SUCCESS
WARNING_COLOR     = Colors.WARNING    # Düzeltildi: Sınıfa WARNING eklendi
NORMAL_COLOR      = Colors.TEXT_DARK

# =============================================================================
# 4. TEKNİK KONFİGÜRASYONLAR
# =============================================================================
class WSCommands:
    """WebSocket komut setleri"""
    FAN_ON  = "FAN:1"
    FAN_OFF = "FAN:0"

SENSOR_LIMITS = {
    "temp": (15, 35),
    "hum":  (40, 70)
}

# 2026 Geliştirme Özellikleri (Var olduğunu varsaydığımız kısımlar)
class Themes:
    DARK, LIGHT, AUTO = "dark", "light", "auto"
    DEFAULT = DARK

THEME_COLORS = {} # Detaylar projenize göre eklenebilir
class GraphSettings:
    MAX_DATA_POINTS = 300
    UPDATE_INTERVAL_MS = 2000

# UI Davranış Ayarları
ENABLE_SYSTEM_TRAY = True
TRAY_TOOLTIP_TEMPLATE = "{app_title} - Bağlantı: {status}"
NOTIFICATION_DURATION = 8000
ENABLE_SOUND_ALERTS = True
SOUND_CRITICAL, SOUND_WARNING, SOUND_INFO = "c.wav", "w.wav", "i.wav"
ENABLE_RESPONSIVE_LAYOUT = True
MINIMUM_CARD_WIDTH, MAXIMUM_CARD_WIDTH = 320, 450
AUTO_RESIZE_CARDS = True
ENABLE_UI_LOG_TAB, LOG_DISPLAY_MAX_LINES = True, 500
LOG_AUTO_SCROLL, LOG_COLORIZE = True, True
BUTTON_ANIMATION_DURATION, LED_BLINK_INTERVAL = 150, 800
PROGRESS_ANIMATION_ENABLED = True
# Kümes bilgileri (dinamik, değiştirilebilir)
KUMES_BILGILERI = {
    1: {
        "ad": "Ana Kümes",
        "tavuk_sayisi": 120,
        "gunluk": 180
    },
    2: {
        "ad": "Yavru Kümes",
        "tavuk_sayisi": 85,
        "gunluk": 45
    },
    3: {
        "ad": "Misafir Kümes",
        "tavuk_sayisi": 50,
        "gunluk": 90
    }
}
# =============================================================================
# 5. EXPORT (__all__)
# =============================================================================
__all__ = [ 
    'APP_TITLE', 'DEFAULT_ESP_IP', 'WS_PORT', 'DB_NAME', 'DB_PATH', 'BACKUP_DIR',
    'KUMLER_COUNT', 'DEFAULT_KUMES_NAMES', 'TIMESTAMP_FORMAT',
    'Colors', 'CARD_BORDER_COLOR', 'ALARM_COLOR', 'SUCCESS_COLOR', 'WARNING_COLOR', 'NORMAL_COLOR',
    'WSCommands', 'SENSOR_LIMITS', 'Themes', 'THEME_COLORS', 'GraphSettings',
    'ENABLE_SYSTEM_TRAY', 'TRAY_TOOLTIP_TEMPLATE', 'NOTIFICATION_DURATION',
    'ENABLE_SOUND_ALERTS', 'SOUND_CRITICAL', 'SOUND_WARNING', 'SOUND_INFO',
    'ENABLE_RESPONSIVE_LAYOUT', 'MINIMUM_CARD_WIDTH', 'MAXIMUM_CARD_WIDTH',
    'AUTO_RESIZE_CARDS', 'ENABLE_UI_LOG_TAB', 'LOG_DISPLAY_MAX_LINES', 
    'LOG_AUTO_SCROLL', 'LOG_COLORIZE', 'BUTTON_ANIMATION_DURATION', 
    'LED_BLINK_INTERVAL', 'PROGRESS_ANIMATION_ENABLED', 'KUMES_BILGILERI',
]