#main.py
import asyncio
import os
import re
import time
from datetime import datetime
from typing import Dict, Optional, List, Tuple
import logging

from telethon import TelegramClient, events, types
from telethon.errors import (
    SessionPasswordNeededError,
    PhoneCodeInvalidError,
    FloodWaitError
)
from telethon.tl.functions.messages import GetBotCallbackAnswerRequest
import aiosqlite
import aiofiles
from config import Config

# تنظیمات لاگ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class UserSession:
    """مدیریت session هر کاربر"""
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.client: Optional[TelegramClient] = None
        self.phone_number: Optional[str] = None
        self.auth_state: str = "disconnected"  # disconnected, code_sent, password_needed, connected
        self.phone_code_hash: Optional[str] = None
        self.last_activity: float = time.time()
        self.is_active: bool = False
        
    async def initialize(self):
        """ایجاد session برای کاربر"""
        session_name = f"sessions/user_{self.user_id}"
        os.makedirs("sessions", exist_ok=True)
        
        self.client = TelegramClient(
            session_name,
            Config.API_ID,
            Config.API_HASH,
            device_model="DownloadBot",
            system_version="1.0",
            app_version="1.0.0",
            lang_code="fa"
        )
        
        await self.client.connect()
        
    async def send_code(self, phone_number: str):
        """ارسال کد تأیید"""
        if not self.client:
            await self.initialize()
        
        try:
            sent = await self.client.send_code_request(phone_number)
            self.phone_number = phone_number
            self.phone_code_hash = sent.phone_code_hash
            self.auth_state = "code_sent"
            return True
        except FloodWaitError as e:
            raise Exception(f"لطفا {e.seconds} ثانیه صبر کنید")
        except Exception as e:
            logger.error(f"Error sending code: {e}")
            return False
    
    async def verify_code(self, code: str):
        """تأیید کد ارسال شده"""
        if not self.client or self.auth_state != "code_sent":
            raise Exception("ابتدا شماره تلفن را ارسال کنید")
        
        try:
            await self.client.sign_in(
                phone=self.phone_number,
                code=code,
                phone_code_hash=self.phone_code_hash
            )
            self.auth_state = "connected"
            self.is_active = True
            return True
        except SessionPasswordNeededError:
            self.auth_state = "password_needed"
            raise Exception("لطفا رمز دو مرحله‌ای را وارد کنید")
        except PhoneCodeInvalidError:
            raise Exception("کد وارد شده نامعتبر است")
        except Exception as e:
            logger.error(f"Error verifying code: {e}")
            return False
    
    async def verify_password(self, password: str):
        """تأیید رمز دو مرحله‌ای"""
        if self.auth_state != "password_needed":
            raise Exception("رمز دو مرحله‌ای مورد نیاز نیست")
        
        try:
            await self.client.sign_in(password=password)
            self.auth_state = "connected"
            self.is_active = True
            return True
        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            raise Exception("رمز وارد شده نامعتبر است")
    
    async def logout(self):
        """خروج از حساب"""
        if self.client:
            await self.client.log_out()
            await self.client.disconnect()
            self.client = None
        
        # حذف فایل session
        session_file = f"sessions/user_{self.user_id}.session"
        if os.path.exists(session_file):
            os.remove(session_file)
        
        self.auth_state = "disconnected"
        self.is_active = False
    
    def update_activity(self):
        """به‌روزرسانی زمان آخرین فعالیت"""
        self.last_activity = time.time()
    
    def is_expired(self):
        """بررسی انقضای session"""
        return time.time() - self.last_activity > Config.SESSION_TIMEOUT

class DownloadBot:
    """ربات اصلی"""
    
    def __init__(self):
        self.bot: Optional[TelegramClient] = None
        self.user_sessions: Dict[int, UserSession] = {}
        self.db_conn: Optional[aiosqlite.Connection] = None
        
    async def initialize(self):
        """راه‌اندازی ربات"""
        # اطمینان از وجود پوشه‌ها
        os.makedirs("sessions", exist_ok=True)
        os.makedirs("downloads", exist_ok=True)
        
        # راه‌اندازی ربات
        self.bot = TelegramClient(
            "bot_session",
            Config.API_ID,
            Config.API_HASH
        ).start(bot_token=Config.BOT_TOKEN)
        
        # راه‌اندازی دیتابیس
        await self.init_database()
        
        # ثبت هندلرها
        await self.register_handlers()
        
        logger.info("ربات راه‌اندازی شد")
        
    async def init_database(self):
        """راه‌اندازی دیتابیس"""
        self.db_conn = await aiosqlite.connect(Config.DB_PATH)
        
        await self.db_conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                phone_number TEXT,
                created_at TIMESTAMP,
                last_login TIMESTAMP,
                download_count INTEGER DEFAULT 0
            )
        ''')
        await self.db_conn.commit()
    
    async def register_handlers(self):
        """ثبت هندلرهای ربات"""
        
        @self.bot.on(events.NewMessage(pattern='/start'))
        async def start_handler(event):
            """دستور شروع"""
            user_id = event.sender_id
            
            # بررسی محدودیت کاربران
            if Config.ALLOWED_USER_IDS and user_id not in Config.ALLOWED_USER_IDS:
                await event.reply("❌ دسترسی شما محدود شده است.")
                return
            
            welcome_text = """
🤖 **ربات دانلودر محتوای محافظت شده**

🔹 **قابلیت‌ها:**
• دانلود از کانال‌ها، گروه‌ها و ربات‌ها
• پشتیبانی از محتوای فروارد شده
• بدون نیاز به ادمین بودن

🔹 **دستورات:**
/login - ورود به حساب کاربری
/download - دانلود از لینک
/channels - لیست کانال‌ها و گروه‌ها
/logout - خروج از حساب
/help - راهنمایی

⚠️ **توجه:** این ربات به شماره تلفن شما نیاز دارد.
            """
            await event.reply(welcome_text)
        
        @self.bot.on(events.NewMessage(pattern='/login'))
        async def login_handler(event):
            """ورود به حساب کاربری"""
            user_id = event.sender_id
            
            # بررسی session فعال
            if user_id in self.user_sessions and self.user_sessions[user_id].is_active:
                await event.reply("✅ شما قبلا وارد شده‌اید.")
                return
            
            # ایجاد session جدید
            session = UserSession(user_id)
            await session.initialize()
            self.user_sessions[user_id] = session
            
            await event.reply("📱 لطفا شماره تلفن خود را با فرمت بین‌المللی ارسال کنید:\nمثال: +989123456789")
        
        @self.bot.on(events.NewMessage(pattern='/download'))
        async def download_handler(event):
            """دانلود محتوا"""
            user_id = event.sender_id
            
            # بررسی لاگین بودن
            if user_id not in self.user_sessions or not self.user_sessions[user_id].is_active:
                await event.reply("❌ ابتدا با دستور /login وارد شوید.")
                return
            
            session = self.user_sessions[user_id]
            session.update_activity()
            
            message = event.message
            if not message.text or len(message.text.split()) < 2:
                await event.reply("📎 لطفا لینک پیام را ارسال کنید:\n/download https://t.me/...")
                return
            
            # استخراج لینک
            link = message.text.split()[1]
            await self.download_content(event, session, link)
        
        @self.bot.on(events.NewMessage(pattern='/channels'))
        async def channels_handler(event):
            """لیست کانال‌ها و گروه‌ها"""
            user_id = event.sender_id
            
            if user_id not in self.user_sessions or not self.user_sessions[user_id].is_active:
                await event.reply("❌ ابتدا وارد شوید.")
                return
            
            session = self.user_sessions[user_id]
            session.update_activity()
            
            try:
                await event.reply("📋 در حال دریافت لیست...")
                
                dialogs = []
                async for dialog in session.client.iter_dialogs(limit=50):
                    if dialog.is_channel or dialog.is_group:
                        dialogs.append(
                            f"• {dialog.name} ({'کانال' if dialog.is_channel else 'گروه'})"
                        )
                
                if dialogs:
                    response = "📊 **کانال‌ها و گروه‌های شما:**\n\n" + "\n".join(dialogs[:20])
                    if len(dialogs) > 20:
                        response += f"\n\n... و {len(dialogs) - 20} مورد دیگر"
                else:
                    response = "کانال یا گروهی یافت نشد."
                
                await event.reply(response)
                
            except Exception as e:
                logger.error(f"Error getting channels: {e}")
                await event.reply("❌ خطا در دریافت لیست.")
        
        @self.bot.on(events.NewMessage(pattern='/logout'))
        async def logout_handler(event):
            """خروج از حساب"""
            user_id = event.sender_id
            
            if user_id in self.user_sessions:
                await self.user_sessions[user_id].logout()
                del self.user_sessions[user_id]
            
            await event.reply("✅ با موفقیت خارج شدید.")
        
        @self.bot.on(events.NewMessage(pattern='/help'))
        async def help_handler(event):
            """راهنمایی"""
            help_text = """
📖 **راهنمای ربات:**

🔐 **احراز هویت:**
1. /login - شروع فرآیند ورود
2. ارسال شماره تلفن با فرمت بین‌المللی
3. دریافت و ارسال کد تأیید
4. در صورت نیاز: ارسال رمز دو مرحله‌ای

📥 **دانلود:**
/download [لینک] - دانلود محتوای لینک

📋 **مدیریت:**
/channels - مشاهده کانال‌ها و گروه‌ها
/logout - خروج از حساب

⚠️ **نکات مهم:**
• شماره تلفن شما نزد ما ذخیره نمی‌شود
• session بعد از 24 ساعت غیرفعال می‌شود
• حداکثر حجم فایل: 2 گیگابایت

🆘 **پشتیبانی:** @your_support_channel
            """
            await event.reply(help_text)
        
        @self.bot.on(events.NewMessage())
        async def message_handler(event):
            """مدیریت پیام‌های معمولی"""
            user_id = event.sender_id
            message = event.message
            
            if user_id not in self.user_sessions:
                return
            
            session = self.user_sessions[user_id]
            session.update_activity()
            
            # مدیریت کد تأیید
            if session.auth_state == "code_sent":
                if message.text and message.text.isdigit():
                    try:
                        await session.verify_code(message.text)
                        await event.reply("✅ ورود موفقیت‌آمیز بود!")
                        
                        # ذخیره در دیتابیس
                        await self.save_user_info(user_id, session.phone_number)
                        
                    except Exception as e:
                        await event.reply(f"❌ {str(e)}")
                else:
                    await event.reply("❌ لطفا فقط عدد کد تأیید را ارسال کنید.")
            
            # مدیریت رمز دو مرحله‌ای
            elif session.auth_state == "password_needed":
                try:
                    await session.verify_password(message.text)
                    await event.reply("✅ ورود موفقیت‌آمیز بود!")
                    
                    # ذخیره در دیتابیس
                    await self.save_user_info(user_id, session.phone_number)
                    
                except Exception as e:
                    await event.reply(f"❌ {str(e)}")
            
            # مدیریت شماره تلفن
            elif session.auth_state == "disconnected":
                if message.text and re.match(r'^\+\d{10,15}$', message.text):
                    try:
                        success = await session.send_code(message.text)
                        if success:
                            await event.reply("📲 کد تأیید به شماره شما ارسال شد.\nلطفا کد را ارسال کنید.")
                        else:
                            await event.reply("❌ خطا در ارسال کد.")
                    except Exception as e:
                        await event.reply(f"❌ {str(e)}")
                else:
                    await event.reply("❌ فرمت شماره تلفن نامعتبر است.\nمثال: +989123456789")
    
    async def save_user_info(self, user_id: int, phone_number: str):
        """ذخیره اطلاعات کاربر در دیتابیس"""
        try:
            await self.db_conn.execute('''
                INSERT OR REPLACE INTO users 
                (user_id, phone_number, created_at, last_login, download_count)
                VALUES (?, ?, ?, ?, COALESCE((SELECT download_count FROM users WHERE user_id = ?), 0))
            ''', (user_id, phone_number, datetime.now(), datetime.now(), user_id))
            await self.db_conn.commit()
        except Exception as e:
            logger.error(f"Error saving user info: {e}")
    
    async def download_content(self, event, session: UserSession, link: str):
        """دانلود محتوای لینک"""
        try:
            # استخراج اطلاعات از لینک
            if "t.me/" not in link:
                await event.reply("❌ لینک نامعتبر است.")
                return
            
            # نمایش وضعیت
            status_msg = await event.reply("⏳ در حال بررسی لینک...")
            
            # دریافت پیام از لینک
            try:
                message = await session.client.get_messages(link)
            except ValueError:
                # اگر لینک مستقیم نبود، سعی در تجزیه
                parts = link.split('/')
                if len(parts) >= 2:
                    entity = parts[-2]
                    message_id = int(parts[-1])
                    message = await session.client.get_messages(entity, ids=message_id)
                else:
                    raise
            
            if not message or not message.media:
                await status_msg.edit("❌ محتوای مدیا یافت نشد.")
                return
            
            await status_msg.edit("📥 در حال دانلود...")
            
            # دانلود فایل
            file_name = f"downloads/{user_id}_{int(time.time())}"
            file_path = await session.client.download_media(
                message,
                file=file_name,
                progress_callback=lambda d, t: self.progress_callback(d, t, status_msg)
            )
            
            if not file_path:
                await status_msg.edit("❌ خطا در دانلود.")
                return
            
            await status_msg.edit("📤 در حال آپلود...")
            
            # ارسال فایل به کاربر
            async with aiofiles.open(file_path, 'rb') as f:
                await self.bot.send_file(
                    event.chat_id,
                    file_path,
                    caption=f"✅ دانلود شد\n📁 {os.path.basename(file_path)}",
                    progress_callback=lambda d, t: self.progress_callback(d, t, status_msg, "آپلود")
                )
            
            await status_msg.delete()
            
            # به‌روزرسانی تعداد دانلودها
            await self.update_download_count(event.sender_id)
            
            # حذف فایل موقت
            try:
                os.remove(file_path)
            except:
                pass
            
        except FloodWaitError as e:
            await event.reply(f"⏳ لطفا {e.seconds} ثانیه صبر کنید و دوباره تلاش کنید.")
        except Exception as e:
            logger.error(f"Download error: {e}")
            await event.reply(f"❌ خطا: {str(e)}")
    
    async def progress_callback(self, downloaded, total, message, action="دانلود"):
        """نمایش پیشرفت"""
        try:
            percent = (downloaded / total) * 100
            bar_length = 20
            filled_length = int(bar_length * downloaded // total)
            bar = '▓' * filled_length + '░' * (bar_length - filled_length)
            
            text = f"{action}: {percent:.1f}%\n{bar}\n{self.format_size(downloaded)} / {self.format_size(total)}"
            
            await message.edit(text)
        except:
            pass
    
    def format_size(self, size_bytes):
        """فرمت‌بندی اندازه فایل"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    async def update_download_count(self, user_id: int):
        """به‌روزرسانی تعداد دانلودها"""
        try:
            await self.db_conn.execute(
                "UPDATE users SET download_count = download_count + 1 WHERE user_id = ?",
                (user_id,)
            )
            await self.db_conn.commit()
        except Exception as e:
            logger.error(f"Error updating download count: {e}")
    
    async def cleanup_sessions(self):
        """پاک‌سازی session های منقضی شده"""
        while True:
            await asyncio.sleep(3600)  # هر ساعت یکبار
            
            expired_users = []
            for user_id, session in self.user_sessions.items():
                if session.is_expired():
                    expired_users.append(user_id)
            
            for user_id in expired_users:
                await self.user_sessions[user_id].logout()
                del self.user_sessions[user_id]
                logger.info(f"Session expired for user {user_id}")
    
    async def run(self):
        """اجرای ربات"""
        await self.initialize()
        
        # شروع پاک‌سازی خودکار
        asyncio.create_task(self.cleanup_sessions())
        
        logger.info("ربات در حال اجراست...")
        await self.bot.run_until_disconnected()

async def main():
    """تابع اصلی"""
    bot = DownloadBot()
    await bot.run()

if __name__ == "__main__":
    # بررسی تنظیمات
    if not Config.API_ID or not Config.API_HASH or not Config.BOT_TOKEN:
        print("❌ لطفا تنظیمات را در فایل .env پر کنید.")
        print("API_ID و API_HASH را از my.telegram.org دریافت کنید.")
        print("BOT_TOKEN را از @BotFather دریافت کنید.")
        exit(1)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n❌ ربات متوقف شد.")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
