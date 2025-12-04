import base64
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from django.conf import settings


class ChatEncryption:
    """
    Quantum-resistant encryption for chat messages using AES-256-GCM
    with a single master key. IV is embedded in the encrypted content.
    """

    @staticmethod
    def _get_master_key():
        """Get the master encryption key from Django settings."""
        master_key = getattr(settings, "CHAT_ENCRYPTION_KEY", None)
        if not master_key:
            raise ValueError("CHAT_ENCRYPTION_KEY not configured in settings")

        # Ensure key is exactly 32 bytes for AES-256
        if len(master_key.encode()) != 32:
            # Derive a proper 32-byte key using PBKDF2
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b"gemnar_chat_salt_2024",  # Fixed salt
                iterations=100000,
                backend=default_backend(),
            )
            return kdf.derive(master_key.encode())
        return master_key.encode()

    @staticmethod
    def encrypt_message(message):
        """
        Encrypt a message using AES-256-GCM with embedded IV.

        Args:
            message (str): The message to encrypt

        Returns:
            str: Base64-encoded encrypted message with embedded IV and tag
        """
        try:
            key = ChatEncryption._get_master_key()
            iv = os.urandom(12)  # 12 bytes for GCM

            # Create cipher using AES-GCM for authenticated encryption
            cipher = Cipher(
                algorithms.AES(key), modes.GCM(iv), backend=default_backend()
            )
            encryptor = cipher.encryptor()

            # Encrypt the message
            message_bytes = message.encode("utf-8")
            encrypted = encryptor.update(message_bytes) + encryptor.finalize()

            # Combine IV + encrypted data + authentication tag
            combined = iv + encrypted + encryptor.tag

            return base64.b64encode(combined).decode("utf-8")
        except Exception as e:
            raise Exception(f"Failed to encrypt message: {str(e)}")

    @staticmethod
    def decrypt_message(encrypted_b64):
        """
        Decrypt a message using AES-256-GCM with embedded IV.

        Args:
            encrypted_b64 (str): Base64-encoded encrypted message with IV and tag

        Returns:
            str: Decrypted message
        """
        try:
            key = ChatEncryption._get_master_key()
            combined = base64.b64decode(encrypted_b64)

            # Extract IV, encrypted data, and tag
            iv = combined[:12]
            encrypted_data = combined[12:-16]
            tag = combined[-16:]

            # Create cipher
            cipher = Cipher(
                algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend()
            )
            decryptor = cipher.decryptor()

            # Decrypt the message
            decrypted = decryptor.update(encrypted_data) + decryptor.finalize()

            return decrypted.decode("utf-8")
        except Exception as e:
            raise Exception(f"Failed to decrypt message: {str(e)}")
