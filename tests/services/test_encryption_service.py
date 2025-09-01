import os
import sys

# Provide password for module-level encryption_service
os.environ.setdefault("ENCRYPTION_PASSWORD", "testpassword")

# Ensure repository root is on the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.services.encryption_service import EncryptionService


def test_encrypt_decrypt_roundtrip():
    service = EncryptionService(password="testpassword")
    plaintext = "Hello, World!"

    encrypted = service.encrypt(plaintext)
    assert encrypted != plaintext

    decrypted = service.decrypt(encrypted)
    assert decrypted == plaintext


def test_encrypt_decrypt_dict_fields():
    service = EncryptionService(password="testpassword")
    original = {
        "username": "admin",
        "password": "secret",
        "token": "abc123",
    }
    fields = ["password", "token"]

    encrypted = service.encrypt_dict(original, fields)

    # encrypted fields should change
    assert encrypted["password"] != original["password"]
    assert encrypted["token"] != original["token"]
    # untouched field should stay the same
    assert encrypted["username"] == original["username"]

    decrypted = service.decrypt_dict(encrypted, fields)

    assert decrypted == original
