"""
Custom encrypted field using Fernet symmetric encryption
"""
from django.db import models
from django.conf import settings
from cryptography.fernet import Fernet
import base64


class EncryptedTextField(models.TextField):
    """
    TextField that automatically encrypts data before saving to database
    and decrypts when reading from database using Fernet encryption
    """

    description = "Encrypted text field using Fernet"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._fernet = None

    @property
    def fernet(self):
        """Lazy load Fernet cipher"""
        if self._fernet is None:
            key = settings.CRYPTOGRAPHY_KEY
            if isinstance(key, str):
                key = key.encode()
            self._fernet = Fernet(key)
        return self._fernet

    def get_prep_value(self, value):
        """Encrypt value before saving to database"""
        if value is None or value == '':
            return value

        # If already encrypted (starts with gAAAAA), don't encrypt again
        if isinstance(value, str) and value.startswith('gAAAAA'):
            return value

        # Convert to bytes if string
        if isinstance(value, str):
            value = value.encode('utf-8')

        # Encrypt and return as string
        encrypted = self.fernet.encrypt(value)
        return encrypted.decode('utf-8')

    def from_db_value(self, value, expression, connection):
        """Decrypt value when reading from database"""
        if value is None or value == '':
            return value

        try:
            # Decrypt
            if isinstance(value, str):
                value = value.encode('utf-8')
            decrypted = self.fernet.decrypt(value)
            return decrypted.decode('utf-8')
        except Exception:
            # If decryption fails, return original value (might be unencrypted)
            return value if isinstance(value, str) else value.decode('utf-8')

    def to_python(self, value):
        """Convert to Python value"""
        if value is None or value == '':
            return value
        return str(value)
