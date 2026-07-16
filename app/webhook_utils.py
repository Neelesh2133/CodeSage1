import hmac
import hashlib
from app.config import settings
#Github webhooks
def verify_github_signature(payload_body: bytes, signature_header: str | None) -> bool:
    """Verifies GitHub's HMAC-SHA256 webhook signature."""
    if not signature_header or not signature_header.startswith("sha256="):
        return False

    expected = hmac.new(
        settings.github_webhook_secret.encode(),
        payload_body,
        hashlib.sha256
    ).hexdigest()
    received = signature_header.removeprefix("sha256=")
    return hmac.compare_digest(expected, received)
