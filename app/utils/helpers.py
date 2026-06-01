from __future__ import annotations

import json
from typing import Any


def to_json(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, default=str)


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))
