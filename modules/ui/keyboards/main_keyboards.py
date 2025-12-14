# modules/ui/keyboards/main_keyboards.py
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from typing import List, Optional

class MainKeyboards:
    """کلیدبوردهای اصلی ربات"""
    
    @staticmethod
    def get_main_menu_keyboard(is_admin: bool = False) -> InlineKeyboardMarkup:
        """منوی اصلی"""
        buttons = [
            [
                InlineKeyboardButton("📥 دانلود", callback_data="menu_download"),
                InlineKeyboardButton("📤 آپلود", callback_data="menu_upload")
            ],
            [
                InlineKeyboardButton("👤 حساب‌ها", callback_data="menu_accounts"),
                InlineKeyboardButton("⚙️ تنظیمات", callback_data="menu_settings")
            ],
            [
                InlineKeyboardButton("📊 آمار", callback_data="menu_stats"),
                InlineKeyboardButton("🆘 راهنما", callback_data="menu_help")
            ]
        ]
        
        if is_admin:
            buttons.append([
                InlineKeyboardButton("🛠️ پنل ادمین", callback_data="menu_admin")
            ])
        
        return InlineKeyboardMarkup(buttons)
    
    @staticmethod
    def get_download_options_keyboard() -> InlineKeyboardMarkup:
        """گزینه‌های دانلود"""
        buttons = [
            [
                InlineKeyboardButton("🔗 از لینک", callback_data="download_link"),
                InlineKeyboardButton("📱 از تلگرام", callback_data="download_telegram")
            ],
            [
                InlineKeyboardButton("📁 فایل‌های من", callback_data="download_myfiles"),
                InlineKeyboardButton("📋 تاریخچه", callback_data="download_history")
            ],
            [
                InlineKeyboardButton("🔙 بازگشت", callback_data="menu_main")
            ]
        ]
        
        return InlineKeyboardMarkup(buttons)
    
    @staticmethod
    def get_accounts_keyboard(accounts: List[Dict]) -> InlineKeyboardMarkup:
        """منوی حساب‌ها"""
        buttons = []
        
        for i, account in enumerate(accounts[:5], 1):
            status = "✅" if account.get('is_active', False) else "❌"
            btn_text = f"{i}. {status} {account.get('name', 'بدون نام')[:15]}"
            buttons.append([
                InlineKeyboardButton(btn_text, callback_data=f"account_{account.get('id')}")
            ])
        
        buttons.extend([
            [
                InlineKeyboardButton("➕ افزودن حساب", callback_data="account_add"),
                InlineKeyboardButton("🔄 تعویض حساب", callback_data="account_switch")
            ],
            [
                InlineKeyboardButton("🗑️ حذف حساب", callback_data="account_remove"),
                InlineKeyboardButton("⚙️ تنظیمات حساب", callback_data="account_settings")
            ],
            [
                InlineKeyboardButton("🔙 بازگشت", callback_data="menu_main")
            ]
        ])
        
        return InlineKeyboardMarkup(buttons)
    
    @staticmethod
    def get_settings_keyboard() -> InlineKeyboardMarkup:
        """تنظیمات"""
        buttons = [
            [
                InlineKeyboardButton("⚡ سرعت دانلود", callback_data="setting_speed"),
                InlineKeyboardButton("💾 محل ذخیره‌سازی", callback_data="setting_storage")
            ],
            [
                InlineKeyboardButton("👤 رفتار انسانی", callback_data="setting_human"),
                InlineKeyboardButton("🔔 نوتیفیکیشن", callback_data="setting_notify")
            ],
            [
                InlineKeyboardButton("🔐 حریم خصوصی", callback_data="setting_privacy"),
                InlineKeyboardButton("🌐 زبان", callback_data="setting_language")
            ],
            [
                InlineKeyboardButton("🔄 بازنشانی", callback_data="setting_reset"),
                InlineKeyboardButton("💾 ذخیره تنظیمات", callback_data="setting_save")
            ],
            [
                InlineKeyboardButton("🔙 بازگشت", callback_data="menu_main")
            ]
        ]
        
        return InlineKeyboardMarkup(buttons)
    
    @staticmethod
    def get_glass_buttons_permissions() -> InlineKeyboardMarkup:
        """دکمه‌های شیشه‌ای دسترسی‌ها"""
        buttons = [
            [
                InlineKeyboardButton("👁️ مشاهده پیام‌ها", callback_data="perm_view"),
                InlineKeyboardButton("💬 ارسال پیام", callback_data="perm_send")
            ],
            [
                InlineKeyboardButton("🗑️ حذف پیام‌ها", callback_data="perm_delete"),
                InlineKeyboardButton("👥 مدیریت چت", callback_data="perm_manage")
            ],
            [
                InlineKeyboardButton("📁 دسترسی فایل‌ها", callback_data="perm_files"),
                InlineKeyboardButton("👤 اطلاعات حساب", callback_data="perm_account")
            ],
            [
                InlineKeyboardButton("✅ تأیید همه", callback_data="perm_all"),
                InlineKeyboardButton("❌ هیچکدام", callback_data="perm_none")
            ],
            [
                InlineKeyboardButton("🔙 بازگشت", callback_data="back"),
                InlineKeyboardButton("➡️ ادامه", callback_data="perm_continue")
            ]
        ]
        
        return InlineKeyboardMarkup(buttons)
    
    @staticmethod
    def get_cancel_keyboard() -> InlineKeyboardMarkup:
        """دکمه لغو"""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ لغو", callback_data="cancel")]
        ])
