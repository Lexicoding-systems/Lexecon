"""Secrets Management System.

Provides secure storage and retrieval of secrets with multiple backend support:
1. Docker Secrets (production) - /run/secrets/*
2. Encrypted .env files (development) - .env.encrypted
3. Environment variables (Railway, fallback)

Priority order: Docker Secrets > Encrypted .env > Environment variables

Features:
- Transparent secret loading from multiple sources
- Fernet symmetric encryption for .env files
- Master key-based encryption/decryption
- Automatic source detection
"""

import base64
import json
import os
from pathlib import Path
from typing import Dict, Optional

from cryptography.fernet import Fernet


class SecretsManager:
    """Secure secrets management with multiple backend support.

    Priority order for secret retrieval:
    1. Docker Secrets (/run/secrets/*)
    2. Encrypted .env file (development)
    3. Environment variables (Railway, fallback)
    """

    def __init__(
        self,
        secrets_dir: str = "/run/secrets",
        env_encrypted_path: Optional[str] = None,
        master_key: Optional[str] = None,
    ):
        """Initialize secrets manager.

        Args:
            secrets_dir: Directory for Docker secrets
            env_encrypted_path: Path to encrypted .env file
            master_key: Master encryption key (base64-encoded)
        """
        self.secrets_dir = Path(secrets_dir)
        self.env_encrypted_path = Path(env_encrypted_path or ".env.encrypted")
        self.master_key = master_key or os.getenv("LEXECON_MASTER_KEY")

        # Cache for loaded secrets
        self._cache: Dict[str, str] = {}

        # Load encrypted env file if it exists
        if self.env_encrypted_path.exists() and self.master_key:
            self._load_encrypted_env()

    def get_secret(self, secret_name: str, default: Optional[str] = None) -> Optional[str]:
        """Get secret value from available sources.

        Priority:
        1. Docker Secrets file
        2. Encrypted .env cache
        3. Environment variable

        Args:
            secret_name: Name of the secret
            default: Default value if secret not found

        Returns:
            Secret value or default
        """
        # Check cache first
        if secret_name in self._cache:
            return self._cache[secret_name]

        # Try Docker Secrets
        secret_file = self.secrets_dir / secret_name
        if secret_file.exists() and secret_file.is_file():
            try:
                with open(secret_file) as f:
                    value = f.read().strip()
                    self._cache[secret_name] = value
                    return value
            except Exception as e:
                print(f"Warning: Failed to read Docker secret {secret_name}: {e}")

        # Try environment variable with _FILE suffix (Docker Secrets convention)
        env_file_var = f"{secret_name.upper()}_FILE"
        file_path = os.getenv(env_file_var)
        if file_path and os.path.exists(file_path):
            try:
                with open(file_path) as f:
                    value = f.read().strip()
                    self._cache[secret_name] = value
                    return value
            except Exception as e:
                print(f"Warning: Failed to read secret from {file_path}: {e}")

        # Try direct environment variable
        env_var = secret_name.upper()
        value = os.getenv(env_var)
        if value:
            self._cache[secret_name] = value
            return value

        # Return default
        return default

    def _load_encrypted_env(self) -> None:
        """Load secrets from encrypted .env file into cache."""
        if not self.master_key:
            return

        try:
            fernet = self._get_fernet()

            with open(self.env_encrypted_path, "rb") as f:
                encrypted_data = f.read()

            decrypted_data = fernet.decrypt(encrypted_data)
            secrets = json.loads(decrypted_data.decode("utf-8"))

            # Load into cache
            self._cache.update(secrets)

        except Exception as e:
            print(f"Warning: Failed to load encrypted .env file: {e}")

    def _get_fernet(self) -> Fernet:
        """Get Fernet cipher instance.

        Returns:
            Fernet cipher

        Raises:
            ValueError: If master key is invalid
        """
        if not self.master_key:
            raise ValueError("Master key not configured")

        # Ensure key is properly formatted (32 bytes, base64-encoded)
        try:
            # If key is hex string, convert to bytes and base64 encode
            if len(self.master_key) == 64:
                key_bytes = bytes.fromhex(self.master_key)
                key_b64 = base64.urlsafe_b64encode(key_bytes)
            else:
                # Assume it's already base64
                key_b64 = self.master_key.encode("utf-8")

            return Fernet(key_b64)
        except Exception as e:
            raise ValueError(f"Invalid master key format: {e}")

    def encrypt_env_file(self, env_path: str, output_path: Optional[str] = None):
        """Encrypt a .env file.

        Args:
            env_path: Path to plaintext .env file
            output_path: Path to write encrypted file (default: .env.encrypted)

        Raises:
            ValueError: If master key not configured
        """
        if not self.master_key:
            raise ValueError("Master key required for encryption")

        output_path = output_path or str(self.env_encrypted_path)

        # Parse .env file
        secrets = {}
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    # Remove quotes if present
                    value = value.strip('"').strip("'")
                    secrets[key] = value

        # Encrypt
        fernet = self._get_fernet()
        json_data = json.dumps(secrets).encode("utf-8")
        encrypted_data = fernet.encrypt(json_data)

        # Write encrypted file
        with open(output_path, "wb") as f:
            f.write(encrypted_data)

        print(f"✓ Encrypted {len(secrets)} secrets to {output_path}")

    def decrypt_env_file(self, encrypted_path: Optional[str] = None, output_path: str = ".env"):
        """Decrypt an encrypted .env file.

        Args:
            encrypted_path: Path to encrypted file (default: .env.encrypted)
            output_path: Path to write decrypted file (default: .env)

        Raises:
            ValueError: If master key not configured
        """
        if not self.master_key:
            raise ValueError("Master key required for decryption")

        encrypted_path = encrypted_path or str(self.env_encrypted_path)

        # Decrypt
        fernet = self._get_fernet()

        with open(encrypted_path, "rb") as f:
            encrypted_data = f.read()

        decrypted_data = fernet.decrypt(encrypted_data)
        secrets = json.loads(decrypted_data.decode("utf-8"))

        # Write .env file
        with open(output_path, "w") as f:
            for key, value in secrets.items():
                f.write(f'{key}="{value}"\n')

        print(f"✓ Decrypted {len(secrets)} secrets to {output_path}")

    @staticmethod
    def generate_master_key() -> str:
        """Generate a new master encryption key.

        Returns:
            32-byte hex-encoded key
        """
        key = Fernet.generate_key()
        # Convert base64 to hex for easier storage
        key_bytes = base64.urlsafe_b64decode(key)
        return key_bytes.hex()

    @staticmethod
    def generate_secret(length: int = 32) -> str:
        """Generate a random secret.

        Args:
            length: Length in bytes

        Returns:
            Hex-encoded random secret
        """
        import secrets
        return secrets.token_hex(length)


# Global secrets manager instance
_secrets_manager: Optional[SecretsManager] = None


def get_secrets_manager() -> SecretsManager:
    """Get global secrets manager instance.

    Returns:
        SecretsManager instance
    """
    global _secrets_manager

    if _secrets_manager is None:
        _secrets_manager = SecretsManager()

    return _secrets_manager


def get_secret(secret_name: str, default: Optional[str] = None) -> Optional[str]:
    """Convenience function to get a secret.

    Args:
        secret_name: Name of the secret
        default: Default value if not found

    Returns:
        Secret value or default
    """
    return get_secrets_manager().get_secret(secret_name, default)
