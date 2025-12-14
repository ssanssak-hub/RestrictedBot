# modules/core/session_manager.py
import asyncio
import json
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from pyrogram import Client
import redis.asyncio as redis

class SessionManager:
    """مدیریت پیشرفته Session کاربران"""
    
    def __init__(self, db_manager, security_manager):
        self.db = db_manager
        self.security = security_manager
        self.redis_client = None
        self.sessions_cache = {}
        
    async def initialize(self):
        """مقداردهی اولیه"""
        try:
            self.redis_client = redis.Redis(
                host='localhost',
                port=6379,
                db=0,
                decode_responses=True
            )
            await self.redis_client.ping()
            print("✅ Redis متصل شد")
        except:
            print("⚠️ Redis در دسترس نیست، از کش داخلی استفاده می‌شود")
            self.redis_client = None
    
    async def create_session(self, user_id: int, session_string: str) -> str:
        """ایجاد نشست جدید"""
        session_id = f"session_{user_id}_{int(datetime.now().timestamp())}"
        
        # رمزنگاری session
        encrypted_session = self.security.encrypt_session(session_string, user_id)
        
        # ذخیره در کش
        session_data = {
            'session_id': session_id,
            'user_id': user_id,
            'encrypted_session': encrypted_session,
            'created_at': datetime.now().isoformat(),
            'last_used': datetime.now().isoformat(),
            'is_active': True
        }
        
        if self.redis_client:
            await self.redis_client.setex(
                f"session:{session_id}",
                timedelta(hours=24),
                json.dumps(session_data)
            )
        else:
            self.sessions_cache[session_id] = {
                'data': session_data,
                'expires': datetime.now() + timedelta(hours=24)
            }
        
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[Dict]:
        """دریافت نشست"""
        try:
            if self.redis_client:
                session_json = await self.redis_client.get(f"session:{session_id}")
                if session_json:
                    return json.loads(session_json)
            else:
                if session_id in self.sessions_cache:
                    cache_data = self.sessions_cache[session_id]
                    if datetime.now() < cache_data['expires']:
                        return cache_data['data']
                    else:
                        del self.sessions_cache[session_id]
        except Exception as e:
            print(f"خطا در دریافت نشست: {e}")
        
        return None
    
    async def get_user_sessions(self, user_id: int) -> List[Dict]:
        """دریافت تمام نشست‌های کاربر"""
        sessions = []
        
        if self.redis_client:
            # جستجو در Redis
            pattern = f"session:*:user:{user_id}:*"
            keys = await self.redis_client.keys(pattern)
            for key in keys:
                session_json = await self.redis_client.get(key)
                if session_json:
                    sessions.append(json.loads(session_json))
        else:
            # جستجو در کش داخلی
            for session_id, cache_data in self.sessions_cache.items():
                if session_id.startswith(f"session_{user_id}_"):
                    sessions.append(cache_data['data'])
        
        return sessions
    
    async def invalidate_session(self, session_id: str) -> bool:
        """غیرفعال کردن نشست"""
        try:
            if self.redis_client:
                await self.redis_client.delete(f"session:{session_id}")
            else:
                if session_id in self.sessions_cache:
                    del self.sessions_cache[session_id]
            
            return True
        except:
            return False
    
    async def invalidate_user_sessions(self, user_id: int) -> bool:
        """غیرفعال کردن تمام نشست‌های کاربر"""
        try:
            sessions = await self.get_user_sessions(user_id)
            for session in sessions:
                await self.invalidate_session(session['session_id'])
            
            return True
        except:
            return False
    
    async def cleanup_expired_sessions(self):
        """پاک‌سازی نشست‌های منقضی شده"""
        try:
            if self.redis_client:
                # Redis به صورت خودکار منقضی می‌شود
                pass
            else:
                # پاک‌سازی کش داخلی
                current_time = datetime.now()
                expired_keys = [
                    session_id for session_id, cache_data in self.sessions_cache.items()
                    if current_time >= cache_data['expires']
                ]
                
                for key in expired_keys:
                    del self.sessions_cache[key]
                
                if expired_keys:
                    print(f"🗑️ {len(expired_keys)} نشست منقضی شده پاک شد")
        except Exception as e:
            print(f"خطا در پاک‌سازی نشست‌ها: {e}")
