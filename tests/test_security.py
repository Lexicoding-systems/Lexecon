"""
Tests for security services.

Focuses on critical security functionality including authentication,
digital signatures, and audit logging.
"""

import os
import shutil
import tempfile

import pytest

from lexecon.security.auth_service import AuthService, Role
from lexecon.security.signature_service import SignatureService


class TestAuthService:
    """Tests for AuthService."""

    @pytest.fixture
    def auth_service(self):
        """Create auth service with temp database."""
        fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        service = AuthService(db_path=db_path)
        yield service
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)

    def test_create_user(self, auth_service):
        """Test user creation."""
        user = auth_service.create_user(
            username="testuser",
            email="test@example.com",
            password="SecurePass123!",
            role=Role.AUDITOR,
            full_name="Test User",
        )

        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == Role.AUDITOR
        assert user.full_name == "Test User"
        assert user.is_active is True
        assert user.failed_login_attempts == 0

    def test_list_users(self, auth_service):
        """Test listing all users."""
        auth_service.create_user(
            username="user1",
            email="user1@example.com",
            password="Pass123!",
            role=Role.VIEWER,
            full_name="User One",
        )
        auth_service.create_user(
            username="user2",
            email="user2@example.com",
            password="Pass123!",
            role=Role.AUDITOR,
            full_name="User Two",
        )

        users = auth_service.list_users()

        assert len(users) == 2
        assert any(u.username == "user1" for u in users)
        assert any(u.username == "user2" for u in users)

    def test_authenticate_success(self, auth_service):
        """Test successful authentication."""
        auth_service.create_user(
            username="authuser",
            email="auth@example.com",
            password="ValidPass123!",
            role=Role.VIEWER,
            full_name="Auth User",
        )

        user, error = auth_service.authenticate("authuser", "ValidPass123!")

        assert user is not None
        assert error is None
        assert user.username == "authuser"

    def test_authenticate_wrong_password(self, auth_service):
        """Test authentication with wrong password."""
        auth_service.create_user(
            username="authuser",
            email="auth@example.com",
            password="ValidPass123!",
            role=Role.VIEWER,
            full_name="Auth User",
        )

        user, error = auth_service.authenticate("authuser", "WrongPassword!")

        assert user is None
        assert error is not None
        assert "password" in error.lower()

    def test_authenticate_nonexistent_user(self, auth_service):
        """Test authentication with non-existent user."""
        user, error = auth_service.authenticate("nonexistent", "SomePassword")

        assert user is None
        assert error is not None

    def test_create_session(self, auth_service):
        """Test session creation."""
        user = auth_service.create_user(
            username="sessionuser",
            email="session@example.com",
            password="Pass123!",
            role=Role.AUDITOR,
            full_name="Session User",
        )

        session = auth_service.create_session(
            user=user,
            ip_address="192.168.1.1",
        )

        assert session is not None
        assert session.username == "sessionuser"
        assert session.role == Role.AUDITOR

    def test_validate_session_valid(self, auth_service):
        """Test validating a valid session."""
        user = auth_service.create_user(
            username="sessuser",
            email="sess@example.com",
            password="Pass123!",
            role=Role.VIEWER,
            full_name="Sess User",
        )

        session = auth_service.create_session(user=user)

        validated, error = auth_service.validate_session(session.session_id)

        assert validated is not None
        assert error is None
        assert validated.session_id == session.session_id

    def test_validate_session_invalid(self, auth_service):
        """Test validating an invalid session."""
        validated, error = auth_service.validate_session("invalid_session_id")

        assert validated is None
        assert error is not None

    def test_revoke_session(self, auth_service):
        """Test revoking a session."""
        user = auth_service.create_user(
            username="revokeuser",
            email="revoke@example.com",
            password="Pass123!",
            role=Role.VIEWER,
            full_name="Revoke User",
        )

        session = auth_service.create_session(user=user)

        # Revoke session
        auth_service.revoke_session(session.session_id)

        # Session should no longer be valid
        validated, _error = auth_service.validate_session(session.session_id)
        assert validated is None

    def test_has_permission(self, auth_service):
        """Test permission checking."""
        from lexecon.security.auth_service import Permission

        # Admin should have export permission
        assert auth_service.has_permission(Role.ADMIN, Permission.EXPORT_DATA) is True

        # Viewer should not have export permission
        assert auth_service.has_permission(Role.VIEWER, Permission.EXPORT_DATA) is False

    def test_get_user_by_id(self, auth_service):
        """Test getting user by ID."""
        user = auth_service.create_user(
            username="getuser",
            email="get@example.com",
            password="Pass123!",
            role=Role.AUDITOR,
            full_name="Get User",
        )

        retrieved = auth_service.get_user_by_id(user.user_id)

        assert retrieved is not None
        assert retrieved.user_id == user.user_id
        assert retrieved.username == "getuser"

    def test_get_user_by_id_nonexistent(self, auth_service):
        """Test getting non-existent user."""
        retrieved = auth_service.get_user_by_id("nonexistent_id")
        assert retrieved is None

    def test_get_active_sessions(self, auth_service):
        """Test getting active sessions for a user."""
        user = auth_service.create_user(
            username="sessiontest",
            email="sessiontest@example.com",
            password="Pass123!",
            role=Role.VIEWER,
            full_name="Session Test User",
        )

        # Create a session
        session = auth_service.create_session(user=user)

        # Get active sessions
        sessions = auth_service.get_active_sessions(user.user_id)

        assert len(sessions) >= 1
        assert any(s.session_id == session.session_id for s in sessions)


class TestSignatureService:
    """Tests for SignatureService (RSA packet signing)."""

    @pytest.fixture
    def signature_service(self):
        """Create signature service with temp keys directory."""
        temp_dir = tempfile.mkdtemp()
        service = SignatureService(keys_dir=temp_dir)
        yield service
        # Cleanup
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

    def test_sign_packet(self, signature_service):
        """Test signing a packet."""
        packet_data = {
            "request_id": "req_123",
            "user": "testuser",
            "data": {"key": "value"},
        }

        result = signature_service.sign_packet(packet_data)

        assert "signature" in result
        assert "signed_at" in result
        assert "packet_hash" in result
        assert len(result["signature"]) > 0

    def test_get_public_key_pem(self, signature_service):
        """Test retrieving public key PEM."""
        pem = signature_service.get_public_key_pem()

        assert "BEGIN PUBLIC KEY" in pem
        assert "END PUBLIC KEY" in pem

    def test_get_public_key_fingerprint(self, signature_service):
        """Test retrieving public key fingerprint."""
        fingerprint = signature_service.get_public_key_fingerprint()

        assert len(fingerprint) > 0
        # Fingerprint should be hex string
        assert all(c in "0123456789abcdef" for c in fingerprint)

    def test_verify_packet_signature(self, signature_service):
        """Test verifying a signed packet."""
        packet_data = {
            "request_id": "req_123",
            "user": "testuser",
            "data": {"key": "value"},
        }

        # Sign and enrich
        enriched = signature_service.sign_and_enrich_packet(packet_data)

        # Verify
        is_valid, message = signature_service.verify_packet_signature(enriched)

        assert is_valid is True
        assert "valid" in message.lower() or "success" in message.lower()

    def test_verify_tampered_packet(self, signature_service):
        """Test that tampered packets fail verification."""
        packet_data = {
            "request_id": "req_123",
            "user": "testuser",
            "data": {"key": "value"},
        }

        # Sign and enrich
        enriched = signature_service.sign_and_enrich_packet(packet_data)

        # Tamper with the data
        enriched["data"]["key"] = "tampered_value"

        # Verify should fail
        is_valid, _message = signature_service.verify_packet_signature(enriched)

        assert is_valid is False

    def test_sign_without_private_key(self, tmpdir):
        """Test signing fails when private key is not loaded."""
        from lexecon.security.signature_service import SignatureService

        # Create service without keys
        service = SignatureService(keys_dir=str(tmpdir))
        service.private_key = None  # Explicitly remove private key

        packet_data = {"request_id": "req_123", "data": {}}

        with pytest.raises(RuntimeError, match="Private key not loaded"):
            service.sign_packet(packet_data)

    def test_verify_without_public_key(self, tmpdir):
        """Test verification fails when public key is not loaded."""
        from lexecon.security.signature_service import SignatureService

        service = SignatureService(keys_dir=str(tmpdir))
        service.public_key = None  # Explicitly remove public key

        packet_data = {"request_id": "req_123"}
        signature_hex = "abcd1234"

        with pytest.raises(RuntimeError, match="Public key not loaded"):
            service.verify_signature(packet_data, signature_hex)

    def test_get_public_key_pem_without_key(self, tmpdir):
        """Test get_public_key_pem fails when public key is not loaded."""
        from lexecon.security.signature_service import SignatureService

        service = SignatureService(keys_dir=str(tmpdir))
        service.public_key = None

        with pytest.raises(RuntimeError, match="Public key not loaded"):
            service.get_public_key_pem()

    def test_get_public_key_fingerprint_without_key(self, tmpdir):
        """Test get_public_key_fingerprint fails when public key is not loaded."""
        from lexecon.security.signature_service import SignatureService

        service = SignatureService(keys_dir=str(tmpdir))
        service.public_key = None

        with pytest.raises(RuntimeError, match="Public key not loaded"):
            service.get_public_key_fingerprint()

    def test_verify_packet_without_signature_info(self, signature_service):
        """Test verify_packet_signature returns False when signature_info is missing."""
        packet_data = {"request_id": "req_123", "data": {}}

        is_valid, message = signature_service.verify_packet_signature(packet_data)

        assert is_valid is False
        assert "No signature_info found" in message

    def test_verify_packet_with_missing_signature(self, signature_service):
        """Test verify_packet_signature returns False when signature is missing from signature_info."""
        packet_data = {
            "request_id": "req_123",
            "data": {},
            "signature_info": {
                "algorithm": "RSA-PSS-SHA256",
                # Missing "signature" field
            },
        }

        is_valid, message = signature_service.verify_packet_signature(packet_data)

        assert is_valid is False
        assert "No signature found" in message

    def test_verify_signature_exception_handling(self, signature_service):
        """Test verify_signature handles exceptions gracefully."""
        packet_data = {"request_id": "req_123"}
        invalid_signature = "not_a_valid_hex_signature"

        is_valid, message = signature_service.verify_signature(packet_data, invalid_signature)

        assert is_valid is False
        assert "error" in message.lower()
