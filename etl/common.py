"""Funcoes utilitarias compartilhadas pelo pipeline ETL."""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent


def ensure_parent_dir(path: Path) -> None:
    """Cria o diretorio pai do arquivo, se necessario."""

    path.parent.mkdir(parents=True, exist_ok=True)


def resolve_repo_path(path: str | Path) -> Path:
    """Resolve caminhos relativos sempre a partir da raiz do repositorio."""

    candidate = Path(path)
    if candidate.is_absolute():
        return candidate

    return REPO_ROOT / candidate


def load_json(path: Path, default: Any | None = None) -> Any:
    """Carrega um arquivo JSON com fallback opcional."""

    if not path.exists():
        if default is not None:
            return default
        raise FileNotFoundError(path)

    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: Any) -> None:
    """Escreve JSON formatado em UTF-8."""

    ensure_parent_dir(path)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def normalize_whitespace(value: str) -> str:
    """Compacta espacos e remove bordas."""

    sanitized = value.replace("\ufeff", "")
    return re.sub(r"\s+", " ", sanitized).strip()


def slugify_ascii(value: str) -> str:
    """Converte texto para slug ASCII simples."""

    normalized = unicodedata.normalize("NFKD", value)
    without_accents = normalized.encode("ascii", "ignore").decode("ascii")
    lowered = without_accents.lower()
    lowered = lowered.replace("&", " and ")
    lowered = re.sub(r"[^a-z0-9]+", "-", lowered)
    lowered = re.sub(r"-{2,}", "-", lowered)
    return lowered.strip("-")


def normalize_brand_name(value: str) -> str:
    """Normaliza o nome da marca para comparacao interna."""

    return slugify_ascii(normalize_whitespace(value))


def normalize_model_name(value: str) -> str:
    """Normaliza o nome do modelo preservando apenas o essencial."""

    base_value = normalize_whitespace(value)
    base_value = re.sub(r"\biii\b", "3", base_value, flags=re.IGNORECASE)
    base_value = re.sub(r"\bii\b", "2", base_value, flags=re.IGNORECASE)
    base_value = re.sub(r"\biv\b", "4", base_value, flags=re.IGNORECASE)
    base_value = base_value.replace("+", " plus ")
    return slugify_ascii(base_value)


def build_normalized_id(brand: str, model: str) -> str:
    """Gera o ID final em kebab-case."""

    normalized_brand = normalize_brand_name(brand)
    normalized_model = normalize_model_name(model)
    return f"{normalized_brand}-{normalized_model}".strip("-")
