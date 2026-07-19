import hashlib
import hmac


def verify_meta_signature(payload: bytes, signature_header: str, app_secret: str) -> bool:
    expected = "sha256=" + hmac.new(app_secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header)
