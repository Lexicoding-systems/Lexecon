"""Tests for authentication middleware."""

from unittest.mock import Mock

import pytest
from fastapi import Request

from lexecon.security.auth_service import Permission, Role, Session
from lexecon.security.middleware import get_current_user, require_permission


class TestGetCurrentUser:
    """Tests for get_current_user helper."""

    def test_get_current_user_with_session(self):
        """Test getting current user from request with session."""
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.user_id = "user_123"
        request.state.username = "testuser"
        request.state.role = Role.AUDITOR
        request.state.session = Mock()

        user = get_current_user(request)

        assert user is not None
        assert user["user_id"] == "user_123"
        assert user["username"] == "testuser"
        assert user["role"] == "auditor"

    def test_get_current_user_without_session(self):
        """Test getting current user from request without session."""
        request = Mock(spec=Request)
        request.state = Mock(spec=[])  # Empty state, no session attribute

        user = get_current_user(request)

        assert user is None

    def test_get_current_user_with_string_role(self):
        """Test getting current user when role is a string."""
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.user_id = "user_123"
        request.state.username = "testuser"
        request.state.role = "viewer"  # String instead of enum
        request.state.session = Mock()

        user = get_current_user(request)

        assert user is not None
        assert user["role"] == "viewer"
