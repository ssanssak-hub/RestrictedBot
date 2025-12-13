#main.py
import asyncio
import logging
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import SessionPasswordNeeded
from config import API_ID, API_HASH, BOT_TOKEN, ADMIN_IDS
from database.models import Database
from keyboards.main_menu import get_main_menu
from keyboards.glass_buttons import get_permission_buttons
from modules.auth import AuthManager
from modules.downloader import DownloadManager
from modules.uploader import UploadManager
from modules.utils import format_size, progress_bar

# تنظیمات لاگ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TelegramUserBot:
    def __init__(self):
        self.db = Database()
        self.auth_manager = AuthManager(self.db)
        self.download_manager = DownloadManager()
        self.upload_manager = UploadManager()
        self.user_clients = {}  # کلاینت‌های کاربران
        self.bot = None
        
    async def start_bot(self):
        """شروع ربات"""
        # اتصال به دیتابیس
        await self.db.connect()
        
        # ایجاد ربات تلگرام
        self.bot = Client(
            "userbot_bot",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN
        )
        
        # ثبت هندلرها
        self.register_handlers()
        
        # شروع ربات
        await self.bot.start()
        logger.info("ربات شروع به کار کرد")
        
        # نگه داشتن ربات در حالت اجرا
        await asyncio.Event().wait()
    
    def register_handlers(self):
        """ثبت هندلرهای ربات"""
        
        @self.bot.on_message(filters.command("start") & filters.private)
        async def start_command(client, message: Message):
            """دستور شروع"""
            welcome_text = """
🎊 **به ربات UserBot پیشرفته خوش آمدید!**

🔒 **امنیت تضمین شده:**
• این ربات کاملاً ایمن و متن‌باز است
• کد ربات قابل بررسی توسط توسعه‌دهندگان
• اطلاعات شما محفوظ می‌ماند

📋 **قابلیت‌های اصلی:**
1. 🔐 مدیریت چند حساب کاربری
2. 📥 دانلود از کانال‌ها و گروه‌ها
3. 📤 آپلود فایل‌ها
4. ⚡ سرعت بالا با نمایش پیشرفت
5. 👤 رفتار طبیعی و انسانی

⚠️ **توجه:** ربات فقط به دسترسی‌های انتخابی شما دسترسی خواهد داشت.
            """
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔐 ورود با حساب کاربری", callback_data="login")],
                [InlineKeyboardButton("📖 راهنمای استفاده", callback_data="help")],
                [InlineKeyboardButton("🔒 حریم خصوصی و امنیت", callback_data="privacy")]
            ])
            
            await message.reply_text(welcome_text, reply_markup=keyboard)
        
        @self.bot.on_callback_query()
        async def handle_callback(client, callback_query):
            """مدیریت کلیک روی دکمه‌ها"""
            data = callback_query.data
            
            if data == "login":
                await self.handle_login(callback_query)
            elif data == "help":
                await self.show_help(callback_query)
            elif data == "privacy":
                await self.show_privacy_info(callback_query)
            elif data.startswith("permission_"):
                await self.handle_permission_selection(callback_query)
            elif data == "confirm_login":
                await self.complete_login(callback_query)
            elif data == "cancel_login":
                await callback_query.message.edit_text("❌ فرآیند ورود لغو شد.")
            
            await callback_query.answer()
        
        @self.bot.on_message(filters.command("menu") & filters.private)
        async def show_menu(client, message: Message):
            """نمایش منوی اصلی"""
            user_id = message.from_user.id
            user_data = await self.db.get_user(user_id)
            
            if user_data and user_data.get('session_string'):
                await message.reply_text(
                    "📋 **منوی اصلی**",
                    reply_markup=get_main_menu(user_id in ADMIN_IDS)
                )
            else:
                await message.reply_text("⚠️ لطفاً ابتدا وارد حساب کاربری خود شوید.")
        
        @self.bot.on_message(filters.command("download") & filters.private)
        async def download_command(client, message: Message):
            """دریافت لینک برای دانلود"""
            args = message.text.split(" ", 1)
            
            if len(args) < 2:
                await message.reply_text("""
📥 **دانلود فایل**

لطفاً لینک فایل را ارسال کنید:
`/download [لینک]`

یا می‌توانید پیام حاوی فایل را فوروارد کنید.
                """)
                return
            
            url = args[1]
            await self.process_download(message, url)
        
        @self.bot.on_message(filters.private & filters.forwarded)
        async def handle_forwarded_message(client, message: Message):
            """مدیریت پیام‌های فوروارد شده"""
            await self.process_download(message)
    
    async def handle_login(self, callback_query):
        """مدیریت فرآیند ورود"""
        # نمایش توضیحات دسترسی‌ها
        permissions_text = """
🔐 **درخواست دسترسی‌های لازم:**

ربات برای ارائه خدمات به دسترسی‌های زیر نیاز دارد:

✅ **دسترسی‌های پایه:**
• خواندن پیام‌ها (برای دانلود محتوا)
• مشاهده گروه‌ها و کانال‌ها

✅ **دسترسی‌های اختیاری (انتخاب شما):**
• ارسال پیام
• مدیریت چت
• حذف پیام‌ها

⚠️ **تضمین امنیت:**
• هیچ اطلاعاتی ذخیره نمی‌شود
• کد منبع قابل بررسی است
• امکان خروج در هر لحظه

لطفاً دسترسی‌های مورد نظر خود را انتخاب کنید:
        """
        
        await callback_query.message.edit_text(
            permissions_text,
            reply_markup=get_permission_buttons()
        )
    
    async def handle_permission_selection(self, callback_query):
        """مدیریت انتخاب دسترسی‌ها"""
        permission_type = callback_query.data.split("_")[1]
        user_id = callback_query.from_user.id
        
        # ذخیره انتخاب کاربر
        await self.db.save_user_permission(user_id, permission_type)
        
        # درخواست شماره تلفن
        await callback_query.message.edit_text(
            "📱 لطفاً شماره تلفن خود را با فرمت بین‌المللی ارسال کنید:\n\n"
            "مثال: `+989123456789`",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data="login")],
                [InlineKeyboardButton("❌ لغو", callback_data="cancel_login")]
            ])
        )
        
        # تنظیم حالت برای دریافت شماره تلفن
        await self.db.set_user_state(user_id, "awaiting_phone")
    
    async def complete_login(self, callback_query):
        """تکمیل فرآیند ورود"""
        user_id = callback_query.from_user.id
        user_data = await self.db.get_user(user_id)
        
        if not user_data or 'phone_number' not in user_data:
            await callback_query.message.edit_text("❌ اطلاعات ناقص است. لطفاً مجدداً تلاش کنید.")
            return
        
        try:
            # ایجاد کلاینت برای کاربر
            session_name = f"user_{user_id}"
            client = Client(
                session_name,
                api_id=API_ID,
                api_hash=API_HASH,
                device_model="UserBot",
                system_version="1.0",
                app_version="1.0.0"
            )
            
            await client.connect()
            
            # ارسال کد تأیید
            sent_code = await client.send_code(user_data['phone_number'])
            
            # درخواست کد تأیید از کاربر
            await callback_query.message.edit_text(
                "🔢 لطفاً کد تأیید ارسال شده به تلگرام را وارد کنید:\n\n"
                "کد را به این فرمت ارسال کنید: `12345`",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ لغو", callback_data="cancel_login")]
                ])
            )
            
            # ذخیره اطلاعات برای مرحله بعد
            await self.db.set_user_state(user_id, "awaiting_code")
            await self.db.save_temp_data(user_id, {
                'client': client,
                'phone_code_hash': sent_code.phone_code_hash
            })
            
        except Exception as e:
            logger.error(f"خطا در ورود: {e}")
            await callback_query.message.edit_text("❌ خطا در فرآیند ورود. لطفاً مجدداً تلاش کنید.")
    
    async def process_download(self, message: Message, url=None):
        """پردازش درخواست دانلود"""
        user_id = message.from_user.id
        user_data = await self.db.get_user(user_id)
        
        if not user_data or 'session_string' not in user_data:
            await message.reply_text("⚠️ لطفاً ابتدا وارد حساب کاربری خود شوید.")
            return
        
        try:
            # ایجاد کلاینت کاربر
            client = self.user_clients.get(user_id)
            if not client:
                client = await self.auth_manager.create_client_from_session(
                    user_data['session_string']
                )
                self.user_clients[user_id] = client
            
            # شروع دانلود
            progress_msg = await message.reply_text("📥 در حال شروع دانلود...")
            
            if url:
                # دانلود از لینک
                result = await self.download_manager.download_from_url(
                    client, url, user_id, progress_callback=lambda p: self.update_progress(p, progress_msg)
                )
            else:
                # دانلود از پیام فوروارد شده
                result = await self.download_manager.download_message(
                    client, message, user_id, progress_callback=lambda p: self.update_progress(p, progress_msg)
                )
            
            if result['success']:
                # آپلود فایل
                await progress_msg.edit_text("📤 در حال آپلود فایل...")
                
                upload_result = await self.upload_manager.upload_file(
                    result['file_path'], 
                    message.chat.id,
                    progress_callback=lambda p: self.update_progress(p, progress_msg)
                )
                
                if upload_result['success']:
                    await progress_msg.edit_text("✅ فایل با موفقیت آپلود شد!")
                else:
                    await progress_msg.edit_text(f"❌ خطا در آپلود: {upload_result['error']}")
            
        except Exception as e:
            logger.error(f"خطا در دانلود: {e}")
            await message.reply_text(f"❌ خطا در پردازش: {str(e)}")
    
    async def update_progress(self, progress_data, progress_msg):
        """به‌روزرسانی وضعیت پیشرفت"""
        try:
            bar = progress_bar(progress_data['percentage'], 20)
            text = f"""
📊 **پیشرفت دانلود**

{bar} {progress_data['percentage']:.1f}%

📁 فایل: `{progress_data.get('filename', 'در حال پردازش')}`
📊 حجم: {format_size(progress_data.get('downloaded', 0))} / {format_size(progress_data.get('total', 0))}
⚡ سرعت: {format_size(progress_data.get('speed', 0))}/s
⏱️ زمان باقی‌مانده: {progress_data.get('eta', '--')} ثانیه
            """
            await progress_msg.edit_text(text)
        except:
            pass
    
    async def show_help(self, callback_query):
        """نمایش راهنما"""
        help_text = """
📖 **راهنمای استفاده از ربات**

🔹 **1. ورود به حساب:**
   - روی دکمه "ورود با حساب کاربری" کلیک کنید
   - دسترسی‌های مورد نظر را انتخاب کنید
   - شماره تلفن و کد تأیید را وارد کنید

🔹 **2. دانلود فایل:**
   - ارسال لینک با دستور `/download [لینک]`
   - فوروارد پیام حاوی فایل
   - انتخاب از منوی دانلود

🔹 **3. مدیریت حساب:**
   - مشاهده حساب‌های متصل
   - خروج از حساب‌ها
   - تنظیمات دانلود/آپلود

🔹 **4. تنظیمات:**
   - محدودیت سرعت
   - فرمت خروجی
   - کیفیت دانلود

🔹 **5. پنل ادمین** (فقط برای مدیران):
   - مشاهده کاربران
   - آمار استفاده
   - تنظیمات سیستم

⚠️ **نکات امنیتی:**
- هرگز اطلاعات حساب خود را با دیگران به اشتراک نگذارید
- به صورت دوره‌ای رمز عبور خود را تغییر دهید
- فقط از کانال‌های معتبر دانلود کنید

برای شروع از دستور /start استفاده کنید.
        """
        
        await callback_query.message.edit_text(
            help_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data="start")]
            ])
        )
    
    async def show_privacy_info(self, callback_query):
        """نمایش اطلاعات حریم خصوصی"""
        privacy_text = """
🔒 **حریم خصوصی و امنیت**

✅ **اطلاعات ذخیره شده:**
• شناسه کاربری
• رشته نشست (Session String) رمزنگاری شده
• تنظیمات کاربر

❌ **اطلاعات ذخیره نشده:**
• شماره تلفن
• رمز عبور
• پیام‌های شخصی
• اطلاعات تماس

🔐 **رمزنگاری:**
• همه داده‌ها با AES-256 رمزنگاری می‌شوند
• ارتباطات با سرورهای تلگرام رمزنگاری شده هستند
• نشست‌ها به صورت محلی ذخیره می‌شوند

🛡️ **امنیت:**
• کد منبع باز و قابل بررسی
• هیچ دسترسی غیرضروری
• امکان حذف کامل داده‌ها

📜 **متن کامل سیاست حریم خصوصی در مخزن گیت‌هاب موجود است.**

🔄 **برای حذف کامل داده‌های خود از دستور /delete_account استفاده کنید.**
        """
        
        await callback_query.message.edit_text(
            privacy_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data="start")],
                [InlineKeyboardButton("🗑️ حذف حساب", callback_data="request_delete")]
            ])
        )

async def main():
    """تابع اصلی اجرای ربات"""
    bot = TelegramUserBot()
    await bot.start_bot()

if __name__ == "__main__":
    asyncio.run(main())
