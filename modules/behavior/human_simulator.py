# modules/behavior/human_simulator.py
import asyncio
import random
import time
from typing import Optional, Dict, Any
from enum import Enum

class HumanBehaviorState(Enum):
    """حالت‌های مختلف رفتار انسانی"""
    IDLE = "idle"
    TYPING = "typing"
    UPLOADING = "uploading"
    DOWNLOADING = "downloading"
    THINKING = "thinking"
    ERROR = "error"

class HumanSimulator:
    """شبیه‌سازی رفتار انسانی برای ربات"""
    
    def __init__(self):
        self.behavior_patterns = {
            'typing_speed': {
                'slow': {'min': 80, 'max': 150},  # میلی‌ثانیه بین حروف
                'normal': {'min': 40, 'max': 80},
                'fast': {'min': 20, 'max': 40}
            },
            'action_delays': {
                'quick': {'min': 0.3, 'max': 0.8},
                'normal': {'min': 0.8, 'max': 1.5},
                'thoughtful': {'min': 1.5, 'max': 3.0}
            },
            'error_behavior': {
                'typo_chance': 0.05,  # 5% chance of typo
                'correction_delay': {'min': 0.5, 'max': 1.2},
                'retry_delay': {'min': 1.0, 'max': 2.5}
            }
        }
        
        self.user_profiles = {}  # user_id -> behavior_profile
        
    async def simulate_typing(self, client, chat_id: int, 
                            duration: Optional[float] = None,
                            speed: str = 'normal'):
        """شبیه‌سازی تایپ کردن"""
        
        if duration is None:
            duration = random.uniform(1.0, 3.0)
        
        try:
            # شروع تایپینگ
            await client.send_chat_action(chat_id, "typing")
            
            # نگه داشتن حالت تایپینگ
            start_time = time.time()
            while time.time() - start_time < duration:
                await asyncio.sleep(0.5)  # تلگرام هر 5 ثانیه نیاز به رفرش دارد
                await client.send_chat_action(chat_id, "typing")
                
                # اضافه کردن تغییرات تصادفی در سرعت
                if random.random() < 0.1:  # 10% chance of pause
                    await asyncio.sleep(random.uniform(0.2, 0.5))
                    
        except Exception:
            pass
    
    async def simulate_uploading(self, client, chat_id: int, 
                                duration: Optional[float] = None):
        """شبیه‌سازی آپلود"""
        
        if duration is None:
            duration = random.uniform(2.0, 5.0)
        
        try:
            await client.send_chat_action(chat_id, "upload_document")
            await asyncio.sleep(duration)
        except Exception:
            pass
    
    async def simulate_thinking(self, client, chat_id: int,
                               duration: Optional[float] = None):
        """شبیه‌سازی فکر کردن"""
        
        if duration is None:
            duration = random.uniform(0.5, 2.0)
        
        # ترکیبی از تایپینگ و مکث
        actions = ['typing', 'pause']
        weights = [0.7, 0.3]
        
        start_time = time.time()
        while time.time() - start_time < duration:
            action = random.choices(actions, weights)[0]
            
            if action == 'typing':
                await self.simulate_typing(client, chat_id, 
                                          duration=random.uniform(0.3, 1.0))
            else:
                await asyncio.sleep(random.uniform(0.2, 0.8))
    
    async def human_response_delay(self, message_length: int = 0, 
                                  complexity: str = 'normal') -> float:
        """تاخیر پاسخ انسانی بر اساس طول پیام و پیچیدگی"""
        
        base_delays = {
            'simple': {'min': 0.5, 'max': 1.2},
            'normal': {'min': 1.0, 'max': 2.5},
            'complex': {'min': 2.0, 'max': 4.0}
        }
        
        # تاخیر پایه
        delay_range = base_delays.get(complexity, base_delays['normal'])
        base_delay = random.uniform(delay_range['min'], delay_range['max'])
        
        # اضافه کردن تاخیر بر اساس طول پیام
        length_factor = message_length / 100  # هر 100 کاراکتر 1 ثانیه اضافه
        length_delay = min(length_factor, 3.0)  # حداکثر 3 ثانیه
        
        # اضافه کردن تصادفی‌سازی
        random_factor = random.uniform(-0.3, 0.3)
        
        total_delay = base_delay + length_delay + random_factor
        
        # حداقل و حداکثر
        total_delay = max(0.3, min(total_delay, 10.0))
        
        return total_delay
    
    async def add_typo_and_correction(self, text: str) -> str:
        """اضافه کردن اشتباه تایپی و تصحیح آن"""
        
        if len(text) < 10 or random.random() > self.behavior_patterns['error_behavior']['typo_chance']:
            return text
        
        # انتخاب یک کلمه برای ایجاد اشتباه
        words = text.split()
        if len(words) < 2:
            return text
        
        word_index = random.randint(0, len(words) - 1)
        original_word = words[word_index]
        
        if len(original_word) < 3:
            return text
        
        # ایجاد اشتباه تایپی
        typo_word = self._create_typo(original_word)
        words[word_index] = typo_word
        
        # ساخت متن با اشتباه
        text_with_typo = ' '.join(words)
        
        # بعد از تاخیر، تصحیح اشتباه
        await asyncio.sleep(random.uniform(
            self.behavior_patterns['error_behavior']['correction_delay']['min'],
            self.behavior_patterns['error_behavior']['correction_delay']['max']
        ))
        
        # تصحیح کلمه
        words[word_index] = original_word
        corrected_text = ' '.join(words)
        
        return corrected_text
    
    def _create_typo(self, word: str) -> str:
        """ایجاد اشتباه تایپی در یک کلمه"""
        
        if len(word) <= 2:
            return word
        
        typo_type = random.choice(['swap', 'missing', 'extra', 'wrong'])
        
        if typo_type == 'swap' and len(word) >= 3:
            # جابجایی دو حرف مجاور
            pos = random.randint(0, len(word) - 2)
            word_list = list(word)
            word_list[pos], word_list[pos + 1] = word_list[pos + 1], word_list[pos]
            return ''.join(word_list)
        
        elif typo_type == 'missing' and len(word) >= 3:
            # حذف یک حرف
            pos = random.randint(1, len(word) - 2)
            return word[:pos] + word[pos + 1:]
        
        elif typo_type == 'extra' and len(word) >= 2:
            # اضافه کردن یک حرف اضافی
            pos = random.randint(0, len(word) - 1)
            extra_char = random.choice(['e', 'a', 'i', 'o', 'u', 'r', 't', 's'])
            return word[:pos] + extra_char + word[pos:]
        
        elif typo_type == 'wrong' and len(word) >= 2:
            # جایگزینی یک حرف با حرف مشابه
            similar_chars = {
                'a': ['s', 'q', 'w'],
                's': ['a', 'd', 'w'],
                'd': ['s', 'f', 'e'],
                'ک': ['گ', 'ق'],
                'گ': ['ک', 'ق'],
                'ی': ['غ', 'ث']
            }
            
            for i, char in enumerate(word):
                if char.lower() in similar_chars:
                    similar = similar_chars[char.lower()]
                    replacement = random.choice(similar)
                    
                    if char.isupper():
                        replacement = replacement.upper()
                    
                    return word[:i] + replacement + word[i + 1:]
        
        return word
    
    async def simulate_human_interaction(self, client, chat_id: int,
                                        action_type: str, 
                                        **kwargs) -> Dict[str, Any]:
        """شبیه‌سازی کامل تعامل انسانی"""
        
        interaction = {
            'start_time': time.time(),
            'action_type': action_type,
            'steps': []
        }
        
        try:
            if action_type == 'send_message':
                # شبیه‌سازی فکر کردن قبل از ارسال
                think_time = await self.human_response_delay(
                    len(kwargs.get('text', '')),
                    kwargs.get('complexity', 'normal')
                )
                
                interaction['steps'].append({
                    'action': 'thinking',
                    'duration': think_time
                })
                
                await self.simulate_thinking(client, chat_id, think_time * 0.7)
                
                # شبیه‌سازی تایپ کردن
                text_length = len(kwargs.get('text', ''))
                typing_time = text_length * random.uniform(0.05, 0.15)  # 50-150ms per char
                typing_time = min(typing_time, 5.0)  # حداکثر 5 ثانیه
                
                interaction['steps'].append({
                    'action': 'typing',
                    'duration': typing_time
                })
                
                await self.simulate_typing(client, chat_id, typing_time)
                
                # اضافه کردن تاخیر نهایی
                final_delay = random.uniform(0.1, 0.5)
                await asyncio.sleep(final_delay)
                
                interaction['steps'].append({
                    'action': 'final_delay',
                    'duration': final_delay
                })
            
            elif action_type == 'upload_file':
                # شبیه‌سازی آپلود
                file_size = kwargs.get('file_size', 0)
                upload_duration = file_size / (1024 * 1024) * 0.5  # 0.5 ثانیه به ازای هر مگابایت
                upload_duration = max(1.0, min(upload_duration, 10.0))
                
                interaction['steps'].append({
                    'action': 'uploading',
                    'duration': upload_duration
                })
                
                await self.simulate_uploading(client, chat_id, upload_duration)
            
            elif action_type == 'process_request':
                # شبیه‌سازی پردازش درخواست
                process_time = random.uniform(1.0, 3.0)
                
                interaction['steps'].append({
                    'action': 'processing',
                    'duration': process_time
                })
                
                # ترکیبی از تایپینگ و آپلودینگ
                await self.simulate_typing(client, chat_id, process_time * 0.3)
                await asyncio.sleep(process_time * 0.4)
                await self.simulate_uploading(client, chat_id, process_time * 0.3)
            
            interaction['end_time'] = time.time()
            interaction['total_duration'] = interaction['end_time'] - interaction['start_time']
            
            return interaction
            
        except Exception as e:
            interaction['error'] = str(e)
            return interaction
    
    def create_user_profile(self, user_id: int) -> Dict[str, Any]:
        """ایجاد پروفایل رفتاری برای کاربر"""
        
        if user_id not in self.user_profiles:
            # تعیین شخصیت تصادفی
            personality = random.choice(['patient', 'impatient', 'accurate', 'careless'])
            
            # تنظیمات بر اساس شخصیت
            if personality == 'patient':
                typing_speed = 'slow'
                action_delay = 'thoughtful'
                typo_chance = 0.02
            elif personality == 'impatient':
                typing_speed = 'fast'
                action_delay = 'quick'
                typo_chance = 0.08
            elif personality == 'accurate':
                typing_speed = 'normal'
                action_delay = 'normal'
                typo_chance = 0.01
            else:  # careless
                typing_speed = 'fast'
                action_delay = 'quick'
                typo_chance = 0.1
            
            self.user_profiles[user_id] = {
                'personality': personality,
                'typing_speed': typing_speed,
                'action_delay': action_delay,
                'typo_chance': typo_chance,
                'interaction_count': 0,
                'average_response_time': 0,
                'created_at': time.time()
            }
        
        return self.user_profiles[user_id]
    
    async def get_humanized_message(self, original_text: str, user_id: int) -> str:
        """تبدیل متن به حالت انسانی"""
        
        profile = self.create_user_profile(user_id)
        
        # اضافه کردن اشتباه تایپی بر اساس پروفایل
        if random.random() < profile['typo_chance']:
            text = await self.add_typo_and_correction(original_text)
        else:
            text = original_text
        
        # اضافه کردن احساسات تصادفی
        if random.random() < 0.2:  # 20% chance
            emotions = [' 😊', ' 👍', ' 😄', ' 🤔', ' ⚡']
            if random.random() < 0.3:  # 30% chance of adding emotion
                text += random.choice(emotions)
        
        # به‌روزرسانی آمار پروفایل
        profile['interaction_count'] += 1
        
        return text
