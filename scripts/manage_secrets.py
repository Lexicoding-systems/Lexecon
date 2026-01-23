#!/usr/bin/env python3
"""Secrets Management CLI.

Command-line tool for managing Lexecon secrets:
- Generate new secrets and keys
- Encrypt/decrypt .env files
- Verify secrets configuration
- Rotate RSA key passwords

Usage:
    python scripts/manage_secrets.py generate [--output DIR]
    python scripts/manage_secrets.py encrypt-env --input .env [--output .env.encrypted]
    python scripts/manage_secrets.py decrypt-env [--input .env.encrypted] [--output .env]
    python scripts/manage_secrets.py verify
    python scripts/manage_secrets.py rotate-rsa-password [--key-path PATH]
"""

import argparse
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from lexecon.security.db_encryption import DatabaseEncryption
from lexecon.security.secrets_manager import SecretsManager


def generate_secrets(output_dir: str = "./secrets"):
    """Generate all required secrets for Lexecon.

    Args:
        output_dir: Directory to write secret files
    """
    print("Generating Lexecon secrets...")
    print("=" * 60)

    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)

    secrets_to_generate = {
        "db_encryption_key.txt": DatabaseEncryption.generate_key(),
        "rsa_private_key_password.txt": SecretsManager.generate_secret(32),
        "session_secret_key.txt": SecretsManager.generate_secret(32),
        "mfa_encryption_key.txt": DatabaseEncryption.generate_key(),
        "master_key.txt": SecretsManager.generate_master_key(),
    }

    for filename, value in secrets_to_generate.items():
        filepath = output_path / filename
        with open(filepath, "w") as f:
            f.write(value)
        print(f"✓ Generated {filename}")

    print("=" * 60)
    print(f"\n✓ Secrets written to {output_dir}/")
    print("\nDocker Secrets Setup:")
    print("  1. Copy files to your secrets directory")
    print(f"  2. Update docker-compose.yml to reference files in {output_dir}/")
    print("\nEnvironment Variables Setup:")
    print("  1. Add to .env or export as environment variables:")
    for filename in secrets_to_generate:
        env_var = filename.replace(".txt", "").upper()
        print(f"     {env_var}=$(cat {output_dir}/{filename})")
    print("\nSecurity Note:")
    print("  • Keep these files secure and never commit to git")
    print("  • Add secrets/ directory to .gitignore")
    print("  • Rotate secrets regularly (every 90 days recommended)")


def encrypt_env(input_path: str, output_path: str = ".env.encrypted"):
    """Encrypt a .env file.

    Args:
        input_path: Path to plaintext .env file
        output_path: Path to write encrypted file
    """
    master_key = os.getenv("LEXECON_MASTER_KEY")
    if not master_key:
        print("Error: LEXECON_MASTER_KEY environment variable not set")
        print("\nGenerate a master key:")
        print("  python scripts/manage_secrets.py generate")
        print("\nThen set the environment variable:")
        print("  export LEXECON_MASTER_KEY=$(cat secrets/master_key.txt)")
        sys.exit(1)

    print(f"Encrypting {input_path} to {output_path}...")

    secrets_manager = SecretsManager(master_key=master_key)
    secrets_manager.encrypt_env_file(input_path, output_path)

    print(f"\n✓ Encrypted .env file created: {output_path}")
    print("\nUsage:")
    print("  1. Set LEXECON_MASTER_KEY environment variable")
    print("  2. SecretsManager will automatically load secrets from encrypted file")
    print("\nSecurity Note:")
    print(f"  • Delete plaintext {input_path} after verifying encrypted file works")
    print(f"  • Keep {output_path} in version control (safe with master key)")
    print("  • Never commit LEXECON_MASTER_KEY to git")


def decrypt_env(input_path: str = ".env.encrypted", output_path: str = ".env"):
    """Decrypt an encrypted .env file.

    Args:
        input_path: Path to encrypted file
        output_path: Path to write decrypted file
    """
    master_key = os.getenv("LEXECON_MASTER_KEY")
    if not master_key:
        print("Error: LEXECON_MASTER_KEY environment variable not set")
        sys.exit(1)

    print(f"Decrypting {input_path} to {output_path}...")

    secrets_manager = SecretsManager(master_key=master_key)
    secrets_manager.decrypt_env_file(input_path, output_path)

    print(f"\n✓ Decrypted .env file created: {output_path}")
    print(f"\nWarning: {output_path} contains plaintext secrets!")
    print("  • Do not commit to git")
    print("  • Delete after use in development")


def verify_secrets():
    """Verify secrets configuration."""
    print("Verifying Lexecon secrets configuration...")
    print("=" * 60)

    secrets_manager = SecretsManager()

    # Check required secrets
    required_secrets = [
        ("db_encryption_key", "Database encryption key"),
        ("rsa_private_key_password", "RSA private key password"),
        ("session_secret_key", "Session secret key"),
    ]

    optional_secrets = [
        ("mfa_encryption_key", "MFA encryption key"),
        ("master_key", "Master encryption key"),
    ]

    all_good = True

    print("\nRequired Secrets:")
    for secret_name, description in required_secrets:
        value = secrets_manager.get_secret(secret_name)
        if value:
            # Show only first 8 chars
            preview = value[:8] + "..." if len(value) > 8 else value
            print(f"  ✓ {description}: {preview}")
        else:
            print(f"  ✗ {description}: NOT FOUND")
            all_good = False

    print("\nOptional Secrets:")
    for secret_name, description in optional_secrets:
        value = secrets_manager.get_secret(secret_name)
        if value:
            preview = value[:8] + "..." if len(value) > 8 else value
            print(f"  ✓ {description}: {preview}")
        else:
            print(f"  ⊘ {description}: Not configured")

    # Check secret sources
    print("\nSecret Sources:")
    docker_secrets_dir = Path("/run/secrets")
    if docker_secrets_dir.exists():
        secrets_count = len(list(docker_secrets_dir.glob("*")))
        print(f"  • Docker Secrets: {secrets_count} files in /run/secrets/")
    else:
        print("  • Docker Secrets: Not available")

    env_encrypted = Path(".env.encrypted")
    if env_encrypted.exists():
        print(f"  • Encrypted .env: {env_encrypted} ({env_encrypted.stat().st_size} bytes)")
    else:
        print("  • Encrypted .env: Not found")

    print("\nEnvironment Variables:")
    env_vars = ["DB_ENCRYPTION_KEY", "RSA_KEY_PASSWORD", "SESSION_SECRET", "LEXECON_MASTER_KEY"]
    for var in env_vars:
        value = os.getenv(var)
        if value:
            preview = value[:8] + "..." if len(value) > 8 else value
            print(f"  • {var}: {preview}")
        else:
            print(f"  • {var}: Not set")

    print("\n" + "=" * 60)
    if all_good:
        print("✓ All required secrets are configured!")
    else:
        print("✗ Some required secrets are missing")
        print("\nTo generate secrets:")
        print("  python scripts/manage_secrets.py generate")
        sys.exit(1)


def rotate_rsa_password(key_path: str = "keys/private_key.pem"):
    """Rotate RSA private key password.

    Args:
        key_path: Path to RSA private key
    """
    print(f"Rotating RSA private key password for {key_path}...")
    print("\nThis feature requires the signature_service.py to be updated first.")
    print("After implementing encrypted key support, this will:")
    print("  1. Load existing key with old password")
    print("  2. Re-encrypt with new password")
    print("  3. Update secrets storage")
    print("\nNot yet implemented - coming in Phase 1D.")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Lexecon Secrets Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Generate command
    generate_parser = subparsers.add_parser("generate", help="Generate new secrets")
    generate_parser.add_argument(
        "--output",
        default="./secrets",
        help="Output directory for secret files (default: ./secrets)",
    )

    # Encrypt command
    encrypt_parser = subparsers.add_parser("encrypt-env", help="Encrypt .env file")
    encrypt_parser.add_argument(
        "--input",
        required=True,
        help="Path to plaintext .env file",
    )
    encrypt_parser.add_argument(
        "--output",
        default=".env.encrypted",
        help="Path to write encrypted file (default: .env.encrypted)",
    )

    # Decrypt command
    decrypt_parser = subparsers.add_parser("decrypt-env", help="Decrypt .env file")
    decrypt_parser.add_argument(
        "--input",
        default=".env.encrypted",
        help="Path to encrypted file (default: .env.encrypted)",
    )
    decrypt_parser.add_argument(
        "--output",
        default=".env",
        help="Path to write decrypted file (default: .env)",
    )

    # Verify command
    subparsers.add_parser("verify", help="Verify secrets configuration")

    # Rotate RSA password command
    rotate_parser = subparsers.add_parser(
        "rotate-rsa-password",
        help="Rotate RSA private key password",
    )
    rotate_parser.add_argument(
        "--key-path",
        default="keys/private_key.pem",
        help="Path to RSA private key (default: keys/private_key.pem)",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == "generate":
            generate_secrets(args.output)
        elif args.command == "encrypt-env":
            encrypt_env(args.input, args.output)
        elif args.command == "decrypt-env":
            decrypt_env(args.input, args.output)
        elif args.command == "verify":
            verify_secrets()
        elif args.command == "rotate-rsa-password":
            rotate_rsa_password(args.key_path)
        else:
            parser.print_help()
            sys.exit(1)

    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
