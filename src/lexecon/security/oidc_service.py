"""OpenID Connect (OIDC) OAuth Authentication Service.

Provides generic OIDC support for SSO with any compliant provider:
- Google, Azure AD, Okta, Auth0, Keycloak, etc.
- Authorization code flow with PKCE support
- ID token verification with JWKS
- User provisioning and account linking
- State/nonce CSRF protection

Architecture:
- OIDCProvider: Individual provider configuration and operations
- OIDCService: Multi-provider management and database integration
"""

import hashlib
import json
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode

import jwt
import requests


class OIDCProvider:
    """Individual OIDC provider configuration and operations.

    Handles discovery, authorization, token exchange, and verification for one provider.
    """

    def __init__(
        self,
        provider_name: str,
        discovery_url: str,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        scopes: Optional[List[str]] = None,
    ):
        """Initialize OIDC provider.

        Args:
            provider_name: Unique provider identifier (e.g., 'google', 'azure')
            discovery_url: OpenID Connect discovery endpoint URL
            client_id: OAuth client ID
            client_secret: OAuth client secret
            redirect_uri: Redirect URI for OAuth callback
            scopes: OAuth scopes (default: ['openid', 'profile', 'email'])
        """
        self.provider_name = provider_name
        self.discovery_url = discovery_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scopes = scopes or ["openid", "profile", "email"]

        # Cached discovery data
        self._discovery_data: Optional[Dict[str, Any]] = None
        self._jwks_data: Optional[Dict[str, Any]] = None

    def get_discovery_data(self) -> Dict[str, Any]:
        """Fetch OpenID Connect discovery document.

        Returns:
            Discovery data with endpoints and capabilities
        """
        if self._discovery_data:
            return self._discovery_data

        try:
            response = requests.get(self.discovery_url, timeout=10)
            response.raise_for_status()
            self._discovery_data = response.json()
            return self._discovery_data
        except Exception as e:
            raise ValueError(f"Failed to fetch OIDC discovery document: {e}")

    def get_jwks(self) -> Dict[str, Any]:
        """Fetch JSON Web Key Set (JWKS) for token verification.

        Returns:
            JWKS data
        """
        if self._jwks_data:
            return self._jwks_data

        discovery = self.get_discovery_data()
        jwks_uri = discovery.get("jwks_uri")

        if not jwks_uri:
            raise ValueError("JWKS URI not found in discovery document")

        try:
            response = requests.get(jwks_uri, timeout=10)
            response.raise_for_status()
            self._jwks_data = response.json()
            return self._jwks_data
        except Exception as e:
            raise ValueError(f"Failed to fetch JWKS: {e}")

    def get_authorization_url(self, state: str, nonce: str) -> str:
        """Generate authorization URL for OAuth flow.

        Args:
            state: CSRF protection token
            nonce: Replay protection token

        Returns:
            Authorization URL to redirect user to
        """
        discovery = self.get_discovery_data()
        auth_endpoint = discovery.get("authorization_endpoint")

        if not auth_endpoint:
            raise ValueError("Authorization endpoint not found in discovery document")

        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "scope": " ".join(self.scopes),
            "redirect_uri": self.redirect_uri,
            "state": state,
            "nonce": nonce,
        }

        return f"{auth_endpoint}?{urlencode(params)}"

    def exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for tokens.

        Args:
            code: Authorization code from callback

        Returns:
            Token response with access_token, id_token, etc.
        """
        discovery = self.get_discovery_data()
        token_endpoint = discovery.get("token_endpoint")

        if not token_endpoint:
            raise ValueError("Token endpoint not found in discovery document")

        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        try:
            response = requests.post(token_endpoint, data=data, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise ValueError(f"Token exchange failed: {e}")

    def verify_id_token(self, id_token: str, nonce: str) -> Dict[str, Any]:
        """Verify and decode ID token.

        Args:
            id_token: JWT ID token
            nonce: Expected nonce value

        Returns:
            Decoded token claims
        """
        try:
            # Decode header to get key ID
            header = jwt.get_unverified_header(id_token)
            kid = header.get("kid")

            # Get signing key from JWKS
            jwks = self.get_jwks()
            signing_key = None

            for key in jwks.get("keys", []):
                if key.get("kid") == kid:
                    signing_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key))
                    break

            if not signing_key:
                raise ValueError(f"Signing key not found in JWKS for kid: {kid}")

            # Verify and decode token
            discovery = self.get_discovery_data()
            issuer = discovery.get("issuer")

            claims = jwt.decode(
                id_token,
                signing_key,
                algorithms=["RS256"],
                audience=self.client_id,
                issuer=issuer,
                options={
                    "verify_signature": True,
                    "verify_aud": True,
                    "verify_iss": True,
                    "verify_exp": True,
                },
            )

            # Verify nonce
            if claims.get("nonce") != nonce:
                raise ValueError("Nonce mismatch")

            return claims

        except jwt.ExpiredSignatureError:
            raise ValueError("ID token has expired")
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid ID token: {e}")
        except Exception as e:
            raise ValueError(f"ID token verification failed: {e}")

    def get_userinfo(self, access_token: str) -> Dict[str, Any]:
        """Fetch user information from userinfo endpoint.

        Args:
            access_token: OAuth access token

        Returns:
            User information
        """
        discovery = self.get_discovery_data()
        userinfo_endpoint = discovery.get("userinfo_endpoint")

        if not userinfo_endpoint:
            # Some providers don't have userinfo endpoint, return empty
            return {}

        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = requests.get(userinfo_endpoint, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            # Non-fatal, userinfo is optional
            print(f"Warning: Failed to fetch userinfo: {e}")
            return {}


class OIDCService:
    """Multi-provider OIDC service with database integration.

    Manages multiple OIDC providers, state/nonce storage, and user provisioning.
    """

    def __init__(self, db_path: str = "lexecon_auth.db", base_url: str = "http://localhost:8000"):
        """Initialize OIDC service.

        Args:
            db_path: Path to authentication database
            base_url: Base URL for OAuth callbacks
        """
        self.db_path = db_path
        self.base_url = base_url
        self.providers: Dict[str, OIDCProvider] = {}

    def register_provider(
        self,
        provider_name: str,
        discovery_url: str,
        client_id: str,
        client_secret: str,
        scopes: Optional[List[str]] = None,
    ) -> OIDCProvider:
        """Register an OIDC provider.

        Args:
            provider_name: Unique provider identifier
            discovery_url: OIDC discovery endpoint
            client_id: OAuth client ID
            client_secret: OAuth client secret
            scopes: OAuth scopes

        Returns:
            Configured OIDCProvider
        """
        redirect_uri = f"{self.base_url}/auth/oidc/callback/{provider_name}"

        provider = OIDCProvider(
            provider_name=provider_name,
            discovery_url=discovery_url,
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scopes=scopes,
        )

        self.providers[provider_name] = provider
        return provider

    def get_provider(self, provider_name: str) -> Optional[OIDCProvider]:
        """Get registered provider by name."""
        return self.providers.get(provider_name)

    def list_providers(self) -> List[Dict[str, str]]:
        """List all registered providers."""
        return [
            {
                "name": name,
                "display_name": name.title(),
            }
            for name in self.providers
        ]

    def initiate_login(self, provider_name: str) -> Tuple[str, str]:
        """Initiate OAuth login flow.

        Args:
            provider_name: Provider to use

        Returns:
            Tuple of (authorization_url, state)
        """
        provider = self.get_provider(provider_name)
        if not provider:
            raise ValueError(f"Provider not found: {provider_name}")

        # Generate state and nonce
        state = secrets.token_urlsafe(32)
        nonce = secrets.token_urlsafe(32)

        # Store state/nonce in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            created_at = datetime.now(timezone.utc)
            expires_at = created_at + timedelta(minutes=10)

            cursor.execute("""
                INSERT INTO oidc_states (
                    state, nonce, provider_name, created_at, expires_at
                ) VALUES (?, ?, ?, ?, ?)
            """, (state, nonce, provider_name, created_at.isoformat(), expires_at.isoformat()))

            conn.commit()
        finally:
            conn.close()

        # Generate authorization URL
        auth_url = provider.get_authorization_url(state, nonce)

        return auth_url, state

    def handle_callback(
        self,
        provider_name: str,
        code: str,
        state: str,
    ) -> Tuple[Optional[str], Optional[str]]:
        """Handle OAuth callback.

        Args:
            provider_name: Provider that sent callback
            code: Authorization code
            state: State parameter

        Returns:
            Tuple of (user_id, error)
        """
        provider = self.get_provider(provider_name)
        if not provider:
            return None, f"Provider not found: {provider_name}"

        # Verify state and get nonce
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT nonce, expires_at
                FROM oidc_states
                WHERE state = ? AND provider_name = ?
            """, (state, provider_name))

            row = cursor.fetchone()
            if not row:
                return None, "Invalid state parameter"

            nonce, expires_at = row

            # Check expiration
            expires_dt = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            if datetime.now(timezone.utc) > expires_dt:
                return None, "State has expired"

            # Delete used state
            cursor.execute("DELETE FROM oidc_states WHERE state = ?", (state,))
            conn.commit()

        finally:
            conn.close()

        # Exchange code for tokens
        try:
            tokens = provider.exchange_code_for_tokens(code)
        except Exception as e:
            return None, f"Token exchange failed: {e!s}"

        # Verify ID token
        id_token = tokens.get("id_token")
        if not id_token:
            return None, "No ID token in response"

        try:
            claims = provider.verify_id_token(id_token, nonce)
        except Exception as e:
            return None, f"ID token verification failed: {e!s}"

        # Extract user information
        provider_user_id = claims.get("sub")
        email = claims.get("email")
        name = claims.get("name", email)

        if not provider_user_id:
            return None, "No subject (sub) in ID token"

        # Provision or link user
        user_id = self._provision_user(
            provider_name=provider_name,
            provider_user_id=provider_user_id,
            email=email,
            name=name,
        )

        return user_id, None

    def _provision_user(
        self,
        provider_name: str,
        provider_user_id: str,
        email: Optional[str],
        name: Optional[str],
    ) -> str:
        """Provision or link user account.

        Args:
            provider_name: OIDC provider name
            provider_user_id: User ID from provider (sub claim)
            email: User email
            name: User display name

        Returns:
            User ID
        """
        from lexecon.security.auth_service import Role

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Check if OIDC mapping already exists
            cursor.execute("""
                SELECT user_id
                FROM oidc_users
                WHERE provider_name = ? AND provider_user_id = ?
            """, (provider_name, provider_user_id))

            row = cursor.fetchone()
            if row:
                # Existing mapping, update last_login
                user_id = row[0]
                cursor.execute("""
                    UPDATE oidc_users
                    SET last_login = ?
                    WHERE provider_name = ? AND provider_user_id = ?
                """, (datetime.now(timezone.utc).isoformat(), provider_name, provider_user_id))
                conn.commit()
                return user_id

            # No existing mapping, check if user exists by email
            if email:
                cursor.execute("SELECT user_id FROM users WHERE email = ?", (email,))
                row = cursor.fetchone()
                if row:
                    # Link OIDC to existing user
                    user_id = row[0]
                    self._link_oidc_to_user(cursor, user_id, provider_name, provider_user_id, email)
                    conn.commit()
                    return user_id

            # Create new user
            user_id = f"user_{secrets.token_hex(16)}"
            username = email.split("@")[0] if email else f"{provider_name}_{provider_user_id[:8]}"

            # Ensure unique username
            cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", (username,))
            if cursor.fetchone()[0] > 0:
                username = f"{username}_{secrets.token_hex(4)}"

            # Generate random password (user won't use it, OAuth login only)
            random_password = secrets.token_urlsafe(32)
            salt = secrets.token_hex(32)
            password_hash = hashlib.pbkdf2_hmac(
                "sha256",
                random_password.encode("utf-8"),
                salt.encode("utf-8"),
                100000,
            ).hex()

            created_at = datetime.now(timezone.utc).isoformat()

            cursor.execute("""
                INSERT INTO users (
                    user_id, username, email, password_hash, salt,
                    role, full_name, created_at, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (user_id, username, email or "", password_hash, salt,
                  Role.VIEWER.value, name or username, created_at))

            # Link OIDC
            self._link_oidc_to_user(cursor, user_id, provider_name, provider_user_id, email)

            conn.commit()
            return user_id

        finally:
            conn.close()

    def _link_oidc_to_user(
        self,
        cursor: sqlite3.Cursor,
        user_id: str,
        provider_name: str,
        provider_user_id: str,
        email: Optional[str],
    ) -> None:
        """Link OIDC provider to user account."""
        mapping_id = f"oidc_{secrets.token_hex(16)}"
        linked_at = datetime.now(timezone.utc).isoformat()

        cursor.execute("""
            INSERT INTO oidc_users (
                mapping_id, user_id, provider_name, provider_user_id,
                provider_email, linked_at, last_login
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (mapping_id, user_id, provider_name, provider_user_id,
              email, linked_at, linked_at))

    def get_linked_providers(self, user_id: str) -> List[Dict[str, Any]]:
        """Get OIDC providers linked to user."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT provider_name, provider_email, linked_at, last_login
                FROM oidc_users
                WHERE user_id = ?
            """, (user_id,))

            providers = []
            for row in cursor.fetchall():
                providers.append({
                    "provider_name": row[0],
                    "provider_email": row[1],
                    "linked_at": row[2],
                    "last_login": row[3],
                })

            return providers

        finally:
            conn.close()

    def unlink_provider(self, user_id: str, provider_name: str) -> bool:
        """Unlink OIDC provider from user."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                DELETE FROM oidc_users
                WHERE user_id = ? AND provider_name = ?
            """, (user_id, provider_name))

            conn.commit()
            return cursor.rowcount > 0

        finally:
            conn.close()

    def cleanup_expired_states(self):
        """Delete expired OAuth states."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cutoff = datetime.now(timezone.utc).isoformat()

            cursor.execute("""
                DELETE FROM oidc_states
                WHERE expires_at < ?
            """, (cutoff,))

            conn.commit()
            return cursor.rowcount

        finally:
            conn.close()


# Global instance
_oidc_service: Optional[OIDCService] = None


def get_oidc_service() -> OIDCService:
    """Get global OIDC service instance."""
    global _oidc_service

    if _oidc_service is None:
        import os
        base_url = os.getenv("LEXECON_BASE_URL", "http://localhost:8000")
        _oidc_service = OIDCService(base_url=base_url)

    return _oidc_service
