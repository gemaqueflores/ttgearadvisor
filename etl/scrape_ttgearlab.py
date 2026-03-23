"""Scraping inicial do TTGearLab para blades."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from common import load_json, normalize_whitespace, resolve_repo_path, write_json

try:
    import httpx
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover
    httpx = None
    BeautifulSoup = None


CONFIG_PATH = resolve_repo_path("etl/ttgearlab_configs.json")
DEFAULT_OUTPUT = resolve_repo_path("data/raw/ttgearlab_blade.json")


@dataclass(slots=True)
class TTGearLabSource:
    source_url: str
    enabled: bool = True
    table_index: int = 0


def load_sources(config_path: Path = CONFIG_PATH) -> list[TTGearLabSource]:
    """Carrega fontes configuradas do TTGearLab."""

    raw_sources = load_json(config_path, default=[])
    return [TTGearLabSource(**item) for item in raw_sources]


def fetch_html(source_url: str) -> str:
    """Busca HTML remoto ou local."""

    potential_file = resolve_repo_path(source_url)
    if potential_file.exists():
        return potential_file.read_text(encoding="utf-8")

    if httpx is None:
        raise RuntimeError(
            "httpx/beautifulsoup4 nao estao instalados. Rode `pip install -r etl/requirements.txt`.",
        )

    response = httpx.get(source_url, timeout=20.0, follow_redirects=True)
    response.raise_for_status()
    return response.text


def parse_float(value: str | None) -> float | None:
    """Extrai float de uma celula."""

    if not value:
        return None

    normalized = value.replace(",", ".")
    import re

    match = re.search(r"\d+(?:\.\d+)?", normalized)
    return float(match.group()) if match else None


def extract_rows_from_html(html: str, table_index: int = 0) -> list[dict[str, str]]:
    """Extrai linhas de tabela do TTGearLab."""

    if BeautifulSoup is None:
        raise RuntimeError(
            "beautifulsoup4 nao esta instalado. Rode `pip install -r etl/requirements.txt`.",
        )

    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")
    if table_index >= len(tables):
        return []

    table = tables[table_index]
    headers = [normalize_whitespace(cell.get_text(" ", strip=True)) for cell in table.find_all("th")]
    rows: list[dict[str, str]] = []

    for row in table.find_all("tr"):
        cells = row.find_all("td")
        if not cells or len(cells) != len(headers):
            continue

        rows.append(
            {
                headers[index]: normalize_whitespace(cell.get_text(" ", strip=True))
                for index, cell in enumerate(cells)
            }
        )

    return rows


def build_record(row: dict[str, str], source_url: str) -> dict:
    """Converte linha do TTGearLab para schema intermediario."""

    return {
        "source": "ttgearlab",
        "source_url": source_url,
        "marca": row.get("Brand") or row.get("Marca") or "",
        "modelo": row.get("Model") or row.get("Modelo") or "",
        "lab": {
            "Ep": parse_float(row.get("Ep")),
            "Ec": parse_float(row.get("Ec")),
            "Vp": parse_float(row.get("Vp")),
            "Vl": parse_float(row.get("Vl")),
            "frequencia_hz": parse_float(row.get("Frequency")),
            "metodo": row.get("Method"),
        },
        "scraped_at": None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Executa scraping inicial do TTGearLab para blades.",
    )
    parser.add_argument(
        "--config",
        default=str(CONFIG_PATH),
        help="Caminho do ttgearlab_configs.json",
    )
    parser.add_argument(
        "--include-disabled",
        action="store_true",
        help="Processa tambem entradas marcadas como enabled=false",
    )
    args = parser.parse_args()

    sources = load_sources(resolve_repo_path(args.config))
    active_sources = [source for source in sources if source.enabled or args.include_disabled]

    records: list[dict] = []
    failures: list[dict] = []

    for source in active_sources:
        try:
            html = fetch_html(source.source_url)
            rows = extract_rows_from_html(html, table_index=source.table_index)
            records.extend(build_record(row, source.source_url) for row in rows)
        except Exception as exc:  # pragma: no cover
            failures.append({"url": source.source_url, "error": str(exc)})

    write_json(DEFAULT_OUTPUT, records)

    print(
        "Scraping do TTGearLab finalizado. "
        f"fontes={len(active_sources)}, records={len(records)}, falhas={len(failures)}",
    )

    if failures:
        print("Falhas detectadas:")
        for failure in failures:
            print(f'url={failure["url"]}')
            print(f'erro={failure["error"]}')


if __name__ == "__main__":
    main()
