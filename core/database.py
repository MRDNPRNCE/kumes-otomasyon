# core/database.py
import sqlite3
import os
import shutil
import threading
from datetime import datetime
import pandas as pd
from .config import DB_PATH, BACKUP_DIR, TIMESTAMP_FORMAT

class DatabaseManager:
    """Tüm veritabanı işlemlerinden sorumlu singleton-like sınıf"""

    def __init__(self):
        db_dir = os.path.dirname(DB_PATH)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        os.makedirs(BACKUP_DIR, exist_ok=True)
        self._lock = threading.Lock()
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self._create_tables()

    def _create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS kumes_veriler (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT (datetime('now','localtime')),
                kumes_id INTEGER,
                sicaklik REAL,
                nem REAL,
                su_seviyesi INTEGER,
                isik_seviyesi INTEGER,
                fan_durumu INTEGER,
                led_durumu INTEGER,
                alarm INTEGER,
                alarm_mesaj TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS komut_gecmisi (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT (datetime('now','localtime')),
                komut TEXT,
                kaynak TEXT,
                sonuc TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alarm_gecmisi (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT (datetime('now','localtime')),
                kumes_id INTEGER,
                mesaj TEXT,
                cozuldu INTEGER DEFAULT 0
            )
        ''')
        self.conn.commit()

    def save_sensor_data(self, kumes_data: dict):
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO kumes_veriler (
                    kumes_id, sicaklik, nem, su_seviyesi, isik_seviyesi,
                    fan_durumu, led_durumu, alarm, alarm_mesaj
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                kumes_data.get('id'),
                kumes_data.get('sicaklik'),
                kumes_data.get('nem'),
                kumes_data.get('su'),
                kumes_data.get('isik'),
                int(kumes_data.get('fan', False)),
                int(kumes_data.get('led', False)),
                int(kumes_data.get('alarm', False)),
                kumes_data.get('mesaj', '')
            ))
            self.conn.commit()

    def save_command(self, command: str, source: str = "UI", result: str = "Gönderildi"):
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO komut_gecmisi (komut, kaynak, sonuc)
                VALUES (?, ?, ?)
            ''', (command, source, result))
            self.conn.commit()

    def save_alarm(self, kumes_id: int, message: str):
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO alarm_gecmisi (kumes_id, mesaj)
                VALUES (?, ?)
            ''', (kumes_id, message))
            self.conn.commit()

    def get_all_sensor_data(self) -> pd.DataFrame:
        with self._lock:
            return pd.read_sql_query("SELECT * FROM kumes_veriler ORDER BY timestamp DESC", self.conn)

    def backup(self) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(BACKUP_DIR, f"kumes_{timestamp}.db")
        shutil.copy(DB_PATH, backup_path)
        return backup_path

    def close(self):
        self.conn.close()