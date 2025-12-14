#main.py
"""
🎯 ربات UserBot تلگرام پیشرفته
📌 ورژن: 3.0.0 کامل
👨‍💻 توسعه‌دهنده: شما
📅 آخرین به‌روزرسانی: 2024

🔐 ویژگی‌ها:
• احراز هویت امن با رمزنگاری AES-256
• دانلود/آپلود هوشمند با نمایش پیشرفت
• مدیریت چند حساب کاربری
• رفتار انسانی واقعی
• پنل ادمین کامل
• امنیت بالا و لاگ‌گیری پیشرفته
"""

import asyncio
import logging
import sys
import signal
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable

# اضافه کردن مسیر ماژول‌ها
sys.path.insert(0, str(Path(__file__).parent))

# ایمپورت‌های Pyrogram
from pyrogram import Client, filters, idle
from pyrogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton,
    CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
)
from pyrogram.errors import (
    FloodWait, SessionPasswordNeeded, PhoneCodeInvalid,
    BadRequest, Unauthorized, ChannelPrivate
)

# ایمپورت ماژول‌های داخلی
from config.settings import settings
from database.models import DatabaseManager, User, DownloadTask, SystemLog
from modules.auth.login_handler import LoginHandler
from modules.auth.multi_account_manager import MultiAccountManager
from modules.downloader.smart_downloader import SmartDownloader
from modules.downloader.telegram_downloader import TelegramDownloader
from modules.uploader.smart_uploader import SmartUploader
from modules.behavior.human_simulator import HumanSimulator
from modules.admin.advanced_panel import AdvancedAdminPanel
from modules.core.security import AdvancedSecurity
from modules.core.session_manager import SessionManager
from modules.ui.keyboards.main_keyboards import MainKeyboards
from modules.ui.progress_display import ProgressDisplay
from modules.utils.error_handler import ErrorHandler
from modules.utils.helpers import Helpers
from modules.utils.advanced_logger import AdvancedLogger
from modules.utils.speed_limiter import SpeedLimiter, RateLimiter

# تنظیمات لاگ‌گیری پیشرفته
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(settings.LOGS_DIR / 'bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class TelegramUserBotPro:
    """کلاس اصلی ربات UserBot"""
    
    def __init__(self):
        self.settings = settings
        self.db = DatabaseManager(settings.DATABASE_URL)
        self.security = AdvancedSecurity()
        self.logger = AdvancedLogger("TelegramUserBotPro")
        self.helpers = Helpers()
        
        # مدیران سیستم
        self.login_handler = LoginHandler(self.db, self.security)
        self.session_manager = SessionManager(self.db, self.security)
        self.account_manager = MultiAccountManager(self.db, self.security)
        self.error_handler = ErrorHandler(self.db)
        
        # ماژول‌های عملیاتی
        self.downloader = SmartDownloader()
        self.telegram_downloader = TelegramDownloader()
        self.uploader = SmartUploader()
        self.humanizer = HumanSimulator()
        
        # رابط کاربری
        self.keyboards = MainKeyboards()
        self.progress_display = ProgressDisplay()
        
        # پنل ادمین
        self.admin_panel = None
        
        # ربات تلگرام
        self.bot = None
        
        # کش داده‌ها
        self.user_cache = {}
        self.download_tasks = {}
        self.rate_limiter = RateLimiter(max_calls=30, period=1.0)  # 30 درخواست در ثانیه
        
        # وضعیت سیستم
        self.start_time = datetime.now()
        self.is_shutting_down = False
        
        # ثبت شروع
        self.logger.logger.info("=" * 50)
        self.logger.logger.info("🚀 ربات UserBot راه‌اندازی شد")
        self.logger.logger.info(f"📁 مسیر داده: {settings.DATA_DIR}")
        self.logger.logger.info(f"🔐 امنیت: AES-256 فعال")
        self.logger.logger.info("=" * 50)
    
    async def initialize(self):
        """مقداردهی اولیه کامل سیستم"""
        try:
            logger.info("📦 در حال مقداردهی اولیه...")
            
            # ایجاد دیتابیس و جداول
            self.db.init_db()
            logger.info("✅ دیتابیس راه‌اندازی شد")
            
            # ایجاد ربات تلگرام
            self.bot = Client(
                "userbot_pro",
                api_id=settings.API_ID,
                api_hash=settings.API_HASH,
                bot_token=settings.BOT_TOKEN,
                workers=100,
                plugins=dict(root="plugins")
            )
            
            # راه‌اندازی session manager
            await self.session_manager.initialize()
            logger.info("✅ Session Manager راه‌اندازی شد")
            
            # تنظیم پنل ادمین
            self.admin_panel = AdvancedAdminPanel(self.db, self)
            
            # ثبت هندلرها
            await self._register_all_handlers()
            logger.info("✅ هندلرها ثبت شدند")
            
            # تنظیم handler سیگنال‌ها
            self._setup_signal_handlers()
            
            # پاک‌سازی فایل‌های موقت قدیمی
            await self._cleanup_temp_files()
            
            logger.info("🎉 مقداردهی اولیه کامل شد!")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطا در مقداردهی اولیه: {e}", exc_info=True)
            return False
    
    def _setup_signal_handlers(self):
        """تنظیم handler برای سیگنال‌های سیستم"""
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)
    
    def _handle_signal(self, signum, frame):
        """مدیریت سیگنال‌های خاموش شدن"""
        logger.info(f"📶 دریافت سیگنال {signum}")
        if not self.is_shutting_down:
            self.is_shutting_down = True
            asyncio.create_task(self.shutdown())
    
    async def _register_all_handlers(self):
        """ثبت تمام هندلرهای ربات"""
        
        # ========== دستورات اصلی ==========
        @self.bot.on_message(filters.command("start") & filters.private)
        async def start_command(client, message: Message):
            await self.handle_start_command(message)
        
        @self.bot.on_message(filters.command("help") & filters.private)
        async def help_command(client, message: Message):
            await self.handle_help_command(message)
        
        @self.bot.on_message(filters.command("menu") & filters.private)
        async def menu_command(client, message: Message):
            await self.handle_menu_command(message)
        
        @self.bot.on_message(filters.command("login") & filters.private)
        async def login_command(client, message: Message):
            await self.handle_login_command(message)
        
        @self.bot.on_message(filters.command("logout") & filters.private)
        async def logout_command(client, message: Message):
            await self.handle_logout_command(message)
        
        # ========== دستورات دانلود/آپلود ==========
        @self.bot.on_message(filters.command("download") & filters.private)
        async def download_command(client, message: Message):
            await self.handle_download_command(message)
        
        @self.bot.on_message(filters.command("upload") & filters.private)
        async def upload_command(client, message: Message):
            await self.handle_upload_command(message)
        
        @self.bot.on_message(filters.command("cancel") & filters.private)
        async def cancel_command(client, message: Message):
            await self.handle_cancel_command(message)
        
        # ========== دستورات مدیریت حساب ==========
        @self.bot.on_message(filters.command("accounts") & filters.private)
        async def accounts_command(client, message: Message):
            await self.handle_accounts_command(message)
        
        @self.bot.on_message(filters.command("addaccount") & filters.private)
        async def add_account_command(client, message: Message):
            await self.handle_add_account_command(message)
        
        # ========== دستورات ادمین ==========
        @self.bot.on_message(filters.command("admin") & filters.private)
        async def admin_command(client, message: Message):
            await self.handle_admin_command(message)
        
        @self.bot.on_message(filters.command("stats") & filters.private)
        async def stats_command(client, message: Message):
            await self.handle_stats_command(message)
        
        # ========== هندلرهای callback ==========
        @self.bot.on_callback_query()
        async def callback_handler(client, callback_query: CallbackQuery):
            await self.handle_callback_query(callback_query)
        
        # ========== هندلرهای پیام متنی ==========
        @self.bot.on_message(filters.private & filters.text)
        async def text_message_handler(client, message: Message):
            await self.handle_text_message(message)
        
        # ========== هندلرهای مدیا ==========
        @self.bot.on_message(filters.private & filters.media)
        async def media_message_handler(client, message: Message):
            await self.handle_media_message(message)
        
        # ========== هندلرهای فوروارد ==========
        @self.bot.on_message(filters.private & filters.forwarded)
        async def forwarded_message_handler(client, message: Message):
            await self.handle_forwarded_message(message)
        
        logger.info("✅ تمام هندلرها ثبت شدند")
    
    # ========== توابع مدیریت دستورات ==========
    
    async def handle_start_command(self, message: Message):
        """مدیریت دستور /start"""
        user_id = message.from_user.id
        
        # لاگ فعالیت
        self.logger.log_user_action(user_id, "start_command", "دستور شروع")
        
        # شبیه‌سازی رفتار انسانی
        await self.humanizer.simulate_typing(self.bot, message.chat.id, duration=1.2)
        
        welcome_text = f"""
👋 **سلام {message.from_user.first_name}!**

🎉 **به ربات UserBot پیشرفته خوش آمدید!**

🆔 **شناسه شما:** `{user_id}`
📅 **تاریخ:** {datetime.now().strftime('%Y/%m/%d %H:%M')}
⚡ **ورژن:** 3.0.0 کامل

✨ **ویژگی‌های اصلی:**
✅ دانلود فوق‌سریع از تلگرام و اینترنت
✅ آپلود هوشمند با قابلیت Resume
✅ مدیریت چند حساب همزمان
✅ پنل ادمین پیشرفته
✅ رفتار انسانی واقعی
✅ امنیت AES-256

🔧 **برای شروع:**
1. ابتدا با `/login` وارد شوید
2. از `/menu` برای دسترسی به امکانات استفاده کنید
3. با `/help` راهنمای کامل را ببینید

⚠️ **توجه:** این ربات کاملاً ایمن است و کد منبع باز است.
        """
        
        keyboard = self.keyboards.get_main_menu_keyboard(
            self.helpers.is_admin(user_id, settings.ADMIN_IDS)
        )
        
        await message.reply_text(welcome_text, reply_markup=keyboard)
    
    async def handle_help_command(self, message: Message):
        """مدیریت دستور /help"""
        user_id = message.from_user.id
        self.logger.log_user_action(user_id, "help_command", "درخواست راهنما")
        
        help_text = """
📖 **راهنمای کامل ربات UserBot**

🔹 **دستورات اصلی:**
• `/start` - شروع ربات و نمایش اطلاعات
• `/menu` - منوی اصلی با دسترسی سریع
• `/help` - این راهنما

🔹 **احراز هویت:**
• `/login` - ورود به حساب تلگرام
• `/logout` - خروج از همه حساب‌ها
• `/accounts` - مدیریت حساب‌های متصل

🔹 **دانلود و آپلود:**
• `/download [لینک]` - دانلود از لینک
• `/upload` - آپلود فایل (فایل را فوروارد کنید)
• `/cancel` - لغو عملیات جاری

🔹 **مدیریت:**
• `/stats` - آمار کاربری
• `/settings` - تنظیمات ربات (به زودی)

🔹 **ادمین:**
• `/admin` - پنل مدیریت (فقط ادمین‌ها)

🔹 **نکات مهم:**
• حداکثر حجم فایل: 2GB
• حداکثر اتصال همزمان: 3 حساب
• لاگ‌ها در مسیر `logs/` ذخیره می‌شوند

🔹 **پشتیبانی:**
برای گزارش مشکل یا پیشنهاد:
• بررسی لاگ‌ها: `logs/bot.log`
• تماس با ادمین: `/admin` (اگر ادمین هستید)

💡 **نکته:** برای دانلود از تلگرام، کافیست پیام را فوروارد کنید یا لینک آن را ارسال کنید.
        """
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 منوی اصلی", callback_data="menu_main")],
            [InlineKeyboardButton("📚 مستندات کامل", url="https://github.com/example/docs")]
        ])
        
        await message.reply_text(help_text, reply_markup=keyboard)
    
    async def handle_menu_command(self, message: Message):
        """مدیریت دستور /menu"""
        user_id = message.from_user.id
        self.logger.log_user_action(user_id, "menu_command", "درخواست منو")
        
        # بررسی لاگین بودن
        if not await self._is_user_logged_in(user_id):
            await message.reply_text("""
⚠️ **لطفاً ابتدا وارد شوید!**

برای استفاده از امکانات ربات نیاز به اتصال حساب تلگرام دارید.

دستور: `/login`
            """)
            return
        
        # شبیه‌سازی تایپ
        await self.humanizer.simulate_thinking(self.bot, message.chat.id, 0.8)
        
        menu_text = """
📱 **منوی اصلی ربات**

🎯 **عملیات اصلی:**
• 📥 دانلود فایل از لینک یا تلگرام
• 📤 آپلود فایل به تلگرام
• 🔄 مدیریت حساب‌های متصل
• ⚡ عملیات سریع

👤 **حساب کاربری:**
• افزودن حساب جدید
• تعویض حساب فعال
• مشاهده حساب‌ها
• تنظیمات حریم خصوصی

⚙️ **تنظیمات:**
• محدودیت سرعت
• مسیر ذخیره‌سازی
• کیفیت دانلود
• رفتار ربات

📊 **آمار و گزارش:**
• استفاده ماهانه
• حجم ترافیک
• فعالیت حساب‌ها
• گزارش سیستم
        """
        
        keyboard = self.keyboards.get_main_menu_keyboard(
            self.helpers.is_admin(user_id, settings.ADMIN_IDS)
        )
        
        await message.reply_text(menu_text, reply_markup=keyboard)
    
    async def handle_login_command(self, message: Message):
        """مدیریت دستور /login"""
        user_id = message.from_user.id
        self.logger.log_user_action(user_id, "login_command", "شروع فرآیند ورود")
        
        await self.login_handler.start_login_process(user_id, message)
    
    async def handle_logout_command(self, message: Message):
        """مدیریت دستور /logout"""
        user_id = message.from_user.id
        self.logger.log_user_action(user_id, "logout_command", "خروج از حساب‌ها")
        
        success = await self.account_manager.logout_all_accounts(user_id)
        
        if success:
            await message.reply_text("""
✅ **خروج موفقیت‌آمیز!**

🔐 تمام حساب‌های شما با موفقیت خارج شدند.
🗑️ اطلاعات نشست پاک‌سازی شد.

💡 برای استفاده مجدد از `/login` استفاده کنید.
            """)
        else:
            await message.reply_text("""
❌ **خطا در خروج!**

⚠️ یا حساب فعالی ندارید یا خطایی رخ داده است.

💡 لطفاً مجدداً تلاش کنید یا با پشتیبانی تماس بگیرید.
            """)
    
    async def handle_download_command(self, message: Message):
        """مدیریت دستور /download"""
        user_id = message.from_user.id
        
        # بررسی لاگین بودن
        if not await self._is_user_logged_in(user_id):
            await message.reply_text("لطفاً ابتدا وارد شوید: `/login`")
            return
        
        # دریافت لینک از پیام
        args = message.text.split(" ", 1)
        if len(args) < 2:
            # نمایش منوی دانلود
            keyboard = self.keyboards.get_download_options_keyboard()
            await message.reply_text("""
📥 **منوی دانلود**

لطفاً روش دانلود را انتخاب کنید:
            """, reply_markup=keyboard)
            return
        
        url = args[1].strip()
        
        # اعتبارسنجی لینک
        if "t.me" in url or "telegram" in url:
            is_valid, error_msg = self.helpers.validate_telegram_link(url)
        else:
            is_valid, error_msg = self.helpers.validate_url(url)
        
        if not is_valid:
            await message.reply_text(f"""
❌ **لینک نامعتبر!**

📛 خطا: {error_msg}

💡 لطفاً لینک معتبری ارسال کنید.
            """)
            return
        
        # شروع دانلود
        await self._start_download(user_id, url, message)
    
    async def handle_upload_command(self, message: Message):
        """مدیریت دستور /upload"""
        user_id = message.from_user.id
        
        # بررسی لاگین بودن
        if not await self._is_user_logged_in(user_id):
            await message.reply_text("لطفاً ابتدا وارد شوید: `/login`")
            return
        
        # بررسی فایل پیوست
        if not message.media:
            await message.reply_text("""
📤 **نحوه آپلود:**

۱. **فایل را به ربات فوروارد کنید**
۲. **یا از منوی آپلود استفاده کنید**

💡 همچنین می‌توانید از دستور زیر استفاده کنید:
`/upload [مسیر فایل در سرور]`
            """)
            return
        
        # شروع آپلود
        await self._start_upload(user_id, message)
    
    async def handle_cancel_command(self, message: Message):
        """مدیریت دستور /cancel"""
        user_id = message.from_user.id
        
        if user_id in self.download_tasks:
            task = self.download_tasks[user_id]
            if 'status_msg' in task:
                try:
                    await task['status_msg'].edit_text("⏹️ عملیات توسط کاربر لغو شد.")
                except:
                    pass
            
            # حذف فایل ناقص
            if 'file_path' in task and os.path.exists(task['file_path']):
                try:
                    os.remove(task['file_path'])
                except:
                    pass
            
            del self.download_tasks[user_id]
            await message.reply_text("✅ عملیات جاری لغو شد.")
        else:
            await message.reply_text("⚠️ هیچ عملیات فعالی برای لغو وجود ندارد.")
    
    async def handle_accounts_command(self, message: Message):
        """مدیریت دستور /accounts"""
        user_id = message.from_user.id
        
        accounts = await self.account_manager.get_user_accounts(user_id)
        
        if not accounts:
            await message.reply_text("""
👤 **حساب‌های شما**

❌ **هیچ حسابی اضافه نکرده‌اید!**

برای اضافه کردن حساب:
۱. از `/login` استفاده کنید
۲. یا روی دکمه زیر کلیک کنید
            """, reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ افزودن حساب", callback_data="account_add")]
            ]))
            return
        
        accounts_text = "👥 **حساب‌های متصل شما:**\n\n"
        
        for i, account in enumerate(accounts, 1):
            status = "✅ فعال" if account.get('is_active', False) else "❌ غیرفعال"
            primary = "⭐ اصلی" if account.get('is_primary', False) else ""
            
            accounts_text += f"{i}. **{account.get('name', 'بدون نام')}**\n"
            accounts_text += f"   👤 @{account.get('username', 'بدون یوزرنیم')}\n"
            accounts_text += f"   {status} {primary}\n"
            
            if 'last_used' in account:
                accounts_text += f"   📅 آخرین استفاده: {account['last_used']}\n"
            
            accounts_text += "\n"
        
        accounts_text += """
💡 **دستورات مدیریت حساب:**
• `/addaccount` - افزودن حساب جدید
• `/accounts switch [شماره]` - تعویض حساب
• `/accounts remove [شماره]` - حذف حساب
• `/logout` - خروج از همه حساب‌ها
        """
        
        keyboard = self.keyboards.get_accounts_keyboard(accounts)
        
        await message.reply_text(accounts_text, reply_markup=keyboard)
    
    async def handle_add_account_command(self, message: Message):
        """مدیریت دستور /addaccount"""
        await self.handle_login_command(message)
    
    async def handle_admin_command(self, message: Message):
        """مدیریت دستور /admin"""
        user_id = message.from_user.id
        
        if not self.helpers.is_admin(user_id, settings.ADMIN_IDS):
            await message.reply_text("""
⛔ **دسترسی ممنوع!**

شما دسترسی ادمین ندارید.

💡 اگر فکر می‌کنید باید ادمین باشید، با توسعه‌دهنده تماس بگیرید.
            """)
            return
        
        await self.admin_panel.show_admin_panel(message)
    
    async def handle_stats_command(self, message: Message):
        """مدیریت دستور /stats"""
        user_id = message.from_user.id
        
        with self.db.get_session() as session:
            user = session.query(User).filter_by(user_id=user_id).first()
            
            if not user:
                stats_text = "📊 **آمار شما**\n\n❌ هنوز فعالیتی ثبت نکرده‌اید."
            else:
                total_downloads = user.total_downloads
                total_uploads = user.total_uploads
                total_download_size = self.helpers._format_size(user.total_download_size)
                total_upload_size = self.helpers._format_size(user.total_upload_size)
                
                stats_text = f"""
📊 **آمار کاربری شما**

👤 **اطلاعات:**
• نام: {user.first_name or 'ندارد'}
• شناسه: `{user.user_id}`
• تاریخ عضویت: {user.created_at.strftime('%Y/%m/%d')}

📥 **دانلود:**
• تعداد: {total_downloads} فایل
• حجم کل: {total_download_size}

📤 **آپلود:**
• تعداد: {total_uploads} فایل
• حجم کل: {total_upload_size}

🕒 **آخرین فعالیت:**
• ورود: {user.last_login.strftime('%Y/%m/%d %H:%M') if user.last_login else 'هرگز'}
• فعالیت: {user.last_activity.strftime('%Y/%m/%d %H:%M') if user.last_activity else 'هرگز'}

💎 **وضعیت:** {'✅ فعال' if user.is_active else '❌ غیرفعال'}
                """
        
        await message.reply_text(stats_text)
    
    async def handle_callback_query(self, callback_query: CallbackQuery):
        """مدیریت کلیک روی دکمه‌ها"""
        data = callback_query.data
        user_id = callback_query.from_user.id
        
        # لاگ فعالیت
        self.logger.log_user_action(user_id, "callback", f"دکمه: {data}")
        
        try:
            # محدودیت rate
            await self.rate_limiter.acquire()
            
            if data == "menu_main":
                await self.handle_menu_command(callback_query.message)
            
            elif data == "menu_download":
                keyboard = self.keyboards.get_download_options_keyboard()
                await callback_query.message.edit_text("📥 لطفاً روش دانلود را انتخاب کنید:", reply_markup=keyboard)
            
            elif data == "download_link":
                await callback_query.message.edit_text("🔗 لطفاً لینک فایل را ارسال کنید:")
            
            elif data == "download_telegram":
                await callback_query.message.edit_text("""
📱 **دانلود از تلگرام**

۱. پیام حاوی فایل را فوروارد کنید
۲. یا لینک پیام تلگرام را ارسال کنید

💡 مثال لینک: `https://t.me/channel/123`
                """)
            
            elif data.startswith("account_"):
                await self._handle_account_callback(callback_query, data)
            
            elif data.startswith("admin_"):
                await self.admin_panel.handle_admin_callback(callback_query)
            
            elif data == "cancel":
                await callback_query.message.edit_text("✅ عملیات لغو شد.")
            
            else:
                await callback_query.answer("⚠️ این دکمه در حال حاضر فعال نیست", show_alert=False)
            
            await callback_query.answer()
            
        except Exception as e:
            error_response = await self.error_handler.handle_error(e, {
                'module': 'callback_handler',
                'user_id': user_id,
                'callback_data': data
            })
            
            user_message = self.error_handler.create_user_friendly_message(error_response)
            await callback_query.message.edit_text(user_message)
    
    async def handle_text_message(self, message: Message):
        """مدیریت پیام‌های متنی"""
        user_id = message.from_user.id
        text = message.text.strip()
        
        # بررسی حالت‌های ورود
        if user_id in self.login_handler.login_states:
            await self._handle_login_states(user_id, message)
            return
        
        # اگر پیام لینک باشد و کاربر لاگین کرده باشد
        if await self._is_user_logged_in(user_id):
            if any(x in text for x in ['http://', 'https://', 't.me', 'telegram']):
                await self._start_download(user_id, text, message)
                return
        
        # پاسخ به پیام‌های متنی دیگر
        await message.reply_text("""
💬 **من یک ربات هستم!**

برای استفاده از امکانات:
• از دستور `/menu` استفاده کنید
• یا از منوی دکمه‌ای استفاده کنید

💡 اگر نیاز به کمک دارید از `/help` استفاده کنید.
        """)
    
    async def handle_media_message(self, message: Message):
        """مدیریت پیام‌های مدیا"""
        user_id = message.from_user.id
        
        if await self._is_user_logged_in(user_id):
            await self._start_upload(user_id, message)
        else:
            await message.reply_text("برای آپلود فایل ابتدا وارد شوید: `/login`")
    
    async def handle_forwarded_message(self, message: Message):
        """مدیریت پیام‌های فوروارد شده"""
        user_id = message.from_user.id
        
        if await self._is_user_logged_in(user_id):
            if message.media:
                await self._start_download(user_id, None, message)
            else:
                await message.reply_text("پیام فوروارد شده حاوی فایل نیست.")
        else:
            await message.reply_text("برای دانلود فایل ابتدا وارد شوید: `/login`")
    
    # ========== توابع کمکی ==========
    
    async def _is_user_logged_in(self, user_id: int) -> bool:
        """بررسی لاگین بودن کاربر"""
        return user_id in self.account_manager.active_clients
    
    async def _handle_login_states(self, user_id: int, message: Message):
        """مدیریت حالت‌های مختلف ورود"""
        login_data = self.login_handler.login_states[user_id]
        
        if login_data['step'] == 'awaiting_phone':
            await self.login_handler.handle_phone_number(user_id, message)
        
        elif login_data['step'] == 'awaiting_code':
            await self.login_handler.handle_verification_code(user_id, message)
        
        elif login_data['step'] == 'awaiting_password':
            await self.login_handler.handle_two_factor_password(user_id, message)
    
    async def _start_download(self, user_id: int, url: Optional[str], message: Message):
        """شروع فرآیند دانلود"""
        try:
            # انتخاب حساب برای دانلود
            accounts = await self.account_manager.get_user_accounts(user_id)
            if not accounts:
                await message.reply_text("هیچ حساب فعالی ندارید. لطفاً ابتدا حساب اضافه کنید.")
                return
            
            # استفاده از حساب فعال یا اولین حساب
            active_account = None
            for account in accounts:
                if account.get('is_active', False):
                    active_account = account
                    break
            
            if not active_account:
                active_account = accounts[0]
            
            account_id = active_account['account_id']
            
            # نمایش وضعیت شروع
            status_msg = await message.reply_text("⏳ در حال بررسی...")
            
            # تابع callback برای نمایش پیشرفت
            async def progress_callback(progress_data: Dict[str, Any]):
                try:
                    progress_text = self.progress_display.create_progress_message(progress_data)
                    await status_msg.edit_text(progress_text)
                except Exception as e:
                    logger.error(f"خطا در آپدیت پیشرفت: {e}")
            
            # ذخیره task
            task_id = f"download_{user_id}_{int(datetime.now().timestamp())}"
            self.download_tasks[user_id] = {
                'task_id': task_id,
                'status_msg': status_msg,
                'start_time': datetime.now(),
                'account_id': account_id
            }
            
            # شروع دانلود
            if url:
                # دانلود از لینک
                if "t.me" in url or "telegram" in url:
                    # دانلود از تلگرام
                    client = self.account_manager.active_clients[user_id][account_id]['client']
                    result = await self.telegram_downloader.download_from_telegram(
                        client, url, progress_callback
                    )
                else:
                    # دانلود از اینترنت
                    result = await self.account_manager.download_with_account(
                        user_id, account_id, url, progress_callback
                    )
            else:
                # دانلود از پیام فوروارد شده
                client = self.account_manager.active_clients[user_id][account_id]['client']
                result = await self.telegram_downloader.download_forwarded_content(
                    client, message.chat.id, message.forward_from_chat.id,
                    message.forward_from_message_id, progress_callback
                )
            
            # پردازش نتیجه
            if result.get('success'):
                # لاگ موفقیت
                self.logger.log_download_complete(
                    user_id,
                    result.get('file_name', 'unknown'),
                    result.get('file_size', 0),
                    (datetime.now() - self.download_tasks[user_id]['start_time']).total_seconds()
                )
                
                # آپلود خودکار
                await self._auto_upload_file(user_id, account_id, result, status_msg)
                
                # به‌روزرسانی آمار کاربر
                await self._update_user_stats(user_id, result.get('file_size', 0), 'download')
                
            else:
                error_text = f"""
❌ **خطا در دانلود!**

📛 خطا: {result.get('error', 'خطای نامشخص')}

💡 **راه‌حل‌ها:**
• لینک را بررسی کنید
• اتصال اینترنت را چک کنید
• از حساب دیگری امتحان کنید
                """
                await status_msg.edit_text(error_text)
            
            # پاک‌سازی task
            if user_id in self.download_tasks:
                del self.download_tasks[user_id]
                
        except Exception as e:
            logger.error(f"خطا در فرآیند دانلود: {e}", exc_info=True)
            
            error_response = await self.error_handler.handle_error(e, {
                'module': '_start_download',
                'user_id': user_id,
                'url': url
            })
            
            user_message = self.error_handler.create_user_friendly_message(error_response)
            await message.reply_text(user_message)
            
            if user_id in self.download_tasks:
                del self.download_tasks[user_id]
    
    async def _start_upload(self, user_id: int, message: Message):
        """شروع فرآیند آپلود"""
        try:
            # انتخاب حساب
            accounts = await self.account_manager.get_user_accounts(user_id)
            if not accounts:
                await message.reply_text("هیچ حساب فعالی ندارید.")
                return
            
            account = accounts[0]
            account_id = account['account_id']
            
            # نمایش وضعیت
            status_msg = await message.reply_text("📥 در حال دریافت فایل...")
            
            # تابع callback برای پیشرفت
            async def progress_callback(progress_data: Dict[str, Any]):
                try:
                    progress_text = self.progress_display.create_progress_message(progress_data)
                    await status_msg.edit_text(progress_text)
                except:
                    pass
            
            # دانلود فایل از پیام
            download_result = await self.telegram_downloader._download_message_media(
                self.bot, message, progress_callback
            )
            
            if not download_result.get('success'):
                await status_msg.edit_text(f"❌ خطا در دریافت فایل: {download_result.get('error')}")
                return
            
            # آپلود فایل
            await status_msg.edit_text("📤 در حال آپلود...")
            
            upload_result = await self.account_manager.upload_with_account(
                user_id, account_id,
                download_result['file_path'],
                message.chat.id,
                progress_callback
            )
            
            if upload_result.get('success'):
                final_text = f"""
✅ **آپلود موفقیت‌آمیز!**

📁 فایل: `{download_result['file_name']}`
📊 حجم: {self.helpers._format_size(download_result['file_size'])}
👤 با حساب: {account['name']}

🎯 عملیات تکمیل شد!
                """
                
                # به‌روزرسانی آمار
                await self._update_user_stats(user_id, download_result['file_size'], 'upload')
                
            else:
                final_text = f"""
❌ **خطا در آپلود!**

📛 خطا: {upload_result.get('error')}

💡 لطفاً دوباره تلاش کنید.
                """
            
            await status_msg.edit_text(final_text)
            
        except Exception as e:
            logger.error(f"خطا در فرآیند آپلود: {e}", exc_info=True)
            
            error_response = await self.error_handler.handle_error(e, {
                'module': '_start_upload',
                'user_id': user_id
            })
            
            user_message = self.error_handler.create_user_friendly_message(error_response)
            await message.reply_text(user_message)
    
    async def _auto_upload_file(self, user_id: int, account_id: str, 
                               download_result: Dict[str, Any], status_msg: Message):
        """آپلود خودکار فایل دانلود شده"""
        try:
            # شبیه‌سازی آپلود
            await self.humanizer.simulate_uploading(self.bot, status_msg.chat.id, 1.0)
            
            # آپلود فایل
            upload_result = await self.account_manager.upload_with_account(
                user_id, account_id,
                download_result['file_path'],
                status_msg.chat.id,
                None  # بدون نمایش پیشرفت
            )
            
            final_text = f"""
✅ **دانلود کامل شد!**

📁 فایل: `{download_result.get('file_name', 'نامشخص')}`
📊 حجم: {self.helpers._format_size(download_result.get('file_size', 0))}
⚡ نوع: {'تلگرام' if 'chat_id' in download_result else 'اینترنت'}

📍 مسیر: `{download_result.get('file_path', 'نامشخص')}`

"""
            
            if upload_result.get('success'):
                final_text += "📤 **آپلود خودکار موفقیت‌آمیز!**\n"
                final_text += f"🔗 فایل با موفقیت آپلود شد."
            else:
                final_text += f"⚠️ **خطا در آپلود خودکار:** {upload_result.get('error', 'خطای نامشخص')}\n"
                final_text += "💡 می‌توانید فایل را دستی آپلود کنید."
            
            await status_msg.edit_text(final_text)
            
        except Exception as e:
            logger.error(f"خطا در آپلود خودکار: {e}")
    
    async def _handle_account_callback(self, callback_query: CallbackQuery, data: str):
        """مدیریت callback‌های حساب"""
        if data == "account_add":
            await callback_query.message.edit_text("لطفاً شماره تلفن خود را ارسال کنید:")
        
        elif data.startswith("account_switch_"):
            account_id = data.replace("account_switch_", "")
            success = await self.account_manager.switch_account(
                callback_query.from_user.id, account_id
            )
            
            if success:
                await callback_query.message.edit_text("✅ حساب فعال تغییر کرد.")
            else:
                await callback_query.message.edit_text("❌ خطا در تعویض حساب.")
    
    async def _update_user_stats(self, user_id: int, file_size: int, action: str):
        """به‌روزرسانی آمار کاربر"""
        try:
            with self.db.get_session() as session:
                user = session.query(User).filter_by(user_id=user_id).first()
                if user:
                    if action == 'download':
                        user.total_downloads += 1
                        user.total_download_size += file_size
                    elif action == 'upload':
                        user.total_uploads += 1
                        user.total_upload_size += file_size
                    
                    user.last_activity = datetime.utcnow()
                    session.commit()
        except Exception as e:
            logger.error(f"خطا در به‌روزرسانی آمار کاربر: {e}")
    
    async def _cleanup_temp_files(self):
        """پاک‌سازی فایل‌های موقت قدیمی"""
        try:
            import shutil
            from datetime import datetime, timedelta
            
            temp_dir = Path("temp")
            if temp_dir.exists():
                for item in temp_dir.iterdir():
                    if item.is_file():
                        # حذف فایل‌های قدیمی‌تر از ۲۴ ساعت
                        file_age = datetime.now() - datetime.fromtimestamp(item.stat().st_mtime)
                        if file_age > timedelta(hours=24):
                            item.unlink()
                    
                    elif item.is_dir():
                        # حذف پوشه‌های خالی
                        if not any(item.iterdir()):
                            item.rmdir()
            
            logger.info("✅ فایل‌های موقت پاک‌سازی شدند")
            
        except Exception as e:
            logger.error(f"خطا در پاک‌سازی فایل‌های موقت: {e}")
    
    async def shutdown(self):
        """خاموش کردن ایمن ربات"""
        if self.is_shutting_down:
            return
        
        self.is_shutting_down = True
        logger.info("🔄 در حال خاموش کردن ربات...")
        
        try:
            # ذخیره وضعیت
            await self._save_system_state()
            
            # قطع اتصالات حساب‌ها
            await self.account_manager.logout_all_accounts()
            
            # پاک‌سازی نشست‌ها
            await self.session_manager.cleanup_expired_sessions()
            
            # قطع اتصال ربات
            if self.bot and self.bot.is_connected:
                await self.bot.stop()
            
            # بستن دیتابیس
            if hasattr(self.db, 'engine'):
                self.db.engine.dispose()
            
            logger.info("✅ ربات با موفقیت خاموش شد")
            
        except Exception as e:
            logger.error(f"❌ خطا در خاموش کردن ربات: {e}")
        
        finally:
            sys.exit(0)
    
    async def _save_system_state(self):
        """ذخیره وضعیت سیستم"""
        try:
            state = {
                'shutdown_time': datetime.now().isoformat(),
                'active_users': len(self.account_manager.active_clients),
                'active_downloads': len(self.download_tasks),
                'total_users': 0,
                'uptime': str(datetime.now() - self.start_time)
            }
            
            with self.db.get_session() as session:
                state['total_users'] = session.query(User).count()
            
            import json
            state_file = settings.DATA_DIR / "system_state.json"
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            
            logger.info("💾 وضعیت سیستم ذخیره شد")
            
        except Exception as e:
            logger.error(f"خطا در ذخیره وضعیت: {e}")
    
    async def run(self):
        """اجرای اصلی ربات"""
        try:
            # مقداردهی اولیه
            if not await self.initialize():
                logger.error("❌ خطا در مقداردهی اولیه")
                return
            
            # شروع ربات
            logger.info("🚀 در حال شروع ربات...")
            await self.bot.start()
            
            # اطلاعات شروع
            me = await self.bot.get_me()
            logger.info(f"🤖 ربات: @{me.username}")
            logger.info(f"🆔 شناسه: {me.id}")
            logger.info(f"👑 ادمین‌ها: {settings.ADMIN_IDS}")
            logger.info(f"📊 محدودیت فایل: {settings.MAX_FILE_SIZE / (1024*1024*1024):.1f}GB")
            
            # نمایش پیام شروع
            startup_msg = f"""
🎉 **ربات UserBot راه‌اندازی شد!**

🤖 ربات: @{me.username}
🆔 شناسه: `{me.id}`
⏰ زمان: {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}
⚡ ورژن: 3.0.0 کامل

✅ سیستم آماده به کار است!
            """
            
            # ارسال پیام به ادمین‌ها
            for admin_id in settings.ADMIN_IDS:
                try:
                    await self.bot.send_message(
                        admin_id,
                        startup_msg
                    )
                except:
                    pass
            
            # لاگ شروع
            self.logger.log_user_action(
                0,  # system
                'bot_startup',
                f"ربات راه‌اندازی شد - @{me.username}"
            )
            
            # نگه داشتن ربات فعال
            logger.info("✅ ربات فعال و آماده به کار!")
            await idle()
            
        except KeyboardInterrupt:
            logger.info("🛑 ربات توسط کاربر متوقف شد")
            
        except Exception as e:
            logger.error(f"❌ خطای غیرمنتظره: {e}", exc_info=True)
            
            # ارسال خطا به ادمین‌ها
            error_msg = f"""
🚨 **خطای ربات!**

📛 خطا: {str(e)[:500]}
⏰ زمان: {datetime.now().strftime('%H:%M:%S')}

⚠️ لطفاً لاگ‌ها را بررسی کنید.
            """
            
            for admin_id in settings.ADMIN_IDS:
                try:
                    await self.bot.send_message(admin_id, error_msg)
                except:
                    pass
            
        finally:
            await self.shutdown()

def main():
    """تابع اصلی اجرا"""
    print("=" * 50)
    print("🎯 ربات UserBot تلگرام - ورژن 3.0.0")
    print("👨‍💻 توسعه‌دهنده: شما")
    print("📅 شروع: " + datetime.now().strftime('%Y/%m/%d %H:%M:%S'))
    print("=" * 50)
    
    # بررسی وجود فایل .env
    if not Path(".env").exists():
        print("❌ فایل .env یافت نشد!")
        print("💡 لطفاً از .env.example یک کپی ایجاد کنید.")
        sys.exit(1)
    
    # بررسی API اطلاعات
    if not settings.API_ID or not settings.API_HASH or not settings.BOT_TOKEN:
        print("❌ اطلاعات API کامل نیست!")
        print("💡 لطفاً فایل .env را بررسی کنید.")
        sys.exit(1)
    
    # ایجاد پوشه‌های لازم
    for directory in [settings.DATA_DIR, settings.LOGS_DIR, 
                      settings.DOWNLOADS_DIR, settings.SESSIONS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
    
    # اجرای ربات
    bot = TelegramUserBotPro()
    
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        print("\n👋 خداحافظ!")
    except Exception as e:
        print(f"❌ خطای اصلی: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # بررسی نسخه Python
    import platform
    python_version = platform.python_version()
    
    if python_version < '3.9':
        print(f"⚠️ هشدار: Python {python_version} - حداقل نسخه مورد نیاز: 3.9")
        print("💡 لطفاً Python را بروزرسانی کنید.")
    
    # اجرای اصلی
    main()
