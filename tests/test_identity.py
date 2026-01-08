"""Tests for identity and signing functionality."""

import json
import tempfile
from pathlib import Path

import pytest

from lexecon.identity.signing import KeyManager, NodeIdentity


class TestKeyManager:
    """Tests for KeyManager class."""

    def test_generate_key_pair(self):
        """Test generating a new Ed25519 key pair."""
        km = KeyManager.generate()

        assert km.private_key is not None
        assert km.public_key is not None

    def test_different_key_pairs_are_unique(self):
        """Test that multiple generated key pairs are different."""
        km1 = KeyManager.generate()
        km2 = KeyManager.generate()

        # Get fingerprints to compare
        fp1 = km1.get_public_key_fingerprint()
        fp2 = km2.get_public_key_fingerprint()

        assert fp1 != fp2

    def test_save_keys_to_disk(self):
        """Test saving keys to disk in PEM format."""
        km = KeyManager.generate()

        with tempfile.TemporaryDirectory() as tmpdir:
            private_path = Path(tmpdir) / "test.key"
            public_path = Path(tmpdir) / "test.pub"

            km.save_keys(private_path, public_path)

            # Check files exist
            assert private_path.exists()
            assert public_path.exists()

            # Check files have content
            assert len(private_path.read_bytes()) > 0
            assert len(public_path.read_bytes()) > 0

            # Check PEM format
            private_content = private_path.read_text()
            public_content = public_path.read_text()

            assert "BEGIN PRIVATE KEY" in private_content
            assert "END PRIVATE KEY" in private_content
            assert "BEGIN PUBLIC KEY" in public_content
            assert "END PUBLIC KEY" in public_content

    def test_load_keys_from_disk(self):
        """Test loading private key from disk."""
        km_original = KeyManager.generate()

        with tempfile.TemporaryDirectory() as tmpdir:
            private_path = Path(tmpdir) / "test.key"
            public_path = Path(tmpdir) / "test.pub"

            # Save keys
            km_original.save_keys(private_path, public_path)

            # Load keys
            km_loaded = KeyManager.load_keys(private_path)

            assert km_loaded.private_key is not None
            assert km_loaded.public_key is not None

            # Fingerprints should match
            assert (
                km_loaded.get_public_key_fingerprint() == km_original.get_public_key_fingerprint()
            )

    def test_load_public_key_from_disk(self):
        """Test loading public key separately."""
        km = KeyManager.generate()

        with tempfile.TemporaryDirectory() as tmpdir:
            private_path = Path(tmpdir) / "test.key"
            public_path = Path(tmpdir) / "test.pub"

            km.save_keys(private_path, public_path)

            # Load public key
            public_key = KeyManager.load_public_key(public_path)

            assert public_key is not None

    def test_sign_data(self):
        """Test signing data with private key."""
        km = KeyManager.generate()
        data = {"message": "test", "value": 42}

        signature = km.sign(data)

        # Signature should be base64 string
        assert isinstance(signature, str)
        assert len(signature) > 0

        # Should be valid base64
        import base64

        decoded = base64.b64decode(signature)
        assert len(decoded) > 0

    def test_sign_creates_deterministic_signature(self):
        """Test that signing same data twice gives same signature."""
        km = KeyManager.generate()
        data = {"key": "value", "number": 123}

        sig1 = km.sign(data)
        sig2 = km.sign(data)

        assert sig1 == sig2

    def test_sign_different_data_gives_different_signatures(self):
        """Test that different data produces different signatures."""
        km = KeyManager.generate()
        data1 = {"message": "first"}
        data2 = {"message": "second"}

        sig1 = km.sign(data1)
        sig2 = km.sign(data2)

        assert sig1 != sig2

    def test_verify_valid_signature(self):
        """Test verifying a valid signature."""
        km = KeyManager.generate()
        data = {"test": "data", "count": 5}

        signature = km.sign(data)
        is_valid = KeyManager.verify(data, signature, km.public_key)

        assert is_valid is True

    def test_verify_invalid_signature(self):
        """Test that invalid signature fails verification."""
        km = KeyManager.generate()
        data = {"test": "data"}

        signature = km.sign(data)

        # Tamper with signature
        import base64

        sig_bytes = base64.b64decode(signature)
        tampered = sig_bytes[:-1] + bytes([sig_bytes[-1] ^ 0xFF])
        tampered_sig = base64.b64encode(tampered).decode()

        is_valid = KeyManager.verify(data, tampered_sig, km.public_key)

        assert is_valid is False

    def test_verify_signature_with_wrong_key(self):
        """Test that signature verification fails with wrong public key."""
        km1 = KeyManager.generate()
        km2 = KeyManager.generate()
        data = {"test": "data"}

        # Sign with km1
        signature = km1.sign(data)

        # Verify with km2's public key
        is_valid = KeyManager.verify(data, signature, km2.public_key)

        assert is_valid is False

    def test_verify_signature_with_tampered_data(self):
        """Test that verification fails when data is tampered."""
        km = KeyManager.generate()
        data = {"value": 100}

        signature = km.sign(data)

        # Tamper with data
        tampered_data = {"value": 999}

        is_valid = KeyManager.verify(tampered_data, signature, km.public_key)

        assert is_valid is False

    def test_sign_without_private_key_raises_error(self):
        """Test that signing without private key raises error."""
        km = KeyManager()  # No key

        with pytest.raises(ValueError, match="No private key"):
            km.sign({"test": "data"})

    def test_save_keys_without_private_key_raises_error(self):
        """Test that saving without private key raises error."""
        km = KeyManager()  # No key

        with tempfile.TemporaryDirectory() as tmpdir:
            private_path = Path(tmpdir) / "test.key"
            public_path = Path(tmpdir) / "test.pub"

            with pytest.raises(ValueError, match="No private key"):
                km.save_keys(private_path, public_path)

    def test_get_public_key_fingerprint(self):
        """Test getting public key fingerprint."""
        km = KeyManager.generate()

        fingerprint = km.get_public_key_fingerprint()

        # Should be 16 character hex string (first 16 chars of SHA256)
        assert isinstance(fingerprint, str)
        assert len(fingerprint) == 16
        # Should be valid hex
        int(fingerprint, 16)

    def test_fingerprint_is_deterministic(self):
        """Test that fingerprint is deterministic for same key."""
        km = KeyManager.generate()

        fp1 = km.get_public_key_fingerprint()
        fp2 = km.get_public_key_fingerprint()

        assert fp1 == fp2

    def test_get_fingerprint_without_public_key_raises_error(self):
        """Test that getting fingerprint without key raises error."""
        km = KeyManager()

        with pytest.raises(ValueError, match="No public key"):
            km.get_public_key_fingerprint()

    def test_sign_canonical_json(self):
        """Test that signing uses canonical JSON representation."""
        km = KeyManager.generate()

        # These should produce the same signature due to canonical JSON
        data1 = {"b": 2, "a": 1}
        data2 = {"a": 1, "b": 2}

        sig1 = km.sign(data1)
        sig2 = km.sign(data2)

        assert sig1 == sig2

    def test_sign_handles_nested_data(self):
        """Test signing complex nested data structures."""
        km = KeyManager.generate()
        data = {
            "user": {"name": "Alice", "id": 123},
            "permissions": ["read", "write"],
            "metadata": {"created": "2025-01-01", "version": 2},
        }

        signature = km.sign(data)
        is_valid = KeyManager.verify(data, signature, km.public_key)

        assert is_valid is True

    def test_key_persistence_roundtrip(self):
        """Test full roundtrip: generate, save, load, verify."""
        km_original = KeyManager.generate()
        data = {"test": "roundtrip"}
        original_signature = km_original.sign(data)

        with tempfile.TemporaryDirectory() as tmpdir:
            private_path = Path(tmpdir) / "key.pem"
            public_path = Path(tmpdir) / "key.pub"

            # Save
            km_original.save_keys(private_path, public_path)

            # Load
            km_loaded = KeyManager.load_keys(private_path)

            # Should be able to sign with loaded key
            loaded_signature = km_loaded.sign(data)

            # Signatures should match
            assert loaded_signature == original_signature

            # Verification should work
            assert KeyManager.verify(data, loaded_signature, km_loaded.public_key) is True


class TestNodeIdentity:
    """Tests for NodeIdentity class."""

    def test_create_node_identity(self):
        """Test creating a node identity."""
        node = NodeIdentity("test-node-1")

        assert node.node_id == "test-node-1"
        assert node.key_manager is not None
        assert node.key_manager.private_key is not None

    def test_create_with_existing_key_manager(self):
        """Test creating node with existing key manager."""
        km = KeyManager.generate()
        node = NodeIdentity("test-node-2", key_manager=km)

        assert node.node_id == "test-node-2"
        assert node.key_manager is km

    def test_get_node_id(self):
        """Test getting node ID."""
        node = NodeIdentity("my-node")

        assert node.get_node_id() == "my-node"

    def test_sign_data(self):
        """Test signing data through node identity."""
        node = NodeIdentity("signer-node")
        data = {"message": "test", "timestamp": "2025-01-01"}

        signature = node.sign(data)

        assert isinstance(signature, str)
        assert len(signature) > 0

    def test_get_public_key_fingerprint(self):
        """Test getting public key fingerprint."""
        node = NodeIdentity("fp-node")

        fingerprint = node.get_public_key_fingerprint()

        assert isinstance(fingerprint, str)
        assert len(fingerprint) == 16

    def test_verify_signature_with_string_data(self):
        """Test verifying signature on string data (like hashes)."""
        node = NodeIdentity("verify-node")

        # Simulate signing a hash string
        hash_string = "abc123def456"

        # Sign it manually through key manager
        import base64

        message = hash_string.encode()
        signature_bytes = node.key_manager.private_key.sign(message)
        signature = base64.b64encode(signature_bytes).decode()

        # Verify using node identity
        is_valid = node.verify_signature(hash_string, signature)

        assert is_valid is True

    def test_verify_signature_fails_with_wrong_data(self):
        """Test that verification fails with different data."""
        node = NodeIdentity("verify-node")

        original_data = "original_hash"
        tampered_data = "tampered_hash"

        # Sign original
        import base64

        message = original_data.encode()
        signature_bytes = node.key_manager.private_key.sign(message)
        signature = base64.b64encode(signature_bytes).decode()

        # Try to verify with tampered data
        is_valid = node.verify_signature(tampered_data, signature)

        assert is_valid is False

    def test_verify_signature_fails_with_wrong_signature(self):
        """Test that verification fails with invalid signature."""
        node = NodeIdentity("verify-node")
        data = "test_data"

        # Create invalid signature
        fake_signature = "aW52YWxpZF9zaWduYXR1cmU="  # base64 of "invalid_signature"

        is_valid = node.verify_signature(data, fake_signature)

        assert is_valid is False

    def test_verify_signature_without_public_key(self):
        """Test verification fails without public key."""
        node = NodeIdentity("no-key-node")
        # Remove public key
        node.key_manager.public_key = None

        is_valid = node.verify_signature("data", "signature")

        assert is_valid is False

    def test_different_nodes_have_different_fingerprints(self):
        """Test that different nodes have unique fingerprints."""
        node1 = NodeIdentity("node-1")
        node2 = NodeIdentity("node-2")

        fp1 = node1.get_public_key_fingerprint()
        fp2 = node2.get_public_key_fingerprint()

        assert fp1 != fp2

    def test_node_can_verify_own_signature(self):
        """Test that node can verify its own signatures."""
        node = NodeIdentity("self-verify-node")
        data = {"action": "test", "value": 42}

        # Sign with node
        signature = node.sign(data)

        # Convert dict to canonical JSON for verification
        import json

        canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))

        # This should work with the node's verify_signature method
        # but it expects string data, so we need to verify differently
        # Let's use the key manager's verify method
        is_valid = KeyManager.verify(data, signature, node.key_manager.public_key)

        assert is_valid is True


class TestCrossNodeVerification:
    """Tests for cross-node signature verification."""

    def test_node_cannot_verify_other_node_signature(self):
        """Test that one node cannot forge another's signature."""
        node1 = NodeIdentity("node-1")
        node2 = NodeIdentity("node-2")

        data = {"message": "test"}

        # Node 1 signs
        signature = node1.sign(data)

        # Node 2 tries to verify with its own key
        is_valid = KeyManager.verify(data, signature, node2.key_manager.public_key)

        assert is_valid is False

    def test_public_key_distribution(self):
        """Test that public keys can be shared for verification."""
        node1 = NodeIdentity("alice")
        node2 = NodeIdentity("bob")

        data = {"transfer": "100", "to": "bob"}

        # Alice signs
        signature = node1.sign(data)

        # Bob can verify using Alice's public key
        is_valid = KeyManager.verify(data, signature, node1.key_manager.public_key)

        assert is_valid is True

    def test_signature_persistence_across_nodes(self):
        """Test signature verification works after key export/import."""
        # Node 1 creates and signs
        node1 = NodeIdentity("node-1")
        data = {"test": "data"}
        signature = node1.sign(data)

        with tempfile.TemporaryDirectory() as tmpdir:
            private_path = Path(tmpdir) / "node1.key"
            public_path = Path(tmpdir) / "node1.pub"

            # Export keys
            node1.key_manager.save_keys(private_path, public_path)

            # Load into new key manager (simulating different node)
            loaded_km = KeyManager.load_keys(private_path)

            # Should be able to verify with loaded keys
            is_valid = KeyManager.verify(data, signature, loaded_km.public_key)
            assert is_valid is True


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_sign_empty_dict(self):
        """Test signing empty dictionary."""
        km = KeyManager.generate()
        data = {}

        signature = km.sign(data)
        is_valid = KeyManager.verify(data, signature, km.public_key)

        assert is_valid is True

    def test_sign_large_data(self):
        """Test signing large data structure."""
        km = KeyManager.generate()
        data = {"items": [{"id": i, "value": f"item_{i}"} for i in range(1000)]}

        signature = km.sign(data)
        is_valid = KeyManager.verify(data, signature, km.public_key)

        assert is_valid is True

    def test_sign_with_unicode(self):
        """Test signing data with unicode characters."""
        km = KeyManager.generate()
        data = {"message": "Hello 世界 🌍", "emoji": "🔐"}

        signature = km.sign(data)
        is_valid = KeyManager.verify(data, signature, km.public_key)

        assert is_valid is True

    def test_node_id_with_special_characters(self):
        """Test node identity with special characters in ID."""
        node = NodeIdentity("node-123_test.example.com")

        assert node.get_node_id() == "node-123_test.example.com"

    def test_verify_with_malformed_signature(self):
        """Test verification with malformed base64 signature."""
        node = NodeIdentity("test-node")

        # Invalid base64
        invalid_sig = "not-valid-base64!!!"

        is_valid = node.verify_signature("data", invalid_sig)

        assert is_valid is False

    def test_load_nonexistent_key_file(self):
        """Test loading from non-existent file."""
        with pytest.raises(FileNotFoundError):
            KeyManager.load_keys(Path("/nonexistent/key.pem"))

    def test_save_to_readonly_directory(self):
        """Test error handling when saving to readonly location."""
        import os

        # Skip if running as root (has permission to write everywhere)
        if os.getuid() == 0:
            pytest.skip("Running as root, cannot test readonly directory")

        km = KeyManager.generate()

        # Try to save to root (should fail on Unix systems)
        readonly_path = Path("/readonly.key")
        readonly_pub = Path("/readonly.pub")

        with pytest.raises((PermissionError, OSError)):
            km.save_keys(readonly_path, readonly_pub)
