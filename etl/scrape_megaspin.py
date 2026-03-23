"""Scraper inicial do Megaspin para blades com ratings normalizados."""

from __future__ import annotations

import argparse
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

from common import load_json, normalize_whitespace, resolve_repo_path, write_json


DEFAULT_CONFIG_PATH = resolve_repo_path("etl/megaspin_configs.json")
DEFAULT_OUTPUT_PATH = resolve_repo_path("data/raw/megaspin_blade.json")


def fetch_source(source_url: str) -> str:
    """Carrega HTML local ou remoto."""

    possible_path = resolve_repo_path(source_url)
    if possible_path.exists():
        return possible_path.read_text(encoding="utf-8")

    response = httpx.get(source_url, timeout=30.0, follow_redirects=True)
    response.raise_for_status()
    return response.text


def parse_float(value: str | None) -> float | None:
    """Converte texto em float quando possivel."""

    if value is None:
        return None

    normalized = normalize_whitespace(value).replace(",", ".")
    normalized = normalized.replace("g", "").strip()
    if not normalized:
        return None

    try:
        return float(normalized)
    except ValueError:
        return None


def find_column_index(headers: list[str], aliases: list[str]) -> int | None:
    """Localiza o indice de uma coluna por lista de aliases."""

    normalized_headers = [normalize_whitespace(header).lower() for header in headers]
    for alias in aliases:
        alias_normalized = normalize_whitespace(alias).lower()
        if alias_normalized in normalized_headers:
            return normalized_headers.index(alias_normalized)
    return None


def parse_table(html: str, config: dict) -> list[dict]:
    """Extrai registros de uma tabela HTML configurada."""

    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")
    table_index = int(config.get("table_index", 0))
    if table_index >= len(tables):
        return []

    table = tables[table_index]
    rows = table.find_all("tr")
    if not rows:
        return []

    headers = [normalize_whitespace(cell.get_text(" ", strip=True)) for cell in rows[0].find_all(["th", "td"])]
    columns = config.get("columns", {})

    brand_index = find_column_index(headers, columns.get("brand", []))
    model_index = find_column_index(headers, columns.get("model", []))
    speed_index = find_column_index(headers, columns.get("speed", []))
    control_index = find_column_index(headers, columns.get("control", []))
    weight_index = find_column_index(headers, columns.get("weight_g", []))

    records: list[dict] = []
    for row in rows[1:]:
        cells = [normalize_whitespace(cell.get_text(" ", strip=True)) for cell in row.find_all(["th", "td"])]
        if not cells:
            continue

        brand = cells[brand_index] if brand_index is not None and brand_index < len(cells) else config.get("brand")
        model = cells[model_index] if model_index is not None and model_index < len(cells) else None
        if not brand or not model:
            continue

        speed = cells[speed_index] if speed_index is not None and speed_index < len(cells) else None
        control = cells[control_index] if control_index is not None and control_index < len(cells) else None
        weight = cells[weight_index] if weight_index is not None and weight_index < len(cells) else None

        records.append(
            {
                "source": "megaspin",
                "source_url": config.get("source_url"),
                "marca": brand,
                "modelo": model,
                "ratings": {
                    "velocidade": parse_float(speed),
                    "controle": parse_float(control),
                    "peso_g": parse_float(weight),
                },
                "scraped_at": None,
            }
        )

    return records


def main() -> None:
    parser = argparse.ArgumentParser(description="Extrai ratings de blades do Megaspin.")
    parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG_PATH),
        help="Caminho para o arquivo de configuracao JSON.",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help="Caminho do JSON de saida.",
    )
    parser.add_argument(
        "--include-disabled",
        action="store_true",
        help="Processa tambem configuracoes marcadas como desabilitadas.",
    )
    args = parser.parse_args()

    configs = load_json(Path(args.config), default=[])
    all_records: list[dict] = []
    failures = 0
    active_sources = 0

    for config in configs:
        if not config.get("enabled", False) and not args.include_disabled:
            continue

        active_sources += 1
        source_url = config.get("source_url")
        if not source_url:
            failures += 1
            continue

        try:
            html = fetch_source(source_url)
            all_records.extend(parse_table(html, config))
        except Exception:
            failures += 1

    write_json(Path(args.output), all_records)
    print(
        "Scraping Megaspin concluido. "
        f"fontes={active_sources}, records={len(all_records)}, falhas={failures}.",
    )


if __name__ == "__main__":
    main()
