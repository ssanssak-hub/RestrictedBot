# config/settings.py
import os
from typing import Dict, Any
import yaml
from pathlib import Path

class Settings:
    """تنظیمات اصلی ربات"""
    
    def __init__(self):
        # مسیرهای اصلی
        self.BASE_DIR = Path(__file__).parent.parent
        self.DATA_DIR = self.BASE_DIR / "data"
        self.SESSIONS_DIR = self.DATA_DIR / "sessions"
        self.DOWNLOADS_DIR = self.DATA_DIR / "downloads"
        self.LOGS_DIR = self.BASE_DIR / "logs"
        
        # ایجاد پوشه‌ها
        self._create_directories()
        
        # تنظیمات API
        self.API_ID = int(os.getenv("API_ID", "29526323"))
        self.API_HASH = os.getenv("API_HASH", "d2cba6d5c5a9b6b7c8d9e0f1a2b3c4d5")
        self.BOT_TOKEN = os.getenv("BOT_TOKEN", "")
        
        # ادمین‌ها
        self.ADMIN_IDS = [int(id.strip()) for id in os.getenv("ADMIN_IDS", "").split(",") if id.strip()]
        
        # محدودیت‌ها
        self.MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB
        self.MAX_CONCURRENT_DOWNLOADS = 3
        self.DOWNLOAD_SPEED_LIMIT = 50 * 1024 * 1024  # 50 MB/s
        self.UPLOAD_SPEED_LIMIT = 20 * 1024 * 1024   # 20 MB/s
        
        # تنظیمات امنیتی
        self.SESSION_ENCRYPTION_KEY = os.getenv("SESSION_ENCRYPTION_KEY", self._generate_encryption_key())
        self.SESSION_TIMEOUT = 3600 * 24 * 7  # 7 روز
        
        # رفتار انسانی
        self.HUMAN_DELAY_MIN = 0.5  # ثانیه
        self.HUMAN_DELAY_MAX = 2.0  # ثانیه
        self.TYPING_DELAY = 0.1     # ثانیه
        
    def _create_directories(self):
        """ایجاد پوشه‌های مورد نیاز"""
        directories = [
            self.DATA_DIR,
            self.SESSIONS_DIR,
            self.DOWNLOADS_DIR,
            self.LOGS_DIR
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _generate_encryption_key(self) -> str:
        """تولید کلید رمزنگاری"""
        import secrets
        return secrets.token_urlsafe(32)
    
    def to_dict(self) -> Dict[str, Any]:
        """تبدیل به دیکشنری"""
        return {
            'api_id': self.API_ID,
            'api_hash': self.API_HASH,
            'admin_ids': self.ADMIN_IDS,
            'max_file_size': self.MAX_FILE_SIZE,
            'max_concurrent_downloads': self.MAX_CONCURRENT_DOWNLOADS,
            'download_speed_limit': self.DOWNLOAD_SPEED_LIMIT
        }

# نمونه تنظیمات
settings = Settings()
