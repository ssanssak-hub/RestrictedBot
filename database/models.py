# database/models.py
from sqlalchemy import create_engine, Column, Integer, String, Text, BigInteger, Boolean, DateTime, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from datetime import datetime
import json

Base = declarative_base()

class User(Base):
    """مدل کاربر"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(100), nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    phone_number = Column(String(20), nullable=True)
    
    # تنظیمات کاربر
    session_string = Column(Text, nullable=True)  # رمزنگاری شده
    permissions = Column(JSON, default={
        'view_messages': True,
        'send_messages': False,
        'delete_messages': False,
        'manage_chats': False,
        'access_files': True,
        'account_info': False
    })
    
    # آمار
    total_downloads = Column(Integer, default=0)
    total_uploads = Column(Integer, default=0)
    total_download_size = Column(BigInteger, default=0)
    total_upload_size = Column(BigInteger, default=0)
    
    # وضعیت
    is_active = Column(Boolean, default=True)
    is_premium = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    
    # زمان‌ها
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    last_activity = Column(DateTime, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.username,
            'first_name': self.first_name,
            'permissions': self.permissions,
            'total_downloads': self.total_downloads,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class DownloadTask(Base):
    """مدل کار دانلود"""
    __tablename__ = 'download_tasks'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    task_id = Column(String(50), unique=True, nullable=False)
    
    # اطلاعات فایل
    file_name = Column(String(500), nullable=True)
    file_size = Column(BigInteger, default=0)
    file_type = Column(String(50), nullable=True)
    source = Column(Text, nullable=True)  # لینک یا chat_id:message_id
    
    # وضعیت
    status = Column(String(20), default='pending')  # pending, downloading, completed, failed
    progress = Column(Float, default=0.0)  # درصد پیشرفت
    download_speed = Column(Float, default=0.0)  # بایت بر ثانیه
    estimated_time = Column(Float, default=0.0)  # ثانیه
    
    # مسیرها
    temp_path = Column(Text, nullable=True)
    final_path = Column(Text, nullable=True)
    
    # لاگ
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    
    # زمان‌ها
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

class SystemLog(Base):
    """مدل لاگ سیستم"""
    __tablename__ = 'system_logs'
    
    id = Column(Integer, primary_key=True)
    level = Column(String(20), nullable=False)  # info, warning, error, security
    module = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    user_id = Column(BigInteger, nullable=True)
    ip_address = Column(String(45), nullable=True)
    additional_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class DatabaseManager:
    """مدیریت دیتابیس"""
    
    def __init__(self, db_url: str = "sqlite:///data/bot.db"):
        self.engine = create_engine(db_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine, expire_on_commit=False)
        
    def init_db(self):
        """ایجاد جداول"""
        Base.metadata.create_all(bind=self.engine)
        print("✅ دیتابیس ایجاد شد")
    
    def get_session(self):
        """دریافت session"""
        return self.SessionLocal()
