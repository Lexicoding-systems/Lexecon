"""
Digital Signature Service for Audit Packets.

Provides:
- RSA key generation and management
- Digital signing of audit packets
- Signature verification
- Non-repudiation guarantees
"""

import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Tuple

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa


class SignatureService:
    """Digital signature service for audit packets."""

    def __init__(self, keys_dir: str = "lexecon_keys"):
        """
        Initialize signature service.

        Args:
            keys_dir: Directory to store public/private keys
        """
        self.keys_dir = keys_dir
        self.private_key_path = os.path.join(keys_dir, "private_key.pem")
        self.public_key_path = os.path.join(keys_dir, "public_key.pem")
        self.private_key = None
        self.public_key = None

        # Create keys directory if it doesn't exist
        os.makedirs(keys_dir, exist_ok=True)

        # Load or generate keys
        if not self._keys_exist():
            self._generate_keys()
        else:
            self._load_keys()

    def _keys_exist(self) -> bool:
        """Check if keys already exist."""
        return os.path.exists(self.private_key_path) and os.path.exists(self.public_key_path)

    def _generate_keys(self):
        """Generate new RSA key pair."""
        # Generate private key (4096 bits for high security)
        self.private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=4096, backend=default_backend()
        )

        # Derive public key
        self.public_key = self.private_key.public_key()

        # Save private key (encrypted with passphrase in production)
        private_pem = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),  # For demo; use BestAvailableEncryption in production
        )

        with open(self.private_key_path, "wb") as f:
            f.write(private_pem)

        # Save public key
        public_pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        with open(self.public_key_path, "wb") as f:
            f.write(public_pem)

        # Set restrictive permissions
        os.chmod(self.private_key_path, 0o600)  # Owner read/write only
        os.chmod(self.public_key_path, 0o644)  # World-readable

    def _load_keys(self):
        """Load existing keys from disk."""
        with open(self.private_key_path, "rb") as f:
            self.private_key = serialization.load_pem_private_key(
                f.read(), password=None, backend=default_backend()  # Use password in production
            )

        with open(self.public_key_path, "rb") as f:
            self.public_key = serialization.load_pem_public_key(f.read(), backend=default_backend())

    def sign_packet(self, packet_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sign an audit packet with digital signature.

        Args:
            packet_data: The audit packet to sign

        Returns:
            Dict with signature information
        """
        if not self.private_key:
            raise RuntimeError("Private key not loaded")

        # Compute packet hash (SHA-256)
        packet_json = json.dumps(packet_data, sort_keys=True)
        packet_hash = hashlib.sha256(packet_json.encode()).hexdigest()

        # Sign the hash with RSA private key
        signature = self.private_key.sign(
            packet_hash.encode(),
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256(),
        )

        # Encode signature as hex
        signature_hex = signature.hex()

        # Get public key fingerprint
        public_pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        public_key_fingerprint = hashlib.sha256(public_pem).hexdigest()[:16]

        # Create signature metadata
        signature_info = {
            "signature_version": "1.0",
            "algorithm": "RSA-PSS-SHA256",
            "key_size": 4096,
            "packet_hash": packet_hash,
            "signature": signature_hex,
            "public_key_fingerprint": public_key_fingerprint,
            "signed_at": datetime.now(timezone.utc).isoformat(),
            "signed_by": "Lexecon Governance System",
            "verification_instructions": "Use /compliance/verify-signature endpoint with packet and signature",
        }

        return signature_info

    def verify_signature(self, packet_data: Dict[str, Any], signature_hex: str) -> Tuple[bool, str]:
        """
        Verify a signature on an audit packet.

        Args:
            packet_data: The audit packet (without signature_info)
            signature_hex: The signature to verify (hex string)

        Returns:
            (is_valid, message) tuple
        """
        if not self.public_key:
            raise RuntimeError("Public key not loaded")

        try:
            # Compute packet hash
            packet_json = json.dumps(packet_data, sort_keys=True)
            packet_hash = hashlib.sha256(packet_json.encode()).hexdigest()

            # Decode signature
            signature = bytes.fromhex(signature_hex)

            # Verify signature
            self.public_key.verify(
                signature,
                packet_hash.encode(),
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                hashes.SHA256(),
            )

            return True, "Signature is valid"

        except InvalidSignature:
            return False, "Signature verification failed - packet may have been tampered with"
        except Exception as e:
            return False, f"Verification error: {str(e)}"

    def get_public_key_pem(self) -> str:
        """Get public key in PEM format for distribution."""
        if not self.public_key:
            raise RuntimeError("Public key not loaded")

        public_pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        return public_pem.decode("utf-8")

    def get_public_key_fingerprint(self) -> str:
        """Get SHA-256 fingerprint of public key."""
        if not self.public_key:
            raise RuntimeError("Public key not loaded")

        public_pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        return hashlib.sha256(public_pem).hexdigest()

    def sign_and_enrich_packet(self, packet_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sign packet and add signature to the packet itself.

        Args:
            packet_data: The audit packet to sign

        Returns:
            Enriched packet with signature_info field
        """
        # Create a copy without signature_info (if it exists)
        packet_to_sign = {k: v for k, v in packet_data.items() if k != "signature_info"}

        # Generate signature
        signature_info = self.sign_packet(packet_to_sign)

        # Add signature to packet
        enriched_packet = {**packet_data, "signature_info": signature_info}

        return enriched_packet

    def verify_packet_signature(self, packet_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Verify signature embedded in packet.

        Args:
            packet_data: Complete packet with signature_info

        Returns:
            (is_valid, message) tuple
        """
        if "signature_info" not in packet_data:
            return False, "No signature_info found in packet"

        signature_info = packet_data["signature_info"]

        if "signature" not in signature_info:
            return False, "No signature found in signature_info"

        # Extract packet without signature
        packet_to_verify = {k: v for k, v in packet_data.items() if k != "signature_info"}

        # Verify
        return self.verify_signature(packet_to_verify, signature_info["signature"])
