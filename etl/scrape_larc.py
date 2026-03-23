"""Scraper automatico da LARC ITTF.

Estrategias:
1. Primaria: PDF oficial da FFTT com URL trimestral previsivel
2. Fallback: Playwright navegando na SPA do equipment.ittf.com e capturando a API interna
"""

from __future__ import annotations

import argparse
import asyncio
import io
import re
import sys
from collections import defaultdict
from dataclasses import asdict
from datetime import date
from pathlib import Path

import requests

from common import normalize_whitespace, resolve_repo_path, write_json
from schemas import LarcWhitelistEntry

try:
    import pdfplumber
except ImportError:  # pragma: no cover
    pdfplumber = None

try:
    from playwright.async_api import async_playwright
except ImportError:  # pragma: no cover
    async_playwright = None


LARC_QUARTER_MONTHS = [1, 4, 7, 10]
DEFAULT_OUTPUT = resolve_repo_path("data/raw/larc_whitelist.json")
PLAYWRIGHT_URL = "https://equipment.ittf.com/#/equipment/racket_coverings"
PLAYWRIGHT_ENDPOINT_FRAGMENT = "Equipment_RacketCoverings/all_list"


def get_versao(year: int, month: int) -> str:
    """Formata a versao YYYY-MM."""

    return f"{year}-{month:02d}"


def get_larc_url(year: int | None = None, month: int | None = None) -> str:
    """Constroi a URL previsivel do PDF da FFTT."""

    today = date.today()
    target_year = year or today.year
    if month:
        quarter_month = month
    else:
        candidates = [value for value in LARC_QUARTER_MONTHS if value <= today.month]
        quarter_month = max(candidates) if candidates else 10

    return (
        "https://www.fftt.com/wp-content/uploads/"
        f"{target_year}/{quarter_month:02d}/"
        f"liste-des-revetements-autorises-{target_year}.pdf"
    )


def download_pdf(url: str) -> bytes:
    """Faz download do PDF da FFTT."""

    response = requests.get(url, timeout=30)
    if response.status_code == 404:
        raise FileNotFoundError(f"PDF nao encontrado na URL: {url}")
    response.raise_for_status()
    return response.content


def normalize_pimple_type(raw: str) -> str:
    """Normaliza o tipo de pino para o contrato interno."""

    normalized = normalize_whitespace(raw).lower()
    mapping = {
        "in": "IN",
        "inverted": "IN",
        "out": "OUT",
        "short": "OUT",
        "long": "LONG",
        "anti": "ANTI",
    }
    return mapping.get(normalized, normalized.upper() if normalized else "")


def _dedupe_records(records: list[dict]) -> list[dict]:
    """Deduplica por marca + modelo + codigo e agrega cores."""

    deduped: dict[tuple[str, str, str], dict] = {}

    for record in records:
        key = (
            normalize_whitespace(record.get("marca", "")).lower(),
            normalize_whitespace(record.get("modelo", "")).lower(),
            normalize_whitespace(record.get("codigo_ittf", "")).lower(),
        )
        if key not in deduped:
            deduped[key] = record
            continue

        existing = deduped[key]
        merged_colors = existing.get("cores", [])[:]
        for color in record.get("cores", []):
            if color not in merged_colors:
                merged_colors.append(color)
        existing["cores"] = merged_colors
        if not existing.get("valido_ate") and record.get("valido_ate"):
            existing["valido_ate"] = record["valido_ate"]

    return list(deduped.values())


def extract_larc_from_pdf(pdf_bytes: bytes, versao: str) -> list[dict]:
    """Extrai a tabela principal do PDF oficial da FFTT."""

    if pdfplumber is None:
        raise RuntimeError(
            "pdfplumber nao esta instalado. Instale as dependencias do ETL para processar o PDF da LARC.",
        )

    registros: dict[tuple[str, str, str], dict] = defaultdict(
        lambda: asdict(
            LarcWhitelistEntry(
                source="ittf_larc",
                versao=versao,
                marca="",
                modelo="",
                codigo_ittf="",
                tipo="",
                cores=[],
                aprovado=True,
                valido_desde=versao,
                valido_ate=None,
                scraped_at=date.today().isoformat(),
            )
        )
    )

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if not table:
                continue

            for row in table:
                if not row or len(row) < 5:
                    continue

                brand, product, code, pimple_type, color, *rest = row
                brand = normalize_whitespace(brand or "")
                product = normalize_whitespace(product or "")
                code = normalize_whitespace(code or "")

                if not brand or not product or not code:
                    continue
                if brand.lower() == "brand":
                    continue

                key = (brand.lower(), product.lower(), code.lower())
                record = registros[key]
                record["marca"] = brand
                record["modelo"] = product
                record["codigo_ittf"] = code
                record["tipo"] = normalize_pimple_type(pimple_type or "")

                expires = normalize_whitespace(rest[0] or "") if rest else ""
                record["valido_ate"] = expires if expires and expires != "-" else None

                normalized_color = normalize_whitespace(color or "")
                if normalized_color and normalized_color not in record["cores"]:
                    record["cores"].append(normalized_color)

    return list(registros.values())


async def fetch_larc_via_playwright(versao: str) -> list[dict]:
    """Fallback: navega na SPA da ITTF e intercepta a API interna."""

    if async_playwright is None:
        raise RuntimeError(
            "playwright nao esta instalado. Instale as dependencias do ETL para usar o fallback da SPA.",
        )

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()

        captured_payloads: list = []
        try:
            async with page.expect_response(
                lambda response: PLAYWRIGHT_ENDPOINT_FRAGMENT in response.url and response.status == 200,
                timeout=60000,
            ) as response_info:
                await page.goto(PLAYWRIGHT_URL, timeout=60000)
            response = await response_info.value
            payload = await response.json()
            if payload:
                response_url = response.url
                payloads_to_scan = payload if isinstance(payload, list) else [payload]
                total_count = None
                for payload_item in payloads_to_scan:
                    if isinstance(payload_item, dict) and isinstance(payload_item.get("Count"), int):
                        total_count = payload_item["Count"]
                        break

                if total_count and total_count > 20:
                    expanded_url = re.sub(r"limit=\d+", f"limit={total_count}", response_url)
                    expanded_url = re.sub(r"skip=\d+", "skip=0", expanded_url)
                    expanded_response = await page.context.request.get(expanded_url, timeout=60000)
                    if not expanded_response.ok:
                        raise RuntimeError(
                            f"Falha ao expandir a captura da SPA: {expanded_response.status} {expanded_url}",
                        )
                    captured_payloads.append(await expanded_response.json())
                else:
                    captured_payloads.append(payload)
        finally:
            await browser.close()

    if not captured_payloads:
        raise RuntimeError("Playwright fallback nao capturou dados da API ITTF")

    return normalize_playwright_response(captured_payloads, versao)


def normalize_playwright_response(data: list, versao: str) -> list[dict]:
    """Normaliza o JSON capturado da API interna da SPA."""

    normalized_records: list[dict] = []

    for payload in data:
        payloads_to_scan = payload if isinstance(payload, list) else [payload]
        for payload_item in payloads_to_scan:
            if not isinstance(payload_item, dict):
                continue
            rows = payload_item.get("rows")
            if not isinstance(rows, list):
                continue

            for item in rows:
                brand = normalize_whitespace(item.get("BrandName", "") or item.get("brand", ""))
                product = normalize_whitespace(item.get("EquipmentName", "") or item.get("product", ""))
                code = normalize_whitespace(
                    str(
                        item.get("EquipmentCode")
                        or item.get("approvalCode")
                        or item.get("ITTFApprovalCode")
                        or ""
                    )
                )
                if not brand or not product or not code:
                    continue

                colors_raw = item.get("ColorsList") or item.get("colors") or ""
                if isinstance(colors_raw, str):
                    colors = [normalize_whitespace(color) for color in colors_raw.split(",") if normalize_whitespace(color)]
                elif isinstance(colors_raw, list):
                    colors = [normalize_whitespace(str(color)) for color in colors_raw if normalize_whitespace(str(color))]
                else:
                    colors = []

                normalized_records.append(
                    {
                        "source": "ittf_larc",
                        "versao": versao,
                        "marca": brand,
                        "modelo": product,
                        "codigo_ittf": code,
                        "tipo": normalize_pimple_type(item.get("PimpleType", "") or item.get("pimpleType", "")),
                        "cores": colors,
                        "aprovado": bool(item.get("ApprovalStatus", True)),
                        "valido_desde": versao,
                        "valido_ate": item.get("ExpiresOn"),
                        "scraped_at": date.today().isoformat(),
                    }
                )

    deduped = _dedupe_records(normalized_records)
    return [record for record in deduped if record.get("aprovado") is True]


def try_pdf_strategy(year: int | None = None, month: int | None = None) -> list[dict]:
    """Tenta o PDF do trimestre atual e, se necessario, o trimestre anterior."""

    today = date.today()
    target_year = year or today.year

    if month and month not in LARC_QUARTER_MONTHS:
        raise ValueError("Mes invalido para LARC. Use apenas 1, 4, 7 ou 10.")

    quarters_to_try: list[tuple[int, int]] = []
    if month:
        quarters_to_try = [(target_year, month)]
    else:
        candidates = [value for value in LARC_QUARTER_MONTHS if value <= today.month]
        current_quarter = max(candidates) if candidates else 10
        quarters_to_try.append((target_year, current_quarter))
        current_index = LARC_QUARTER_MONTHS.index(current_quarter)
        if current_index > 0:
            quarters_to_try.append((target_year, LARC_QUARTER_MONTHS[current_index - 1]))
        else:
            quarters_to_try.append((target_year - 1, LARC_QUARTER_MONTHS[-1]))

    for attempt_year, attempt_month in quarters_to_try:
        url = get_larc_url(attempt_year, attempt_month)
        print(f"[LARC] Tentando PDF: {url}")
        try:
            pdf_bytes = download_pdf(url)
            versao = get_versao(attempt_year, attempt_month)
            registros = extract_larc_from_pdf(pdf_bytes, versao)
            print(f"[LARC] PDF extraido: {len(registros)} registros ({versao})")
            return registros
        except FileNotFoundError:
            print(f"[LARC] PDF nao encontrado para {attempt_year}-{attempt_month:02d}, tentando proximo...")
            continue

    raise RuntimeError("Nenhum PDF disponivel nos trimestres tentados")


def main() -> None:
    parser = argparse.ArgumentParser(description="Scraper automatico da LARC ITTF")
    parser.add_argument("--year", type=int, help="Ano da LARC (padrao: ano atual)")
    parser.add_argument("--month", type=int, help="Mes do trimestre (1/4/7/10)")
    parser.add_argument(
        "--mode",
        choices=["auto", "pdf", "playwright"],
        default="auto",
        help="Estrategia de obtencao",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help="Caminho do arquivo de saida",
    )
    args = parser.parse_args()

    registros: list[dict] = []

    if args.mode in {"auto", "pdf"}:
        try:
            registros = try_pdf_strategy(args.year, args.month)
        except RuntimeError as exc:
            if args.mode == "pdf":
                print(f"[LARC] ERRO: {exc}")
                sys.exit(1)
            print(f"[LARC] PDF falhou: {exc}. Ativando fallback Playwright...")

    if not registros and args.mode in {"auto", "playwright"}:
        today = date.today()
        candidates = [value for value in LARC_QUARTER_MONTHS if value <= today.month]
        version_month = args.month or (max(candidates) if candidates else 10)
        version_year = args.year or today.year
        versao = get_versao(version_year, version_month)
        registros = asyncio.run(fetch_larc_via_playwright(versao))
        print(f"[LARC] Playwright capturou: {len(registros)} registros")

    if not registros:
        print("[LARC] ERRO: nenhum dado obtido por nenhuma estrategia")
        sys.exit(1)

    output_path = resolve_repo_path(args.output)
    write_json(output_path, registros)
    print(f"[LARC] Salvo: {output_path} ({len(registros)} registros)")


if __name__ == "__main__":
    main()
