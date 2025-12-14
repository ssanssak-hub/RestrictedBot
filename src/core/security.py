# src/core/security.py
import hashlib
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os

class AdvancedSecurity:
    """سیستم امنیتی پیشرفته با رمزنگاری چند لایه"""
    
    def __init__(self):
        self.master_key = self._generate_master_key()
        
    def _generate_master_key(self) -> bytes:
        """تولید کلید اصلی از entropy سیستم"""
        entropy = os.urandom(32) + str(os.getpid()).encode() + str(time.time()).encode()
        return hashlib.sha512(entropy).digest()
    
    def encrypt_session(self, session_data: str, user_id: int) -> dict:
        """رمزنگاری session با الگوریتم ترکیبی"""
        # تولید salt منحصر به فرد
        salt = os.urandom(16)
        
        # تولید کلید از PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.master_key))
        
        # رمزنگاری با Fernet
        fernet = Fernet(key)
        encrypted_data = fernet.encrypt(session_data.encode())
        
        return {
            'encrypted_data': base64.b64encode(encrypted_data).decode(),
            'salt': base64.b64encode(salt).decode(),
            'user_id': user_id,
            'timestamp': time.time(),
            'version': '2.0'
        }
    
    def decrypt_session(self, encrypted_package: dict) -> str:
        """رمزگشایی session"""
        try:
            salt = base64.b64decode(encrypted_package['salt'])
            encrypted_data = base64.b64decode(encrypted_package['encrypted_data'])
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(self.master_key))
            
            fernet = Fernet(key)
            decrypted_data = fernet.decrypt(encrypted_data)
            
            return decrypted_data.decode()
        except Exception as e:
            raise SecurityException(f"خطا در رمزگشایی: {str(e)}")

class SecurityException(Exception):
    """خطاهای امنیتی"""
    pass
