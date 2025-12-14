# modules/ui/progress_display.py
from typing import Dict, Any
import math

class ProgressDisplay:
    """نمایش پیشرفت به صورت گرافیکی"""
    
    @staticmethod
    def create_progress_bar(percentage: float, width: int = 20) -> str:
        """ایجاد نوار پیشرفت"""
        
        filled = math.ceil(percentage / 100 * width)
        empty = width - filled
        
        bar = "█" * filled + "░" * empty
        return bar
    
    @staticmethod
    def format_speed(speed_bytes: float) -> str:
        """فرمت‌بندی سرعت"""
        
        if speed_bytes >= 1024 * 1024 * 1024:  # GB/s
            return f"{speed_bytes / (1024*1024*1024):.2f} GB/s"
        elif speed_bytes >= 1024 * 1024:  # MB/s
            return f"{speed_bytes / (1024*1024):.2f} MB/s"
        elif speed_bytes >= 1024:  # KB/s
            return f"{speed_bytes / 1024:.2f} KB/s"
        else:
            return f"{speed_bytes:.0f} B/s"
    
    @staticmethod
    def format_size(size_bytes: int) -> str:
        """فرمت‌بندی حجم"""
        
        if size_bytes >= 1024 * 1024 * 1024:  # GB
            return f"{size_bytes / (1024*1024*1024):.2f} GB"
        elif size_bytes >= 1024 * 1024:  # MB
            return f"{size_bytes / (1024*1024):.2f} MB"
        elif size_bytes >= 1024:  # KB
            return f"{size_bytes / 1024:.2f} KB"
        else:
            return f"{size_bytes} B"
    
    @staticmethod
    def format_time(seconds: float) -> str:
        """فرمت‌بندی زمان"""
        
        if seconds < 60:
            return f"{seconds:.0f} ثانیه"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes:.0f}:{secs:02.0f}"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            return f"{hours:.0f}:{minutes:02.0f}:{secs:02.0f}"
    
    @staticmethod
    def create_progress_message(progress_data: Dict[str, Any]) -> str:
        """ایجاد پیام پیشرفت"""
        
        bar = ProgressDisplay.create_progress_bar(progress_data.get('progress', 0))
        percentage = progress_data.get('progress', 0)
        downloaded = ProgressDisplay.format_size(progress_data.get('downloaded', 0))
        total = ProgressDisplay.format_size(progress_data.get('total', 0))
        speed = ProgressDisplay.format_speed(progress_data.get('speed', 0))
        eta = ProgressDisplay.format_time(progress_data.get('eta', 0))
        filename = progress_data.get('filename', 'در حال پردازش')
        
        message = f"""
📥 **در حال دانلود**

📁 **فایل:** `{filename}`
{bar} **{percentage:.1f}%**

📊 **حجم:** {downloaded} / {total}
⚡ **سرعت:** {speed}
⏱️ **زمان باقی‌مانده:** {eta}

🔄 **پیشرفت دقیق:** {progress_data.get('downloaded', 0):,} از {progress_data.get('total', 0):,} بایت
        """
        
        return message
    
    @staticmethod
    def create_simple_progress(percentage: float) -> str:
        """نمایش ساده پیشرفت"""
        
        stages = ['○', '◔', '◑', '◕', '●']
        stage_index = min(int(percentage / 25), 4)
        
        progress_visual = stages[stage_index] * 5
        return f"{progress_visual} {percentage:.1f}%"
