import base64
from math import floor
from time import time


def decrypt_url(encrypted_b64: str, timestamp: int | None = None) -> str:
    if timestamp is None:
        timestamp = int(time())

    key = f"SECRET_KEY_{floor(timestamp / 3600)}"
    key_bytes = key.encode()

    encrypted_bytes = base64.b64decode(encrypted_b64)

    decrypted = bytearray(len(encrypted_bytes))
    for i, byte in enumerate(encrypted_bytes):
        decrypted[i] = byte ^ key_bytes[i % len(key_bytes)]

    return decrypted.decode()
