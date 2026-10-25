import hashlib
import json
from dataclasses import asdict

from src.application.schemas import MarketChartRequest


class Sha256IdempotencyKeyGenerator:
    def __call__(self, data: MarketChartRequest) -> str:
        serialized = json.dumps(
            asdict(data),
            sort_keys=True,
            separators=(",", ":"),
        )

        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()