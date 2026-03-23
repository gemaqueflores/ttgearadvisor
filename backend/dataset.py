from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
UNIFIED_BLADE_PATH = REPO_ROOT / "data" / "unified" / "unified_blade.json"
UNIFIED_RUBBER_PATH = REPO_ROOT / "data" / "unified" / "unified_rubber.json"
LARC_PATH = REPO_ROOT / "data" / "raw" / "larc_whitelist.json"


def _load_json(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8-sig") as file:
        payload = json.load(file)

    return payload if isinstance(payload, list) else []


@lru_cache(maxsize=1)
def load_blades() -> list[dict[str, Any]]:
    return _load_json(UNIFIED_BLADE_PATH)


@lru_cache(maxsize=1)
def load_rubbers() -> list[dict[str, Any]]:
    return _load_json(UNIFIED_RUBBER_PATH)


@lru_cache(maxsize=1)
def load_larc() -> list[dict[str, Any]]:
    return _load_json(LARC_PATH)


def reload_datasets() -> None:
    load_blades.cache_clear()
    load_rubbers.cache_clear()
    load_larc.cache_clear()
