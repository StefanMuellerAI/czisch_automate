from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import logging
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)


class EncryptionService:
    """Service for encrypting/decrypting sensitive data like SSH credentials"""
    
    def __init__(self, password: Optional[str] = None):
        """Initialize with password or use environment variable"""
        self.password = password or settings.encryption_password
        if not self.password:
            raise EnvironmentError("ENCRYPTION_PASSWORD environment variable is required")
        self._fernet = None
    
    def _get_fernet(self) -> Fernet:
        """Get or create Fernet cipher instance"""
        if self._fernet is None:
            # Derive key from password
            salt = b'stable_salt_for_db_encryption'  # Use fixed salt for consistent keys
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(self.password.encode()))
            self._fernet = Fernet(key)
        return self._fernet
    
    def encrypt(self, plaintext: str) -> str:
        """Encrypt a string and return base64 encoded result"""
        try:
            if not plaintext:
                return ""
            
            fernet = self._get_fernet()
            encrypted_bytes = fernet.encrypt(plaintext.encode('utf-8'))
            return base64.urlsafe_b64encode(encrypted_bytes).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            raise
    
    def decrypt(self, encrypted_text: str) -> str:
        """Decrypt a base64 encoded encrypted string"""
        try:
            if not encrypted_text:
                return ""
            
            fernet = self._get_fernet()
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_text.encode('utf-8'))
            decrypted_bytes = fernet.decrypt(encrypted_bytes)
            return decrypted_bytes.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            raise
    
    def encrypt_dict(self, data: dict, fields_to_encrypt: list) -> dict:
        """Encrypt specific fields in a dictionary"""
        result = data.copy()
        for field in fields_to_encrypt:
            if field in result and result[field]:
                result[field] = self.encrypt(str(result[field]))
        return result
    
    def decrypt_dict(self, data: dict, fields_to_decrypt: list) -> dict:
        """Decrypt specific fields in a dictionary"""
        result = data.copy()
        for field in fields_to_decrypt:
            if field in result and result[field]:
                result[field] = self.decrypt(result[field])
        return result


# Global encryption service
encryption_service = EncryptionService()
