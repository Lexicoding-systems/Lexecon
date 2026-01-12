"""
Multi-Factor Authentication (MFA) Service.

Implements TOTP-based two-factor authentication using time-based one-time passwords.
Supports:
- TOTP secret generation and QR codes
- 6-digit code verification with time window tolerance
- Backup codes for account recovery
- MFA challenges for login flow
- Challenge expiration and cleanup

Uses pyotp for TOTP generation/verification and qrcode for QR code generation.
"""

import sqlite3
import secrets
import hashlib
import base64
import pyotp
import qrcode
import io
from typing import Tuple, List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from pathlib import Path


class MFAService:
    """
    Multi-factor authentication service using TOTP (Time-based One-Time Password).

    Integrates with existing auth_service database.
    """

    def __init__(self, db_path: str = "lexecon_auth.db", issuer: str = "Lexecon"):
        """
        Initialize MFA service.

        Args:
            db_path: Path to authentication database
            issuer: Issuer name for TOTP (shown in authenticator apps)
        """
        self.db_path = db_path
        self.issuer = issuer

    def generate_secret(self) -> str:
        """
        Generate a new TOTP secret.

        Returns:
            Base32-encoded secret (32 bytes / 52 characters)
        """
        # Generate 32 random bytes, encode as base32
        random_bytes = secrets.token_bytes(32)
        secret = base64.b32encode(random_bytes).decode('utf-8')
        return secret

    def generate_qr_code(self, username: str, secret: str) -> bytes:
        """
        Generate QR code for authenticator app setup.

        Args:
            username: Username to display in authenticator
            secret: TOTP secret (base32)

        Returns:
            PNG image bytes
        """
        # Create TOTP URI
        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(name=username, issuer_name=self.issuer)

        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to PNG bytes
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()

    def verify_totp(self, secret: str, token: str) -> bool:
        """
        Verify a TOTP token.

        Args:
            secret: TOTP secret (base32)
            token: 6-digit code from authenticator

        Returns:
            True if code is valid
        """
        if not token or not token.isdigit() or len(token) != 6:
            return False

        totp = pyotp.TOTP(secret)

        # Verify with 1 time window tolerance (±30 seconds)
        # This allows for slight clock drift and user delay
        return totp.verify(token, valid_window=1)

    def generate_backup_codes(self, count: int = 10) -> List[str]:
        """
        Generate backup recovery codes.

        Args:
            count: Number of codes to generate

        Returns:
            List of 8-character alphanumeric codes
        """
        codes = []
        for _ in range(count):
            # Generate 8-character code (uppercase letters and digits)
            code = ''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(8))
            codes.append(code)
        return codes

    def hash_backup_code(self, code: str) -> str:
        """
        Hash a backup code for storage.

        Uses PBKDF2-HMAC-SHA256 (same as passwords).

        Args:
            code: Plain backup code

        Returns:
            Hex-encoded hash
        """
        # Use a fixed salt for backup codes (they're already random)
        salt = b"lexecon-backup-code-salt"
        return hashlib.pbkdf2_hmac(
            'sha256',
            code.encode('utf-8'),
            salt,
            100000
        ).hex()

    def verify_backup_code(self, user_id: str, code: str) -> bool:
        """
        Verify a backup code and mark it as used.

        Args:
            user_id: User ID
            code: Backup code to verify

        Returns:
            True if code is valid and unused
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Get user's backup codes
            cursor.execute("""
                SELECT mfa_backup_codes
                FROM users
                WHERE user_id = ? AND mfa_enabled = 1
            """, (user_id,))

            row = cursor.fetchone()
            if not row or not row[0]:
                return False

            import json
            backup_codes = json.loads(row[0])

            # Hash provided code
            code_hash = self.hash_backup_code(code.upper())

            # Check if code exists and is unused
            for i, stored_code in enumerate(backup_codes):
                if stored_code['hash'] == code_hash and not stored_code.get('used', False):
                    # Mark as used
                    backup_codes[i]['used'] = True
                    backup_codes[i]['used_at'] = datetime.now(timezone.utc).isoformat()

                    # Update database
                    cursor.execute("""
                        UPDATE users
                        SET mfa_backup_codes = ?
                        WHERE user_id = ?
                    """, (json.dumps(backup_codes), user_id))

                    conn.commit()
                    return True

            return False

        finally:
            conn.close()

    def enable_mfa(self, user_id: str, secret: str, backup_codes: List[str]) -> bool:
        """
        Enable MFA for a user.

        Args:
            user_id: User ID
            secret: TOTP secret (will be encrypted)
            backup_codes: List of backup codes (will be hashed)

        Returns:
            True if enabled successfully
        """
        import json
        from lexecon.security.db_encryption import get_db_encryption

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Encrypt TOTP secret
            db_encryption = get_db_encryption()
            encrypted_secret = db_encryption.encrypt_field(secret)

            # Hash backup codes
            backup_code_data = [
                {
                    'hash': self.hash_backup_code(code),
                    'used': False
                }
                for code in backup_codes
            ]

            enrolled_at = datetime.now(timezone.utc).isoformat()

            cursor.execute("""
                UPDATE users
                SET mfa_enabled = 1,
                    mfa_secret = ?,
                    mfa_backup_codes = ?,
                    mfa_enrolled_at = ?
                WHERE user_id = ?
            """, (encrypted_secret, json.dumps(backup_code_data), enrolled_at, user_id))

            conn.commit()
            return cursor.rowcount > 0

        finally:
            conn.close()

    def disable_mfa(self, user_id: str) -> bool:
        """
        Disable MFA for a user.

        Args:
            user_id: User ID

        Returns:
            True if disabled successfully
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                UPDATE users
                SET mfa_enabled = 0,
                    mfa_secret = NULL,
                    mfa_backup_codes = NULL
                WHERE user_id = ?
            """, (user_id,))

            conn.commit()
            return cursor.rowcount > 0

        finally:
            conn.close()

    def create_mfa_challenge(
        self,
        user_id: str,
        session_token: str,
        ip_address: Optional[str] = None
    ) -> str:
        """
        Create an MFA challenge for login.

        Args:
            user_id: User ID
            session_token: Temporary pre-MFA session token
            ip_address: Client IP address

        Returns:
            Challenge ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            challenge_id = f"mfa_{secrets.token_hex(16)}"
            created_at = datetime.now(timezone.utc)
            expires_at = created_at + timedelta(minutes=5)

            cursor.execute("""
                INSERT INTO mfa_challenges (
                    challenge_id, user_id, session_token, created_at,
                    expires_at, ip_address, verified
                ) VALUES (?, ?, ?, ?, ?, ?, 0)
            """, (
                challenge_id,
                user_id,
                session_token,
                created_at.isoformat(),
                expires_at.isoformat(),
                ip_address
            ))

            conn.commit()
            return challenge_id

        finally:
            conn.close()

    def verify_mfa_challenge(
        self,
        challenge_id: str,
        totp_code: str
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Verify an MFA challenge with TOTP code.

        Args:
            challenge_id: Challenge ID
            totp_code: 6-digit TOTP code

        Returns:
            Tuple of (success, user_id, session_token)
        """
        from lexecon.security.db_encryption import get_db_encryption

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Get challenge
            cursor.execute("""
                SELECT c.user_id, c.session_token, c.expires_at, u.mfa_secret
                FROM mfa_challenges c
                JOIN users u ON c.user_id = u.user_id
                WHERE c.challenge_id = ? AND c.verified = 0
            """, (challenge_id,))

            row = cursor.fetchone()
            if not row:
                return False, None, None

            user_id, session_token, expires_at, encrypted_secret = row

            # Check expiration
            expires_dt = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            if datetime.now(timezone.utc) > expires_dt:
                return False, None, None

            # Decrypt TOTP secret
            db_encryption = get_db_encryption()
            secret = db_encryption.decrypt_field(encrypted_secret)

            # Verify TOTP code
            if not self.verify_totp(secret, totp_code):
                return False, None, None

            # Mark challenge as verified
            cursor.execute("""
                UPDATE mfa_challenges
                SET verified = 1
                WHERE challenge_id = ?
            """, (challenge_id,))

            conn.commit()
            return True, user_id, session_token

        finally:
            conn.close()

    def verify_mfa_challenge_with_backup(
        self,
        challenge_id: str,
        backup_code: str
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Verify an MFA challenge with backup code.

        Args:
            challenge_id: Challenge ID
            backup_code: Backup recovery code

        Returns:
            Tuple of (success, user_id, session_token)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Get challenge
            cursor.execute("""
                SELECT user_id, session_token, expires_at
                FROM mfa_challenges
                WHERE challenge_id = ? AND verified = 0
            """, (challenge_id,))

            row = cursor.fetchone()
            if not row:
                return False, None, None

            user_id, session_token, expires_at = row

            # Check expiration
            expires_dt = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            if datetime.now(timezone.utc) > expires_dt:
                return False, None, None

            # Verify backup code
            if not self.verify_backup_code(user_id, backup_code):
                return False, None, None

            # Mark challenge as verified
            cursor.execute("""
                UPDATE mfa_challenges
                SET verified = 1
                WHERE challenge_id = ?
            """, (challenge_id,))

            conn.commit()
            return True, user_id, session_token

        finally:
            conn.close()

    def cleanup_expired_challenges(self):
        """Delete expired MFA challenges (older than 10 minutes)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cutoff = datetime.now(timezone.utc) - timedelta(minutes=10)

            cursor.execute("""
                DELETE FROM mfa_challenges
                WHERE expires_at < ?
            """, (cutoff.isoformat(),))

            conn.commit()
            deleted_count = cursor.rowcount

            return deleted_count

        finally:
            conn.close()

    def get_mfa_status(self, user_id: str) -> Dict[str, Any]:
        """
        Get MFA status for a user.

        Args:
            user_id: User ID

        Returns:
            Dictionary with MFA status information
        """
        import json

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT mfa_enabled, mfa_enrolled_at, mfa_backup_codes
                FROM users
                WHERE user_id = ?
            """, (user_id,))

            row = cursor.fetchone()
            if not row:
                return {
                    "enabled": False,
                    "enrolled_at": None,
                    "backup_codes_remaining": 0
                }

            mfa_enabled, enrolled_at, backup_codes_json = row

            # Count remaining backup codes
            backup_codes_remaining = 0
            if backup_codes_json:
                backup_codes = json.loads(backup_codes_json)
                backup_codes_remaining = sum(
                    1 for code in backup_codes if not code.get('used', False)
                )

            return {
                "enabled": bool(mfa_enabled),
                "enrolled_at": enrolled_at,
                "backup_codes_remaining": backup_codes_remaining
            }

        finally:
            conn.close()


# Global instance
_mfa_service: Optional[MFAService] = None


def get_mfa_service() -> MFAService:
    """
    Get global MFA service instance.

    Returns:
        MFAService instance
    """
    global _mfa_service

    if _mfa_service is None:
        _mfa_service = MFAService()

    return _mfa_service
