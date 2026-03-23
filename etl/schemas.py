"""Schemas leves do pipeline ETL."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(slots=True)
class LarcWhitelistEntry:
    source: str
    versao: str
    marca: str
    modelo: str
    codigo_ittf: str
    tipo: str
    cores: list[str]
    aprovado: bool
    valido_desde: str
    valido_ate: str | None
    scraped_at: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)
