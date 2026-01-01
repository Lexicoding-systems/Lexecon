"""
Identity & Signing - Ed25519 key management and cryptographic signatures.

Manages key pairs for signing decisions and verifying integrity.
"""

import base64
import json
from pathlib import Path
from typing import Any, Dict, Optional

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey


class NodeIdentity:
    """
    Represents a node's identity in the governance system.

    Each node has a unique identifier and associated cryptographic keys.
    """

    def __init__(self, node_id: str, key_manager: Optional["KeyManager"] = None):
        self.node_id = node_id
        self.key_manager = key_manager or KeyManager.generate()

    def get_node_id(self) -> str:
        """Get the node identifier."""
        return self.node_id

    def sign(self, data: Dict[str, Any]) -> str:
        """Sign data using the node's private key."""
        return self.key_manager.sign(data)

    def get_public_key_fingerprint(self) -> str:
        """Get the fingerprint of the node's public key."""
        return self.key_manager.get_public_key_fingerprint()


class KeyManager:
    """
    Manages Ed25519 key pairs for signing and verification.

    Keys can be generated, saved to disk, and loaded from disk.
    """

    def __init__(self, private_key: Optional[Ed25519PrivateKey] = None):
        self.private_key = private_key
        self.public_key = private_key.public_key() if private_key else None

    @classmethod
    def generate(cls) -> "KeyManager":
        """Generate a new Ed25519 key pair."""
        private_key = Ed25519PrivateKey.generate()
        return cls(private_key=private_key)

    def save_keys(self, private_key_path: Path, public_key_path: Path) -> None:
        """Save keys to disk in PEM format."""
        if self.private_key is None:
            raise ValueError("No private key to save")

        # Save private key
        private_pem = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        private_key_path.write_bytes(private_pem)

        # Save public key
        public_pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        public_key_path.write_bytes(public_pem)

    @classmethod
    def load_keys(cls, private_key_path: Path) -> "KeyManager":
        """Load private key from disk."""
        private_pem = private_key_path.read_bytes()
        private_key = serialization.load_pem_private_key(private_pem, password=None)
        return cls(private_key=private_key)

    @classmethod
    def load_public_key(cls, public_key_path: Path) -> Ed25519PublicKey:
        """Load public key from disk."""
        public_pem = public_key_path.read_bytes()
        return serialization.load_pem_public_key(public_pem)

    def sign(self, data: Dict[str, Any]) -> str:
        """
        Sign data using private key.

        Returns base64-encoded signature.
        """
        if self.private_key is None:
            raise ValueError("No private key available for signing")

        # Create canonical JSON representation
        canonical_json = json.dumps(data, sort_keys=True, separators=(",", ":"))
        message = canonical_json.encode()

        # Sign
        signature = self.private_key.sign(message)

        # Return base64-encoded signature
        return base64.b64encode(signature).decode()

    @staticmethod
    def verify(data: Dict[str, Any], signature: str, public_key: Ed25519PublicKey) -> bool:
        """
        Verify signature on data using public key.

        Returns True if signature is valid, False otherwise.
        """
        try:
            # Create canonical JSON representation
            canonical_json = json.dumps(data, sort_keys=True, separators=(",", ":"))
            message = canonical_json.encode()

            # Decode signature
            signature_bytes = base64.b64decode(signature)

            # Verify (raises exception if invalid)
            public_key.verify(signature_bytes, message)
            return True
        except Exception:
            return False

    def get_public_key_fingerprint(self) -> str:
        """Get fingerprint of public key for identification."""
        if self.public_key is None:
            raise ValueError("No public key available")

        public_pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        import hashlib

        return hashlib.sha256(public_pem).hexdigest()[:16]
