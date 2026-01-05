#!/usr/bin/env python3
"""
Setup script for Lexecon enterprise security features.

Creates:
- Authentication database with initial users
- Export audit logging database
- RSA key pair for digital signatures
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from lexecon.security.auth_service import AuthService, Role
from lexecon.security.audit_service import AuditService
from lexecon.security.signature_service import SignatureService


def main():
    print("=" * 70)
    print("LEXECON ENTERPRISE SECURITY SETUP")
    print("=" * 70)
    print()

    # Initialize services
    print("Initializing security services...")
    auth = AuthService("lexecon_auth.db")
    audit = AuditService("lexecon_export_audit.db")
    signature = SignatureService("lexecon_keys")

    print("   [OK] Authentication service initialized")
    print("   [OK] Export audit logging initialized")
    print("   [OK] Digital signature service initialized")
    print(f"   [OK] RSA key pair generated (fingerprint: {signature.get_public_key_fingerprint()[:16]}...)")
    print()

    # Create admin user
    print("Creating initial users...")
    try:
        admin = auth.create_user(
            username="admin",
            email="admin@lexecon.local",
            password="ChangeMe123!",  # MUST CHANGE IN PRODUCTION
            role=Role.ADMIN,
            full_name="System Administrator"
        )
        print(f"   [OK] Admin user created")
        print(f"        Username: {admin.username}")
        print(f"        Email: {admin.email}")
        print(f"        Role: {admin.role.value}")
        print(f"        ℹ Password: ChangeMe123! (CHANGE IMMEDIATELY)")
    except ValueError as e:
        print(f"   [SKIP] Admin user already exists or error: {e}")

    print()

    # Create test auditor
    try:
        auditor = auth.create_user(
            username="auditor",
            email="auditor@lexecon.local",
            password="TestAuditor123!",
            role=Role.AUDITOR,
            full_name="Test Auditor"
        )
        print(f"   [OK] Auditor user created")
        print(f"        Username: {auditor.username}")
        print(f"        Email: {auditor.email}")
        print(f"        Role: {auditor.role.value}")
        print(f"        Password: TestAuditor123!")
    except ValueError as e:
        print(f"   [SKIP] Auditor user already exists or error: {e}")

    print()

    # Create test compliance officer
    try:
        officer = auth.create_user(
            username="compliance",
            email="compliance@lexecon.local",
            password="TestCompliance123!",
            role=Role.COMPLIANCE_OFFICER,
            full_name="Compliance Officer"
        )
        print(f"   [OK] Compliance Officer created")
        print(f"        Username: {officer.username}")
        print(f"        Email: {officer.email}")
        print(f"        Role: {officer.role.value}")
        print(f"        Password: TestCompliance123!")
    except ValueError as e:
        print(f"   [SKIP] Compliance Officer already exists or error: {e}")

    print()
    print("=" * 70)
    print("ENTERPRISE SECURITY SETUP COMPLETE")
    print("=" * 70)
    print()
    print("Files created:")
    print("   - lexecon_auth.db (user database)")
    print("   - lexecon_export_audit.db (export audit log)")
    print("   - lexecon_keys/private_key.pem (RSA private key)")
    print("   - lexecon_keys/public_key.pem (RSA public key)")
    print()
    print("Default Users:")
    print("   1. admin / ChangeMe123! (ADMIN)")
    print("   2. auditor / TestAuditor123! (AUDITOR)")
    print("   3. compliance / TestCompliance123! (COMPLIANCE_OFFICER)")
    print()
    print("ℹ SECURITY NOTICE:")
    print("   - Change the admin password immediately")
    print("   - These are TEST credentials for development only")
    print("   - In production, use strong passwords and enable MFA")
    print("   - Protect the private key file (lexecon_keys/private_key.pem)")
    print()
    print("Next steps:")
    print("   1. Start the server: cd src && python3 -m lexecon.api.server")
    print("   2. Login at: http://localhost:8000/login")
    print("   3. Access dashboard: http://localhost:8000/dashboard")
    print()


if __name__ == "__main__":
    main()
