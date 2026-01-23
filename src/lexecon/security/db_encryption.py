"""Database Field Encryption.

Provides transparent encryption/decryption for sensitive database fields
like MFA secrets, API keys, tokens, etc.

Uses Fernet symmetric encryption with a dedicated database encryption key.
Key is managed by SecretsManager (Docker Secrets, encrypted .env, or env vars).
"""

import base64
from typing import Optional

from cryptography.fernet import Fernet


class DatabaseEncryption:
    """Encrypt/decrypt sensitive database fields.

    Uses Fernet symmetric encryption for fast, secure field-level encryption.
    """

    def __init__(self, encryption_key: Optional[str] = None):
        """Initialize database encryption.

        Args:
            encryption_key: Base64-encoded Fernet key (32 bytes)
                           If None, will load from SecretsManager
        """
        if encryption_key:
            self.encryption_key = encryption_key
        else:
            # Load from secrets manager
            from lexecon.security.secrets_manager import get_secret
            self.encryption_key = get_secret("db_encryption_key")

        if not self.encryption_key:
            raise ValueError(
                "Database encryption key not found. "
                "Set DB_ENCRYPTION_KEY environment variable or configure Docker Secrets.",
            )

        self._fernet = self._init_fernet()

    def _init_fernet(self) -> Fernet:
        """Initialize Fernet cipher.

        Returns:
            Fernet instance

        Raises:
            ValueError: If encryption key is invalid
        """
        try:
            # If key is hex string, convert to base64
            if len(self.encryption_key) == 64:
                key_bytes = bytes.fromhex(self.encryption_key)
                key_b64 = base64.urlsafe_b64encode(key_bytes)
            else:
                # Assume it's already base64
                key_b64 = self.encryption_key.encode("utf-8") if isinstance(self.encryption_key, str) else self.encryption_key

            return Fernet(key_b64)
        except Exception as e:
            raise ValueError(f"Invalid database encryption key: {e}")

    def encrypt_field(self, plaintext: str) -> str:
        """Encrypt a database field value.

        Args:
            plaintext: Plain text value to encrypt

        Returns:
            Base64-encoded encrypted value
        """
        if not plaintext:
            return plaintext

        encrypted_bytes = self._fernet.encrypt(plaintext.encode("utf-8"))
        return encrypted_bytes.decode("utf-8")

    def decrypt_field(self, ciphertext: str) -> str:
        """Decrypt a database field value.

        Args:
            ciphertext: Encrypted value (base64-encoded)

        Returns:
            Decrypted plain text value
        """
        if not ciphertext:
            return ciphertext

        try:
            decrypted_bytes = self._fernet.decrypt(ciphertext.encode("utf-8"))
            return decrypted_bytes.decode("utf-8")
        except Exception as e:
            raise ValueError(f"Failed to decrypt field: {e}")

    def encrypt_dict(self, data: dict, fields_to_encrypt: list) -> dict:
        """Encrypt specified fields in a dictionary.

        Args:
            data: Dictionary with data
            fields_to_encrypt: List of field names to encrypt

        Returns:
            Dictionary with encrypted fields
        """
        result = data.copy()
        for field in fields_to_encrypt:
            if result.get(field):
                result[field] = self.encrypt_field(str(result[field]))
        return result

    def decrypt_dict(self, data: dict, fields_to_decrypt: list) -> dict:
        """Decrypt specified fields in a dictionary.

        Args:
            data: Dictionary with encrypted data
            fields_to_decrypt: List of field names to decrypt

        Returns:
            Dictionary with decrypted fields
        """
        result = data.copy()
        for field in fields_to_decrypt:
            if result.get(field):
                result[field] = self.decrypt_field(str(result[field]))
        return result

    @staticmethod
    def generate_key() -> str:
        """Generate a new database encryption key.

        Returns:
            64-character hex-encoded key (32 bytes)
        """
        key = Fernet.generate_key()
        key_bytes = base64.urlsafe_b64decode(key)
        return key_bytes.hex()


# Global instance
_db_encryption: Optional[DatabaseEncryption] = None


def get_db_encryption() -> DatabaseEncryption:
    """Get global database encryption instance.

    Returns:
        DatabaseEncryption instance
    """
    global _db_encryption

    if _db_encryption is None:
        _db_encryption = DatabaseEncryption()

    return _db_encryption


def encrypt_field(plaintext: str) -> str:
    """Convenience function to encrypt a field.

    Args:
        plaintext: Plain text to encrypt

    Returns:
        Encrypted value
    """
    return get_db_encryption().encrypt_field(plaintext)


def decrypt_field(ciphertext: str) -> str:
    """Convenience function to decrypt a field.

    Args:
        ciphertext: Encrypted value

    Returns:
        Decrypted plain text
    """
    return get_db_encryption().decrypt_field(ciphertext)
