# modules/utils/error_handler.py
import traceback
import sys
from typing import Optional, Dict, Any
from datetime import datetime
from pyrogram.errors import FloodWait, BadRequest, Unauthorized

class ErrorHandler:
    """مدیریت خطاهای ربات"""
    
    def __init__(self, db_manager=None):
        self.db = db_manager
        
    async def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """مدیریت خطاها"""
        
        error_type = type(error).__name__
        error_message = str(error)
        trace = traceback.format_exc()
        
        # دسته‌بندی خطاها
        if isinstance(error, FloodWait):
            return await self._handle_flood_wait(error, context)
        elif isinstance(error, BadRequest):
            return await self._handle_bad_request(error, context)
        elif isinstance(error, Unauthorized):
            return await self._handle_unauthorized(error, context)
        else:
            return await self._handle_general_error(error, error_type, error_message, trace, context)
    
    async def _handle_flood_wait(self, error: FloodWait, context: Optional[Dict]) -> Dict[str, Any]:
        """مدیریت FloodWait"""
        wait_time = error.value
        
        response = {
            'success': False,
            'error_type': 'FloodWait',
            'error_message': f'تلگرام محدودیت اعمال کرده است. لطفاً {wait_time} ثانیه صبر کنید.',
            'wait_time': wait_time,
            'retry_after': wait_time,
            'can_retry': True,
            'suggested_action': 'wait'
        }
        
        # ذخیره لاگ
        await self._log_error('FloodWait', str(error), context)
        
        return response
    
    async def _handle_bad_request(self, error: BadRequest, context: Optional[Dict]) -> Dict[str, Any]:
        """مدیریت BadRequest"""
        
        error_codes = {
            'FILE_REFERENCE_EXPIRED': 'لینک فایل منقضی شده است',
            'CHANNEL_PRIVATE': 'کانال خصوصی است',
            'USER_NOT_PARTICIPANT': 'شما عضو کانال نیستید',
            'MESSAGE_NOT_FOUND': 'پیام یافت نشد'
        }
        
        error_msg = str(error)
        user_message = 'درخواست نامعتبر است'
        
        for code, message in error_codes.items():
            if code in error_msg:
                user_message = message
                break
        
        response = {
            'success': False,
            'error_type': 'BadRequest',
            'error_message': user_message,
            'can_retry': False,
            'suggested_action': 'check_input'
        }
        
        await self._log_error('BadRequest', error_msg, context)
        
        return response
    
    async def _handle_unauthorized(self, error: Unauthorized, context: Optional[Dict]) -> Dict[str, Any]:
        """مدیریت Unauthorized"""
        response = {
            'success': False,
            'error_type': 'Unauthorized',
            'error_message': 'دسترسی ندارید. لطفاً مجدداً وارد شوید.',
            'can_retry': True,
            'suggested_action': 'relogin',
            'needs_relogin': True
        }
        
        await self._log_error('Unauthorized', str(error), context)
        
        return response
    
    async def _handle_general_error(self, error: Exception, error_type: str, 
                                   error_message: str, trace: str, 
                                   context: Optional[Dict]) -> Dict[str, Any]:
        """مدیریت خطاهای عمومی"""
        
        response = {
            'success': False,
            'error_type': error_type,
            'error_message': 'خطای داخلی رخ داده است',
            'internal_error': error_message,
            'can_retry': False,
            'suggested_action': 'contact_support'
        }
        
        # ذخیره خطا با جزئیات کامل
        await self._log_error(error_type, error_message, context, trace)
        
        return response
    
    async def _log_error(self, error_type: str, error_message: str, 
                        context: Optional[Dict], traceback_str: str = None):
        """ذخیره خطا در دیتابیس"""
        
        if self.db:
            try:
                log_data = {
                    'level': 'ERROR',
                    'module': context.get('module', 'unknown') if context else 'unknown',
                    'message': f"{error_type}: {error_message}",
                    'user_id': context.get('user_id') if context else None,
                    'additional_data': {
                        'context': context,
                        'traceback': traceback_str,
                        'timestamp': datetime.now().isoformat()
                    }
                }
                
                # ذخیره در دیتابیس
                with self.db.get_session() as session:
                    from database.models import SystemLog
                    log = SystemLog(**log_data)
                    session.add(log)
                    session.commit()
                    
            except Exception as e:
                # اگر ذخیره در دیتابیس شکست خورد، در فایل ذخیره کن
                self._log_to_file(error_type, error_message, traceback_str)
    
    def _log_to_file(self, error_type: str, error_message: str, traceback_str: str = None):
        """ذخیره خطا در فایل"""
        try:
            log_entry = f"""
[{datetime.now().isoformat()}] {error_type}: {error_message}
{traceback_str if traceback_str else ''}
{'='*50}
            """
            
            with open('logs/errors.log', 'a', encoding='utf-8') as f:
                f.write(log_entry)
                
        except:
            # آخرین راه حل: چاپ در کنسول
            print(f"[ERROR] {error_type}: {error_message}")
    
    def create_user_friendly_message(self, error_response: Dict[str, Any]) -> str:
        """ایجاد پیام کاربرپسند از خطا"""
        
        templates = {
            'FloodWait': """
⚠️ **محدودیت تلگرام**

تلگرام برای جلوگیری از اسپم، درخواست‌های شما را محدود کرده است.

⏱️ **لطفاً {wait_time} ثانیه صبر کنید**

💡 **راه‌حل:**
• کمی صبر کنید و دوباره تلاش کنید
• از VPN استفاده نکنید
• اگر ادمین هستید، از @SpamBot وضعیت خود را بررسی کنید
            """,
            
            'BadRequest': """
❌ **درخواست نامعتبر**

{error_message}

💡 **راه‌حل:**
• لینک را بررسی کنید
• از عضویت در کانال اطمینان حاصل کنید
• فایل ممکن است حذف شده باشد
            """,
            
            'Unauthorized': """
🔐 **مشکل دسترسی**

احراز هویت شما با مشکل مواجه شده است.

🔄 **لطفاً مجدداً وارد شوید:**
دستور: `/login`

💡 **اگر مشکل ادامه داشت:**
• از حساب دیگری استفاده کنید
• با پشتیبانی تماس بگیرید
            """,
            
            'default': """
❌ **خطای سیستمی**

متأسفانه یک خطای داخلی رخ داده است.

🛠️ **تیم فنی مطلع شد**

⏳ **لطفاً چند دقیقه دیگر مجدداً تلاش کنید**

📞 **اگر مشکل ادامه داشت با پشتیبانی تماس بگیرید**
            """
        }
        
        error_type = error_response.get('error_type', 'default')
        
        if error_type in templates:
            template = templates[error_type]
            if error_type == 'FloodWait':
                return template.format(wait_time=error_response.get('wait_time', 'مقداری'))
            elif error_type == 'BadRequest':
                return template.format(error_message=error_response.get('error_message', 'خطای نامشخص'))
            else:
                return template
        else:
            return templates['default']
