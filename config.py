# config/settings.py
import os
from pathlib import Path
from typing import Dict, List, Any
import yaml
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """کلاس مدیریت تنظیمات"""
    
    def __init__(self):
        # مسیرهای اصلی
        self.BASE_DIR = Path(__file__).parent.parent
        self.DATA_DIR = self.BASE_DIR / "data"
        self.DOWNLOADS_DIR = self.BASE_DIR / "downloads"
        self.LOGS_DIR = self.BASE_DIR / "logs"
        self.SESSIONS_DIR = self.BASE_DIR / "data" / "sessions"
        
        # اطلاعات API
        self.API_ID = int(os.getenv("API_ID", 0))
        self.API_HASH = os.getenv("API_HASH", "")
       
