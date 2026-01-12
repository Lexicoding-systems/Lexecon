#!/usr/bin/env python3
"""
Quick Authentication System Test.

Focused tests without heavy API calls to avoid timeouts.
"""

import sys
import sqlite3

GREEN = "\033[92m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"

def print_test(name: str, passed: bool, details: str = ""):
    status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
    print(f"{status} {name}")
    if details:
        print(f"       {details}")
    return passed

def print_section(title: str):
    print(f"\n{BLUE}{'=' * 70}{RESET}")
    print(f"{BLUE}{title}{RESET}")
    print(f"{BLUE}{'=' * 70}{RESET}")

results = []

# Test imports
print_section("Module Imports")

try:
    from lexecon.security.auth_service import AuthService
    results.append(print_test("AuthService imports", True))
except Exception as e:
    results.append(print_test("AuthService imports", False, str(e)))

try:
    from lexecon.security.password_policy import PasswordPolicy
    results.append(print_test("PasswordPolicy imports", True))
except Exception as e:
    results.append(print_test("PasswordPolicy imports", False, str(e)))

try:
    from lexecon.security.secrets_manager import SecretsManager
    results.append(print_test("SecretsManager imports", True))
except Exception as e:
    results.append(print_test("SecretsManager imports", False, str(e)))

try:
    from lexecon.security.db_encryption import DatabaseEncryption
    results.append(print_test("DatabaseEncryption imports", True))
except Exception as e:
    results.append(print_test("DatabaseEncryption imports", False, str(e)))

try:
    from lexecon.security.mfa_service import MFAService
    results.append(print_test("MFAService imports", True))
except Exception as e:
    results.append(print_test("MFAService imports", False, str(e)))

try:
    from lexecon.security.oidc_service import OIDCService
    results.append(print_test("OIDCService imports", True))
except Exception as e:
    results.append(print_test("OIDCService imports", False, str(e)))

try:
    from lexecon.security.rate_limiter import RateLimiter
    results.append(print_test("RateLimiter imports", True))
except Exception as e:
    results.append(print_test("RateLimiter imports", False, str(e)))

try:
    from lexecon.security.security_headers import SecurityHeadersMiddleware
    results.append(print_test("SecurityHeadersMiddleware imports", True))
except Exception as e:
    results.append(print_test("SecurityHeadersMiddleware imports", False, str(e)))

# Test password policy functionality
print_section("Password Policy Functionality")

try:
    from lexecon.security.password_policy import PasswordPolicy
    policy = PasswordPolicy()

    # Test weak password rejection
    valid, errors = policy.validate_password("password")
    results.append(print_test("Weak password rejected", not valid, f"{len(errors)} errors"))

    # Test strong password acceptance
    valid, errors = policy.validate_password("MySecureP@ssw0rd123!")
    results.append(print_test("Strong password accepted", valid, "No errors"))

    # Test password strength calculation
    strength = policy.calculate_password_strength("MySecureP@ssw0rd123!")
    results.append(print_test("Password strength calculation", strength['score'] > 70, f"Score: {strength['score']}"))

except Exception as e:
    results.append(print_test("Password policy functionality", False, str(e)))

# Test MFA functionality
print_section("MFA Functionality")

try:
    from lexecon.security.mfa_service import MFAService
    mfa = MFAService()

    # Generate secret
    secret = mfa.generate_secret()
    results.append(print_test("TOTP secret generation", len(secret) > 0, f"{len(secret)} chars"))

    # Generate QR code
    qr = mfa.generate_qr_code("testuser", secret)
    results.append(print_test("QR code generation", len(qr) > 0, f"{len(qr)} bytes"))

    # Generate backup codes
    codes = mfa.generate_backup_codes(10)
    results.append(print_test("Backup codes generation", len(codes) == 10, f"{len(codes)} codes"))

    # Test TOTP verification
    valid = mfa.verify_totp(secret, "000000")
    results.append(print_test("TOTP verification (invalid)", not valid, "Correctly rejected"))

except Exception as e:
    results.append(print_test("MFA functionality", False, str(e)))

# Test secrets management
print_section("Secrets Management")

try:
    from lexecon.security.secrets_manager import SecretsManager
    sm = SecretsManager()

    # Test key generation
    key = SecretsManager.generate_master_key()
    results.append(print_test("Master key generation", len(key) == 64, f"{len(key)} chars"))

    secret = SecretsManager.generate_secret(32)
    results.append(print_test("Secret generation", len(secret) == 64, f"{len(secret)} chars"))

except Exception as e:
    results.append(print_test("Secrets management", False, str(e)))

try:
    from lexecon.security.db_encryption import DatabaseEncryption

    # Test DB encryption key generation
    key = DatabaseEncryption.generate_key()
    results.append(print_test("DB encryption key generation", len(key) == 64, f"{len(key)} chars"))

except Exception as e:
    results.append(print_test("DB encryption", False, str(e)))

# Test database schema
print_section("Database Schema")

try:
    conn = sqlite3.connect("lexecon_auth.db")
    cursor = conn.cursor()

    # Check tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = {row[0] for row in cursor.fetchall()}

    required_tables = {
        "users", "sessions", "login_attempts", "password_history",
        "mfa_challenges", "oidc_states", "oidc_users"
    }

    for table in required_tables:
        results.append(print_test(f"Table '{table}'", table in tables))

    # Check users table columns
    cursor.execute("PRAGMA table_info(users)")
    columns = {row[1] for row in cursor.fetchall()}

    required_columns = {
        "user_id", "username", "email", "password_hash", "role",
        "password_changed_at", "password_expires_at", "force_password_change",
        "mfa_enabled", "mfa_secret", "mfa_backup_codes", "mfa_enrolled_at"
    }

    missing_columns = required_columns - columns
    results.append(print_test(
        "Users table has all columns",
        len(missing_columns) == 0,
        f"Missing: {missing_columns}" if missing_columns else "All present"
    ))

    # Check indexes
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
    indexes = {row[0] for row in cursor.fetchall() if row[0]}

    expected_indexes = {
        "idx_password_history_user",
        "idx_mfa_challenges_expires",
        "idx_oidc_users_lookup"
    }

    for index in expected_indexes:
        results.append(print_test(f"Index '{index}'", index in indexes))

    conn.close()

except Exception as e:
    results.append(print_test("Database schema", False, str(e)))

# Test rate limiter
print_section("Rate Limiter")

try:
    from lexecon.security.rate_limiter import RateLimiter, TokenBucket

    rl = RateLimiter()
    results.append(print_test("RateLimiter initialization", True))

    # Test token bucket
    bucket = TokenBucket(capacity=5, refill_rate=1.0)
    results.append(print_test("TokenBucket initialization", True))

    # Consume tokens
    consumed = bucket.consume(3)
    results.append(print_test("Token consumption", consumed, "3 tokens consumed"))

except Exception as e:
    results.append(print_test("Rate limiter", False, str(e)))

# Test OIDC service
print_section("OIDC OAuth Service")

try:
    from lexecon.security.oidc_service import OIDCService, OIDCProvider

    oidc = OIDCService()
    results.append(print_test("OIDCService initialization", True))

    # Test provider registration
    provider = oidc.register_provider(
        provider_name="test",
        discovery_url="https://accounts.google.com/.well-known/openid-configuration",
        client_id="test-client",
        client_secret="test-secret"
    )
    results.append(print_test("OIDC provider registration", provider is not None))

    # Test provider listing
    providers = oidc.list_providers()
    results.append(print_test("OIDC provider listing", len(providers) >= 1, f"{len(providers)} providers"))

except Exception as e:
    results.append(print_test("OIDC OAuth service", False, str(e)))

# Print summary
print(f"\n{BLUE}{'=' * 70}{RESET}")
print(f"{BLUE}Test Summary{RESET}")
print(f"{BLUE}{'=' * 70}{RESET}\n")

total = len(results)
passed = sum(results)
failed = total - passed

print(f"Total Tests: {total}")
print(f"{GREEN}Passed: {passed}{RESET}")
print(f"{RED}Failed: {failed}{RESET}")
print(f"\nSuccess Rate: {passed/total*100:.1f}%")

if failed == 0:
    print(f"\n{GREEN}🎉 ALL TESTS PASSED!{RESET}\n")
    sys.exit(0)
else:
    print(f"\n{RED}⚠️  {failed} test(s) failed.{RESET}\n")
    sys.exit(1)
