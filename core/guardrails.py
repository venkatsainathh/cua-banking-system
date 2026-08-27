import re
from typing import Any
from core.models import ActionType

class SecurityPolicyException(Exception):
    pass

class SafetyGuardrails:
    ALLOWED_HOSTS = ["127.0.0.1:8000", "localhost:8000"]
    ALLOWED_ACTIONS = {
        ActionType.NAVIGATE,
        ActionType.FILL,
        ActionType.CLICK,
        ActionType.SELECT,
        ActionType.WAIT_FOR_ELEMENT,
        ActionType.EXTRACT,
    }

    SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
    CARD_PATTERN = re.compile(r"\b(?:\d{4}-){3}\d{4}\b|\b\d{16}\b")
    SECRET_KEY_PATTERN = re.compile(r"(?i)(password|secret|token|apikey)\s*[:=]\s*['\"]?([^'\"\s]+)")

    @classmethod
    def validate_navigation(cls, url: str):
        if not any(host in url for host in cls.ALLOWED_HOSTS):
            raise SecurityPolicyException(f"Navigation blocked: URL '{url}' is outside allowlist {cls.ALLOWED_HOSTS}")

    @classmethod
    def validate_action(cls, action: ActionType, is_irreversible: bool = False):
        if action not in cls.ALLOWED_ACTIONS:
            raise SecurityPolicyException(f"Action '{action}' is strictly forbidden by policy.")

    @classmethod
    def sanitize_data(cls, data: Any) -> Any:
        if isinstance(data, str):
            sanitized = cls.SSN_PATTERN.sub("[REDACTED_SSN]", data)
            sanitized = cls.CARD_PATTERN.sub("[REDACTED_PAN]", sanitized)
            sanitized = cls.SECRET_KEY_PATTERN.sub(r"\1: [REDACTED_SECRET]", sanitized)
            return sanitized
        elif isinstance(data, dict):
            return {k: cls.sanitize_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [cls.sanitize_data(item) for item in data]
        return data