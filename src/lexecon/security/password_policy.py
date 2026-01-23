"""Password Policy Enforcement.

Implements comprehensive password security policies including:
- Complexity requirements (length, character types)
- Password history (prevent reuse)
- Weak password detection
- Password expiration
- Sequential/repeated character detection

Configurable policies for different security requirements.
"""

import hashlib
import re
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple


class PasswordPolicy:
    """Configurable password policy enforcement.

    Validates passwords against complexity, history, and quality rules.
    Supports password expiration and forced password changes.
    """

    def __init__(
        self,
        min_length: int = 12,
        require_uppercase: bool = True,
        require_lowercase: bool = True,
        require_digits: bool = True,
        require_special: bool = True,
        special_chars: str = "!@#$%^&*()_+-=[]{}|;:,.<>?",
        max_age_days: Optional[int] = 90,  # None = no expiration
        history_count: int = 5,  # Remember last N passwords
        min_unique_chars: int = 8,  # Minimum unique characters
    ):
        """Initialize password policy.

        Args:
            min_length: Minimum password length
            require_uppercase: Require at least one uppercase letter
            require_lowercase: Require at least one lowercase letter
            require_digits: Require at least one digit
            require_special: Require at least one special character
            special_chars: Allowed special characters
            max_age_days: Password expiration in days (None = no expiration)
            history_count: Number of previous passwords to remember
            min_unique_chars: Minimum number of unique characters
        """
        self.min_length = min_length
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_digits = require_digits
        self.require_special = require_special
        self.special_chars = special_chars
        self.max_age_days = max_age_days
        self.history_count = history_count
        self.min_unique_chars = min_unique_chars

        # Load common weak passwords
        self.weak_passwords = self._load_weak_passwords()

    def validate_password(self, password: str) -> Tuple[bool, List[str]]:
        """Validate password against all policy rules.

        Args:
            password: Password to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Check length
        if len(password) < self.min_length:
            errors.append(f"Password must be at least {self.min_length} characters long")

        # Check uppercase
        if self.require_uppercase and not re.search(r"[A-Z]", password):
            errors.append("Password must contain at least one uppercase letter (A-Z)")

        # Check lowercase
        if self.require_lowercase and not re.search(r"[a-z]", password):
            errors.append("Password must contain at least one lowercase letter (a-z)")

        # Check digits
        if self.require_digits and not re.search(r"\d", password):
            errors.append("Password must contain at least one digit (0-9)")

        # Check special characters
        if self.require_special and not any(c in self.special_chars for c in password):
            errors.append(f"Password must contain at least one special character ({self.special_chars})")

        # Check minimum unique characters
        unique_chars = len(set(password))
        if unique_chars < self.min_unique_chars:
            errors.append(f"Password must contain at least {self.min_unique_chars} unique characters")

        # Check against common weak passwords
        if password.lower() in self.weak_passwords:
            errors.append("Password is too common and easily guessable")

        # Check for keyboard patterns
        if self._has_keyboard_pattern(password):
            errors.append("Password contains keyboard patterns (e.g., 'qwerty', 'asdf')")

        # Check for sequential characters
        if self._has_sequential_chars(password):
            errors.append("Password contains sequential characters (e.g., '123', 'abc')")

        # Check for repeated characters
        if self._has_repeated_chars(password):
            errors.append("Password has too many repeated characters (e.g., 'aaa', '111')")

        # Check for dictionary words (basic check)
        if self._contains_dictionary_word(password):
            errors.append("Password contains common dictionary words")

        return len(errors) == 0, errors

    def _load_weak_passwords(self) -> set:
        """Load list of common weak passwords.

        Returns:
            Set of weak passwords (lowercase)
        """
        # Top 100 most common passwords (from various breach databases)
        return {
            "password", "123456", "123456789", "12345678", "12345", "1234567",
            "password1", "123123", "1234567890", "000000", "abc123", "qwerty",
            "iloveyou", "welcome", "monkey", "dragon", "master", "sunshine",
            "princess", "admin", "letmein", "login", "passw0rd", "qwerty123",
            "solo", "pass", "test", "guest", "123qwe", "zxcvbnm", "football",
            "baseball", "superman", "batman", "trustno1", "111111", "666666",
            "123321", "654321", "555555", "lovely", "7777777", "888888",
            "adobe123", "photoshop", "1234", "shadow", "12345678910",
            "password123", "qwertyuiop", "asdfghjkl", "zxcvbn", "michael",
            "jennifer", "jordan", "michelle", "thomas", "hunter", "ranger",
            "buster", "soccer", "harley", "hockey", "tennis", "mercedes",
            "mustang", "maverick", "cookie", "bigdog", "access", "master1",
            "changeme", "demo", "temp", "temporary", "default", "admin123",
            "root", "toor", "administrator", "user", "test123", "welcome1",
            "Password1!", "P@ssw0rd", "P@ssword", "Passw0rd!", "Password1",
        }

    def _has_keyboard_pattern(self, password: str) -> bool:
        """Check for common keyboard patterns.

        Args:
            password: Password to check

        Returns:
            True if contains keyboard pattern
        """
        keyboard_patterns = [
            "qwerty", "asdfgh", "zxcvbn", "qwertyuiop", "asdfghjkl", "zxcvbnm",
            "1qaz2wsx", "!qaz@wsx", "1234qwer", "qazwsx", "qweasd", "qweasdzxc",
        ]

        password_lower = password.lower()
        return any(pattern in password_lower for pattern in keyboard_patterns)

    def _has_sequential_chars(self, password: str, length: int = 3) -> bool:
        """Check for sequential characters.

        Args:
            password: Password to check
            length: Minimum sequence length to detect

        Returns:
            True if contains sequential characters
        """
        password_lower = password.lower()

        for i in range(len(password_lower) - length + 1):
            substr = password_lower[i:i+length]

            # Check numeric sequences (123, 321, 111)
            if substr.isdigit():
                digits = [int(d) for d in substr]
                # Ascending (123)
                if all(digits[j+1] - digits[j] == 1 for j in range(len(digits)-1)):
                    return True
                # Descending (321)
                if all(digits[j] - digits[j+1] == 1 for j in range(len(digits)-1)):
                    return True

            # Check alphabetic sequences (abc, zyx)
            if substr.isalpha():
                chars = [ord(c) for c in substr]
                # Ascending (abc)
                if all(chars[j+1] - chars[j] == 1 for j in range(len(chars)-1)):
                    return True
                # Descending (zyx)
                if all(chars[j] - chars[j+1] == 1 for j in range(len(chars)-1)):
                    return True

        return False

    def _has_repeated_chars(self, password: str, max_repeat: int = 3) -> bool:
        """Check for repeated characters.

        Args:
            password: Password to check
            max_repeat: Maximum allowed repetitions

        Returns:
            True if has too many repeated characters
        """
        return any(len(set(password[i:i + max_repeat])) == 1 for i in range(len(password) - max_repeat + 1))

    def _contains_dictionary_word(self, password: str) -> bool:
        """Check if password contains common dictionary words.

        Args:
            password: Password to check

        Returns:
            True if contains dictionary word
        """
        # Common dictionary words (basic list)
        common_words = {
            "password", "welcome", "admin", "user", "login", "access",
            "system", "computer", "internet", "security", "database",
            "server", "network", "manager", "account", "company", "business",
            "hello", "world", "test", "demo", "sample", "example",
        }

        password_lower = password.lower()

        # Check if password is a dictionary word
        if password_lower in common_words:
            return True

        # Check if password contains dictionary words
        return any(len(word) >= 5 and word in password_lower for word in common_words)

    def check_password_history(
        self,
        new_password: str,
        salt: str,
        password_history: List[str],
    ) -> bool:
        """Check if password was used recently.

        Args:
            new_password: New password to check
            salt: Salt for hashing
            password_history: List of previous password hashes

        Returns:
            True if password is allowed (not in history)
        """
        new_hash = self._hash_password(new_password, salt)
        return new_hash not in password_history

    def _hash_password(self, password: str, salt: str) -> str:
        """Hash password using PBKDF2-HMAC-SHA256.

        Uses same algorithm as AuthService for consistency.

        Args:
            password: Password to hash
            salt: Salt for hashing

        Returns:
            Hex-encoded password hash
        """
        return hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            100000,  # Same iteration count as AuthService
        ).hex()

    def is_password_expired(self, last_changed: str) -> bool:
        """Check if password has expired.

        Args:
            last_changed: ISO 8601 timestamp of last password change

        Returns:
            True if password is expired
        """
        if not self.max_age_days:
            return False

        try:
            last_changed_dt = datetime.fromisoformat(last_changed.replace("Z", "+00:00"))
            age = datetime.now(timezone.utc) - last_changed_dt
            return age.days > self.max_age_days
        except (ValueError, AttributeError):
            # If timestamp is invalid, consider expired for safety
            return True

    def days_until_expiration(self, last_changed: str) -> Optional[int]:
        """Calculate days until password expires.

        Args:
            last_changed: ISO 8601 timestamp of last password change

        Returns:
            Days remaining (None if no expiration policy)
        """
        if not self.max_age_days:
            return None

        try:
            last_changed_dt = datetime.fromisoformat(last_changed.replace("Z", "+00:00"))
            expires_at = last_changed_dt + timedelta(days=self.max_age_days)
            remaining = expires_at - datetime.now(timezone.utc)
            return max(0, remaining.days)
        except (ValueError, AttributeError):
            return 0

    def calculate_password_strength(self, password: str) -> dict:
        """Calculate password strength score and feedback.

        Args:
            password: Password to analyze

        Returns:
            Dictionary with score (0-100) and feedback
        """
        score = 0
        feedback = []

        # Length score (max 30 points)
        if len(password) >= self.min_length:
            score += 30
            feedback.append("Good length")
        elif len(password) >= 8:
            score += 15
            feedback.append("Length could be longer")

        # Character diversity score (max 40 points)
        has_upper = bool(re.search(r"[A-Z]", password))
        has_lower = bool(re.search(r"[a-z]", password))
        has_digit = bool(re.search(r"\d", password))
        has_special = any(c in self.special_chars for c in password)

        char_types = sum([has_upper, has_lower, has_digit, has_special])
        score += char_types * 10
        if char_types == 4:
            feedback.append("Excellent character diversity")
        elif char_types >= 3:
            feedback.append("Good character mix")

        # Uniqueness score (max 15 points)
        unique_ratio = len(set(password)) / len(password) if password else 0
        score += int(unique_ratio * 15)
        if unique_ratio >= 0.8:
            feedback.append("High character uniqueness")

        # Penalty for weak patterns
        if password.lower() in self.weak_passwords:
            score -= 50
            feedback.append("⚠️ Common password")

        if self._has_sequential_chars(password):
            score -= 10
            feedback.append("⚠️ Contains sequences")

        if self._has_repeated_chars(password):
            score -= 10
            feedback.append("⚠️ Too many repeated characters")

        # Bonus for length beyond minimum (max 15 points)
        if len(password) > self.min_length:
            bonus = min(15, (len(password) - self.min_length) * 2)
            score += bonus

        # Clamp score to 0-100
        score = max(0, min(100, score))

        # Determine strength label
        if score >= 80:
            strength = "Strong"
        elif score >= 60:
            strength = "Good"
        elif score >= 40:
            strength = "Fair"
        else:
            strength = "Weak"

        return {
            "score": score,
            "strength": strength,
            "feedback": feedback,
        }


# Default policy instance
_default_policy: Optional[PasswordPolicy] = None


def get_default_policy() -> PasswordPolicy:
    """Get default password policy instance.

    Returns:
        Default PasswordPolicy
    """
    global _default_policy

    if _default_policy is None:
        _default_policy = PasswordPolicy()

    return _default_policy
