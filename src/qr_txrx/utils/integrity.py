import hashlib


def sha256(data: bytes) -> str:
    """Return the SHA-256 digest of data as a hexadecimal string."""
    return hashlib.sha256(data).hexdigest()
