import hashlib
import json
from typing import Any

from app.modules.billing.application.services.i_request_hasher import IRequestHasher


class Sha256RequestHasher(IRequestHasher):
    def hash(self, payload: dict[str, Any]) -> str:
        normalized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

