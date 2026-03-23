"""Scraping inicial de fabricantes com configuracao por marca."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Literal
from urllib.parse import urljoin

from common import load_json, normalize_whitespace, resolve_repo_path, write_json

try:
    import httpx
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover - dependencias instaladas na Fase 1 completa
    httpx = None
    BeautifulSoup = None


CONFIG_PATH = resolve_repo_path("etl/manufacturer_configs.json")
DEFAULT_BLADE_OUTPUT = resolve_repo_path("data/raw/fabricante_blade.json")
DEFAULT_RUBBER_OUTPUT = resolve_repo_path("data/raw/fabricante_rubber.json")


@dataclass(slots=True)
class ManufacturerSource:
    brand: str
    category: Literal["blade", "rubber"]
    source_url: str
    parser: str = "generic_table"
    enabled: bool = True
    table_index: int = 0
    column_aliases: dict[str, str] | None = None
    note: str | None = None


TODAY = date.today().isoformat()


def load_sources(config_path: Path = CONFIG_PATH) -> list[ManufacturerSource]:
    """Carrega a lista de fontes configuradas para scraping."""

    raw_sources = load_json(config_path, default=[])
    return [ManufacturerSource(**item) for item in raw_sources]


def fetch_html(source_url: str) -> str:
    """Busca HTML remoto ou local com timeout curto."""

    potential_file = resolve_repo_path(source_url)
    if potential_file.exists():
        return potential_file.read_text(encoding="utf-8")

    if source_url.startswith("file://"):
        file_path = Path(source_url.removeprefix("file://"))
        return file_path.read_text(encoding="utf-8")

    if httpx is None:
        raise RuntimeError(
            "httpx/beautifulsoup4 nao estao instalados. Rode `pip install -r etl/requirements.txt`.",
        )

    response = httpx.get(source_url, timeout=20.0, follow_redirects=True)
    response.raise_for_status()
    return response.text


def normalize_headers(
    headers: list[str],
    aliases: dict[str, str] | None = None,
) -> list[str]:
    """Normaliza nomes de colunas com aliases configuraveis."""

    alias_map = {key.lower(): value for key, value in (aliases or {}).items()}
    normalized: list[str] = []

    for header in headers:
        key = normalize_whitespace(header).lower()
        normalized.append(alias_map.get(key, normalize_whitespace(header)))

    return normalized


def extract_rows_from_html(
    html: str,
    table_index: int = 0,
    column_aliases: dict[str, str] | None = None,
) -> list[dict[str, str]]:
    """Extrai linhas genericas de tabelas HTML para posterior mapeamento.

    Esta etapa ainda e um parser generico. Cada marca podera receber regras
    especificas depois, mas ja deixa um ponto unico de evolucao.
    """

    if BeautifulSoup is None:
        raise RuntimeError(
            "beautifulsoup4 nao esta instalado. Rode `pip install -r etl/requirements.txt`.",
        )

    soup = BeautifulSoup(html, "html.parser")
    rows: list[dict[str, str]] = []

    tables = soup.find_all("table")
    if table_index >= len(tables):
        return []

    table = tables[table_index]
    header_cells = [normalize_whitespace(cell.get_text(" ", strip=True)) for cell in table.find_all("th")]
    header_cells = normalize_headers(header_cells, aliases=column_aliases)
    if not header_cells:
        return []

    for row in table.find_all("tr"):
        cells = row.find_all("td")
        if not cells or len(cells) != len(header_cells):
            continue

        rows.append(
            {
                header_cells[index]: normalize_whitespace(cell.get_text(" ", strip=True))
                for index, cell in enumerate(cells)
            }
        )

    return rows


def build_placeholder_blade_record(source: ManufacturerSource, row: dict[str, str]) -> dict:
    """Converte uma linha generica em schema intermediario de blade."""

    brand = row.get("Brand") or row.get("Marca") or source.brand
    model = row.get("Model") or row.get("Name") or row.get("Produto") or "desconhecido"
    handle_values = row.get("Handles", "")
    handle_list = parse_handles(handle_values)
    composition_value = row.get("Composition", "")
    head_width, head_height = parse_head_size(row.get("Head Size") or row.get("Size"))
    total_plies = parse_int(row.get("Plies"))

    return {
        "source": "fabricante",
        "source_url": source.source_url,
        "marca": brand,
        "modelo": model,
        "fisica": {
            "peso_g": parse_float(row.get("Weight")),
            "espessura_mm": parse_float(row.get("Thickness")),
            "largura_mm": head_width,
            "altura_mm": head_height,
            "cabos_disponiveis": handle_list,
        },
        "composicao": {
            "total_camadas": total_plies,
            "estrutura": [],
            "tem_carbono": None,
            "tipo_carbono": composition_value or None,
            "posicao_carbono": None,
            "camadas_carbono": None,
            "fibra_especial": None,
        },
        "scraped_at": TODAY,
    }


def build_placeholder_rubber_record(source: ManufacturerSource, row: dict[str, str]) -> dict:
    """Converte uma linha generica em schema intermediario de rubber."""

    brand = row.get("Brand") or row.get("Marca") or source.brand
    model = row.get("Model") or row.get("Name") or row.get("Produto") or "desconhecido"
    thicknesses = parse_thicknesses(row.get("Thickness", "") or row.get("Sponge", ""))
    hardness_value = row.get("Hardness", "")
    hardness_scale = infer_hardness_scale(hardness_value)
    hardness_degrees = parse_float(hardness_value)

    return {
        "source": "fabricante",
        "source_url": source.source_url,
        "marca": brand,
        "modelo": model,
        "tipo": infer_rubber_type(row.get("Type", "")),
        "fisica": {
            "espessuras_disponiveis_mm": thicknesses,
            "dureza_esponja_graus": hardness_degrees,
            "escala_dureza": hardness_scale,
            "peso_por_espessura_g": None,
            "diametro_topsheet_mm": None,
        },
        "aprovacao_ittf_declarada": has_keyword(row.get("Approval", ""), ["ittf", "approved"]),
        "scraped_at": TODAY,
    }


def parse_float(value: str | None) -> float | None:
    """Extrai o primeiro numero decimal de uma string."""

    if not value:
        return None

    normalized = value.replace(",", ".")
    match = __import__("re").search(r"\d+(?:\.\d+)?", normalized)
    return float(match.group()) if match else None


def parse_head_size(value: str | None) -> tuple[float | None, float | None]:
    """Extrai largura e altura de medidas como 150 x 157 mm."""

    if not value:
        return None, None

    normalized = normalize_whitespace(value).lower().replace(",", ".")
    matches = re.findall(r"\d+(?:\.\d+)?", normalized)
    if len(matches) < 2:
        return None, None

    first = float(matches[0])
    second = float(matches[1])
    return (min(first, second), max(first, second))


def parse_int(value: str | None) -> int | None:
    """Extrai o primeiro inteiro de uma string."""

    parsed = parse_float(value)
    return int(parsed) if parsed is not None else None


def parse_thicknesses(value: str) -> list[str]:
    """Extrai lista simples de espessuras ou MAX."""

    if not value:
        return []

    normalized = value.upper().replace(";", ",").replace("/", ",")
    normalized = normalized.replace("，", ",")
    parts = [item.strip() for item in normalized.split(",")]
    parsed: list[str] = []
    for part in parts:
        if not part:
            continue
        if "MAX" in part:
            parsed.append("MAX")
            continue
        matches = re.findall(r"\d+(?:[.,]\d+)?", part)
        for match in matches:
            parsed.append(match.replace(",", "."))
    return parsed


def parse_handles(value: str) -> list[str]:
    """Normaliza codigos de cabo mais comuns de fabricantes."""

    if not value:
        return []

    normalized = normalize_whitespace(value).upper()
    raw_parts = [item.strip() for item in re.split(r"[/,|]", normalized) if item.strip()]
    alias_map = {
        "FLARE": "FL",
        "FLARED": "FL",
        "STRAIGHT": "ST",
        "ANATOMIC": "AN",
        "PEN": "JP",
        "PENHOLD": "JP",
        "JPN": "JP",
        "CHINESE PENHOLD": "CN",
        "C PEN": "CN",
        "CS": "CN",
    }

    handles: list[str] = []
    for part in raw_parts:
        handles.append(alias_map.get(part, part))

    return list(dict.fromkeys(handles))


def has_keyword(value: str, keywords: list[str]) -> bool:
    """Verifica se um texto contem qualquer palavra-chave."""

    lowered = value.lower()
    return any(keyword in lowered for keyword in keywords)


def build_blade_record_from_fields(
    source: ManufacturerSource,
    *,
    brand: str,
    model: str,
    weight: str | None = None,
    thickness: str | None = None,
    head_size: str | None = None,
    plies: str | None = None,
    composition_value: str | None = None,
    handles: str | None = None,
) -> dict:
    """Monta schema intermediario de blade a partir de campos ja extraidos."""

    row = {
        "Brand": brand,
        "Model": model,
        "Weight": weight or "",
        "Thickness": thickness or "",
        "Head Size": head_size or "",
        "Plies": plies or "",
        "Composition": composition_value or "",
        "Handles": handles or "",
    }
    return build_placeholder_blade_record(source, row)


def extract_text(html: str) -> str:
    if BeautifulSoup is None:
        raise RuntimeError(
            "beautifulsoup4 nao esta instalado. Rode `pip install -r etl/requirements.txt`.",
        )
    soup = BeautifulSoup(html, "html.parser")
    return normalize_whitespace(soup.get_text(" ", strip=True))


def extract_key_value_table(html: str, table_index: int = 0) -> dict[str, str]:
    """Extrai tabelas simples no formato Label/Value."""

    if BeautifulSoup is None:
        raise RuntimeError(
            "beautifulsoup4 nao esta instalado. Rode `pip install -r etl/requirements.txt`.",
        )

    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")
    if table_index >= len(tables):
        return {}

    data: dict[str, str] = {}
    for row in tables[table_index].find_all("tr"):
        cells = [normalize_whitespace(cell.get_text(" ", strip=True)) for cell in row.find_all(["th", "td"])]
        if len(cells) >= 2:
            data[cells[0]] = cells[1]
    return data


def parse_butterfly_blade_detail(source: ManufacturerSource, html: str) -> list[dict]:
    """Extrai specs de paginas oficiais de blade da Butterfly Global."""

    data = extract_key_value_table(html, table_index=source.table_index)
    if not data:
        return []

    secondary = extract_key_value_table(html, table_index=source.table_index + 1)
    handle_blob = " ".join(secondary.values())
    handles = " / ".join(
        handle_code
        for handle_code in ["FL", "ST", "AN", "JP", "CN"]
        if re.search(rf"\b{handle_code}\b", handle_blob)
    )

    model = data.get("Name", "desconhecido")
    composition_value = data.get("Structure")
    record = build_blade_record_from_fields(
        source,
        brand=source.brand,
        model=model,
        thickness=data.get("Thickness"),
        head_size=data.get("Head size"),
        composition_value=composition_value,
        handles=handles,
        plies=None,
    )
    enrich_blade_composition_from_text(record, f"{model} {composition_value or ''}")
    return [record]


def parse_nittaku_blade_detail(source: ManufacturerSource, html: str) -> list[dict]:
    """Extrai specs de paginas oficiais da Nittaku em formato textual compacto."""

    soup = BeautifulSoup(html, "html.parser")
    text = normalize_whitespace(soup.get_text(" ", strip=True))
    ascii_text = text.encode("ascii", "ignore").decode("ascii")
    h1 = soup.find("h1")
    title_text = normalize_whitespace(h1.get_text(" ", strip=True)) if h1 else ""
    title_match = re.search(r"[A-Z][A-Z0-9\s\-]{2,}", title_text)
    size_match = re.search(r"(\d{3})(\d{3})mm", ascii_text)
    weight_match = re.search(r"\b(\d{2,3})g\b", ascii_text)
    thickness_match = re.search(r"(\d+\.\d+)mm", ascii_text)
    handle_matches = re.findall(r"\b(FL|ST|JP|PEN|AN|CN)\b", ascii_text)

    model = title_match.group(0).strip().title() if title_match else "desconhecido"
    head_size = f"{size_match.group(1)} x {size_match.group(2)} mm" if size_match else None
    weight = f"{weight_match.group(1)} g" if weight_match else None
    thickness = f"{thickness_match.group(1)} mm" if thickness_match else None
    handles = " / ".join(list(dict.fromkeys(handle_matches)))

    plies = None
    model_upper = model.upper()
    after_model = ascii_text[ascii_text.find(model_upper):] if model_upper in ascii_text else ascii_text
    plies_match = re.search(r"\b([3579])\b\s+\d{6}mm", after_model)
    if plies_match:
        plies = plies_match.group(1)

    composition_value = "Wood"
    lowered = text.lower()
    if "inner" in lowered and "carbon" in lowered:
        composition_value = "Inner Carbon"
    elif "outer" in lowered and "carbon" in lowered:
        composition_value = "Outer Carbon"

    record = build_blade_record_from_fields(
        source,
        brand=source.brand,
        model=model,
        weight=weight,
        thickness=thickness,
        head_size=head_size,
        plies=plies,
        composition_value=composition_value,
        handles=handles,
    )
    enrich_blade_composition_from_text(record, f"{model} {composition_value}")
    return [record]


def parse_total_plies_from_structure(value: str | None) -> int | None:
    if not value:
        return None
    normalized = normalize_whitespace(value).lower().replace("×", "x")
    wood_plus_carbon = re.search(r"(\d+)\s*-\s*ply\s*wood\s*\+\s*(\d+)", normalized)
    if wood_plus_carbon:
        return int(wood_plus_carbon.group(1)) + int(wood_plus_carbon.group(2))
    pair = re.search(r"(\d+)\s*[-+x]\s*(\d+)", normalized)
    if pair:
        return int(pair.group(1)) + int(pair.group(2))
    ply = re.findall(r"(\d+)\s*-\s*ply", normalized)
    if ply:
        return sum(int(item) for item in ply)
    standalone = re.search(r"\b(\d+)\b", normalized)
    return int(standalone.group(1)) if standalone else None


def parse_carbon_layers_from_structure(value: str | None) -> int | None:
    if not value:
        return None
    normalized = normalize_whitespace(value).lower().replace("×", "x")
    wood_plus_carbon = re.search(r"\d+\s*-\s*ply\s*wood\s*\+\s*(\d+)", normalized)
    if wood_plus_carbon:
        return int(wood_plus_carbon.group(1))
    pair = re.search(r"(\d+)\s*[-+x]\s*(\d+)", normalized)
    if pair:
        return int(pair.group(2))
    carbon_match = re.search(r"(\d+)\s+(?:arylate-)?carbon", normalized)
    return int(carbon_match.group(1)) if carbon_match else None


def extract_fiber_special(value: str | None) -> str | None:
    if not value:
        return None
    lowered = value.lower()
    mapping = [
        ("arylate-carbon", "Arylate-Carbon"),
        ("alc", "ALC"),
        ("super alc", "Super ALC"),
        ("super zlc", "Super ZLC"),
        ("zlc", "ZLC"),
        ("cnf", "CNF"),
        ("caf", "CAF"),
        ("carbon", "Carbon"),
    ]
    for needle, label in mapping:
        if needle in lowered:
            return label
    return None


def enrich_blade_composition_from_text(record: dict, text: str) -> None:
    composition = record.get("composicao", {})
    normalized = normalize_whitespace(text)
    lowered = normalized.lower()
    total_plies = composition.get("total_camadas") or parse_total_plies_from_structure(normalized)
    composition["total_camadas"] = total_plies

    if "carbon" in lowered or "alc" in lowered or "zlc" in lowered or "cnf" in lowered or "caf" in lowered:
        composition["tem_carbono"] = True
    elif normalized:
        composition["tem_carbono"] = False

    composition["camadas_carbono"] = parse_carbon_layers_from_structure(normalized)
    composition["fibra_especial"] = extract_fiber_special(normalized)
    if composition.get("tipo_carbono") in (None, ""):
        composition["tipo_carbono"] = normalized or None

    if "inner" in lowered or "innerforce" in lowered or "innerfiber" in lowered:
        composition["posicao_carbono"] = "inner"
    elif "outer" in lowered or "outerforce" in lowered or "outerfiber" in lowered:
        composition["posicao_carbono"] = "outer"


def parse_butterfly_blade_listing(source: ManufacturerSource, html: str) -> list[dict]:
    if BeautifulSoup is None:
        raise RuntimeError(
            "beautifulsoup4 nao esta instalado. Rode `pip install -r etl/requirements.txt`.",
        )

    soup = BeautifulSoup(html, "html.parser")
    detail_urls: list[str] = []
    seen: set[str] = set()
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]
        if "/en/products/detail/" not in href:
            continue
        absolute = urljoin(source.source_url, href)
        if absolute in seen:
            continue
        seen.add(absolute)
        detail_urls.append(absolute)

    records: list[dict] = []
    for detail_url in detail_urls:
        detail_source = ManufacturerSource(
            brand=source.brand,
            category="blade",
            source_url=detail_url,
            parser="butterfly_global_blade_detail",
            enabled=True,
            table_index=source.table_index,
        )
        detail_html = fetch_html(detail_url)
        records.extend(parse_butterfly_blade_detail(detail_source, detail_html))
    return records


def parse_butterfly_rubber_detail(source: ManufacturerSource, html: str) -> list[dict]:
    data = extract_key_value_table(html, table_index=source.table_index)
    secondary = extract_key_value_table(html, table_index=source.table_index + 1)
    if not data:
        return []

    model = data.get("Name", "desconhecido")
    hardness = secondary.get("Sponge hardness")
    thicknesses = secondary.get("Sponge thickness")
    rubber_type = data.get("Type", "")

    record = {
        "source": "fabricante",
        "source_url": source.source_url,
        "marca": source.brand,
        "modelo": model,
        "tipo": infer_rubber_type(rubber_type),
        "fisica": {
            "espessuras_disponiveis_mm": parse_thicknesses(thicknesses or ""),
            "dureza_esponja_graus": parse_float(hardness),
            "escala_dureza": None,
            "peso_por_espessura_g": None,
            "diametro_topsheet_mm": None,
        },
        "aprovacao_ittf_declarada": False,
        "scraped_at": TODAY,
    }
    return [record]


def parse_butterfly_rubber_listing(source: ManufacturerSource, html: str) -> list[dict]:
    if BeautifulSoup is None:
        raise RuntimeError(
            "beautifulsoup4 nao esta instalado. Rode `pip install -r etl/requirements.txt`.",
        )

    soup = BeautifulSoup(html, "html.parser")
    detail_urls: list[str] = []
    seen: set[str] = set()
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]
        if "/en/products/detail/" not in href:
            continue
        absolute = urljoin(source.source_url, href)
        if absolute in seen:
            continue
        seen.add(absolute)
        detail_urls.append(absolute)

    records: list[dict] = []
    for detail_url in detail_urls:
        detail_source = ManufacturerSource(
            brand=source.brand,
            category="rubber",
            source_url=detail_url,
            parser="butterfly_global_rubber_detail",
            enabled=True,
            table_index=source.table_index,
        )
        detail_html = fetch_html(detail_url)
        records.extend(parse_butterfly_rubber_detail(detail_source, detail_html))
    return records


def parse_dhs_blade_detail(source: ManufacturerSource, html: str) -> list[dict]:
    if BeautifulSoup is None:
        raise RuntimeError(
            "beautifulsoup4 nao esta instalado. Rode `pip install -r etl/requirements.txt`.",
        )

    soup = BeautifulSoup(html, "html.parser")
    title_node = soup.find("h1") or soup.find("div", class_="product-name") or soup.find("title")
    title = normalize_whitespace(title_node.get_text(" ", strip=True)) if title_node else ""
    model = title.replace("DHS Table Tennis Equipment", "").replace("Details", "").strip()
    model = re.sub(r"^DHS\s+", "", model).strip()
    text = extract_text(html)

    table = soup.find("table")
    details: dict[str, str] = {}
    if table:
        for row in table.find_all("tr"):
            cells = [normalize_whitespace(cell.get_text(" ", strip=True)) for cell in row.find_all(["th", "td"])]
            if len(cells) >= 3:
                details[cells[0]] = cells[2]
            elif len(cells) == 2:
                details[cells[0]] = cells[1]

    composition_text = ""
    detail_match = re.search(r"(\d+\s*layers?\s*\([^)]+\))", text, flags=re.I)
    if detail_match:
        composition_text = detail_match.group(1)
    elif "aryl-carbon" in text.lower():
        composition_text = "Aryl-Carbon"

    if details.get("Number of Layers"):
        composition_text = f"{details['Number of Layers']} {composition_text}".strip()

    record = build_blade_record_from_fields(
        source,
        brand=source.brand,
        model=model or "desconhecido",
        weight=details.get("approximate weight (g)"),
        thickness=details.get("thickness (mm)"),
        plies=details.get("Number of Layers"),
        composition_value=composition_text,
    )
    enrich_blade_composition_from_text(record, f"{model} {composition_text} {text}")
    return [record]


def parse_dhs_blade_listing(source: ManufacturerSource, html: str) -> list[dict]:
    if BeautifulSoup is None:
        raise RuntimeError(
            "beautifulsoup4 nao esta instalado. Rode `pip install -r etl/requirements.txt`.",
        )

    soup = BeautifulSoup(html, "html.parser")
    detail_urls: list[str] = []
    seen: set[str] = set()
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]
        absolute = urljoin(source.source_url, href)
        if not absolute.startswith("https://www.dhs-tt.com/en/dhs-"):
            continue
        if absolute in seen:
            continue
        seen.add(absolute)
        detail_urls.append(absolute)

    records: list[dict] = []
    for detail_url in detail_urls:
        detail_source = ManufacturerSource(
            brand=source.brand,
            category="blade",
            source_url=detail_url,
            parser="dhs_blade_detail",
            enabled=True,
            table_index=0,
        )
        detail_html = fetch_html(detail_url)
        records.extend(parse_dhs_blade_detail(detail_source, detail_html))
    return records


def parse_dhs_rubber_detail(source: ManufacturerSource, html: str) -> list[dict]:
    if BeautifulSoup is None:
        raise RuntimeError(
            "beautifulsoup4 nao esta instalado. Rode `pip install -r etl/requirements.txt`.",
        )

    soup = BeautifulSoup(html, "html.parser")
    title_node = soup.find("h1") or soup.find("div", class_="product-name") or soup.find("title")
    title = normalize_whitespace(title_node.get_text(" ", strip=True)) if title_node else ""
    model = title.replace("DHS Table Tennis Equipment", "").replace("Details", "").strip()
    model = re.sub(r"^DHS\s+", "", model).strip()
    text = extract_text(html)

    rubber_type = "IN"
    table = soup.find("table")
    if table:
        for row in table.find_all("tr"):
            cells = [normalize_whitespace(cell.get_text(" ", strip=True)) for cell in row.find_all(["th", "td"])]
            if len(cells) >= 3 and cells[0].lower() == "rubber type":
                rubber_type = infer_rubber_type(cells[2])

    hardness: float | None = None
    scale: str | None = None
    apostrophe_match = re.search(r"(\d+(?:\.\d+)?)\s*'", model)
    if apostrophe_match:
        hardness = float(apostrophe_match.group(1))
        scale = "chinesa"
    else:
        degree_match = re.search(r"(\d+(?:\.\d+)?)", model)
        if degree_match and any(token in model.lower() for token in ["deg", "goldarc"]):
            hardness = float(degree_match.group(1))

    if scale is None and "chinese style sponge" in text.lower():
        scale = "chinesa"

    thicknesses = []
    if "max" in text.lower():
        thicknesses.append("MAX")

    return [
        {
            "source": "fabricante",
            "source_url": source.source_url,
            "marca": source.brand,
            "modelo": model or "desconhecido",
            "tipo": rubber_type,
            "fisica": {
                "espessuras_disponiveis_mm": thicknesses,
                "dureza_esponja_graus": hardness,
                "escala_dureza": scale,
                "peso_por_espessura_g": None,
                "diametro_topsheet_mm": None,
            },
            "aprovacao_ittf_declarada": False,
            "scraped_at": TODAY,
        }
    ]


def parse_dhs_rubber_listing(source: ManufacturerSource, html: str) -> list[dict]:
    if BeautifulSoup is None:
        raise RuntimeError(
            "beautifulsoup4 nao esta instalado. Rode `pip install -r etl/requirements.txt`.",
        )

    soup = BeautifulSoup(html, "html.parser")
    detail_urls: list[str] = []
    seen: set[str] = set()
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]
        absolute = urljoin(source.source_url, href)
        if not absolute.startswith("https://www.dhs-tt.com/en/dhs-"):
            continue
        if absolute in seen:
            continue
        seen.add(absolute)
        detail_urls.append(absolute)

    records: list[dict] = []
    for detail_url in detail_urls:
        detail_source = ManufacturerSource(
            brand=source.brand,
            category="rubber",
            source_url=detail_url,
            parser="dhs_rubber_detail",
            enabled=True,
            table_index=0,
        )
        detail_html = fetch_html(detail_url)
        records.extend(parse_dhs_rubber_detail(detail_source, detail_html))
    return records


def extract_product_links_from_boxes(html: str, selector: str, base_url: str) -> list[str]:
    if BeautifulSoup is None:
        raise RuntimeError(
            "beautifulsoup4 nao esta instalado. Rode `pip install -r etl/requirements.txt`.",
        )
    soup = BeautifulSoup(html, "html.parser")
    links: list[str] = []
    seen: set[str] = set()
    for anchor in soup.select(selector):
        href = anchor.get("href")
        if not href:
            continue
        absolute = urljoin(base_url, href)
        if absolute in seen:
            continue
        seen.add(absolute)
        links.append(absolute)
    return links


def parse_donic_blade_listing(source: ManufacturerSource, html: str) -> list[dict]:
    category_urls = [
        "https://www.donic.com/hoelzer/charakteristik/offensiv/",
        "https://www.donic.com/hoelzer/charakteristik/allround/",
        "https://www.donic.com/Hoelzer/Charakteristik/Defensiv/",
    ]
    detail_urls: list[str] = []
    seen: set[str] = set()
    for category_url in category_urls:
        category_html = fetch_html(category_url)
        for link in extract_product_links_from_boxes(category_html, ".product-box a.product-image-link", category_url):
            if link in seen:
                continue
            seen.add(link)
            detail_urls.append(link)

    records: list[dict] = []
    for detail_url in detail_urls:
        detail_source = ManufacturerSource(
            brand=source.brand,
            category="blade",
            source_url=detail_url,
            parser="donic_blade_detail",
            enabled=True,
            table_index=0,
        )
        records.extend(parse_donic_blade_detail(detail_source, fetch_html(detail_url)))
    return records


def parse_donic_blade_detail(source: ManufacturerSource, html: str) -> list[dict]:
    if BeautifulSoup is None:
        raise RuntimeError(
            "beautifulsoup4 nao esta instalado. Rode `pip install -r etl/requirements.txt`.",
        )
    soup = BeautifulSoup(html, "html.parser")
    name_node = soup.select_one(".product-detail-name")
    description_node = soup.select_one(".product-detail-description")
    properties_node = soup.select_one(".product-detail-properties-table")
    config_node = soup.select_one(".product-detail-configurator")

    model = normalize_whitespace(name_node.get_text(" ", strip=True)) if name_node else "desconhecido"
    model = re.sub(r"^DONIC\s+", "", model, flags=re.I)
    description = normalize_whitespace(description_node.get_text(" ", strip=True)) if description_node else ""
    properties = normalize_whitespace(properties_node.get_text(" ", strip=True)) if properties_node else ""
    configurator = normalize_whitespace(config_node.get_text(" ", strip=True)) if config_node else ""
    combined = " ".join(part for part in [model, description, properties] if part)

    layers_match = re.search(r"Schichten:\s*([0-9+]+)", properties, flags=re.I)
    weight_match = re.search(r"(\d{2,3})\s*g", description, flags=re.I)
    thickness_match = re.search(r"(\d+(?:[.,]\d+)?)\s*mm", description, flags=re.I)
    handles = " / ".join(re.findall(r"\b(anatomisch|gerade|konkav)\b", configurator, flags=re.I))

    record = build_blade_record_from_fields(
        source,
        brand=source.brand,
        model=model,
        weight=weight_match.group(1) if weight_match else None,
        thickness=thickness_match.group(1) if thickness_match else None,
        plies=layers_match.group(1) if layers_match else None,
        composition_value=properties or description or None,
        handles=handles,
    )
    enrich_blade_composition_from_text(record, combined)
    return [record]


def parse_donic_rubber_listing(source: ManufacturerSource, html: str) -> list[dict]:
    category_urls = [
        "https://www.donic.com/belaege/noppen-innen/offensiv/",
        "https://www.donic.com/belaege/noppen-innen/allround/",
        "https://www.donic.com/belaege/noppen-innen/defensiv/",
        "https://www.donic.com/belaege/noppen-aussen/lange-noppen/",
        "https://www.donic.com/belaege/noppen-aussen/mittellange-noppen/",
        "https://www.donic.com/belaege/noppen-aussen/kurze-noppen/",
        "https://www.donic.com/belaege/anti-spin/",
    ]
    detail_urls: list[tuple[str, str]] = []
    seen: set[str] = set()
    for category_url in category_urls:
        category_html = fetch_html(category_url)
        rubber_type = infer_rubber_type_from_url(category_url)
        for link in extract_product_links_from_boxes(category_html, ".product-box a.product-image-link", category_url):
            if link in seen:
                continue
            seen.add(link)
            detail_urls.append((link, rubber_type))

    records: list[dict] = []
    for detail_url, rubber_type in detail_urls:
        detail_source = ManufacturerSource(
            brand=source.brand,
            category="rubber",
            source_url=detail_url,
            parser="donic_rubber_detail",
            enabled=True,
            table_index=0,
        )
        records.extend(parse_donic_rubber_detail(detail_source, fetch_html(detail_url), rubber_type))
    return records


def infer_rubber_type_from_url(url: str) -> str:
    lowered = url.lower()
    if "lange-noppen" in lowered:
        return "LONG"
    if "kurze-noppen" in lowered or "mittellange-noppen" in lowered:
        return "OUT"
    if "anti-spin" in lowered:
        return "ANTI"
    return "IN"


def parse_donic_rubber_detail(source: ManufacturerSource, html: str, rubber_type: str) -> list[dict]:
    if BeautifulSoup is None:
        raise RuntimeError(
            "beautifulsoup4 nao esta instalado. Rode `pip install -r etl/requirements.txt`.",
        )
    soup = BeautifulSoup(html, "html.parser")
    name_node = soup.select_one(".product-detail-name")
    description_node = soup.select_one(".product-detail-description")
    properties_node = soup.select_one(".product-detail-properties-table")
    config_node = soup.select_one(".product-detail-configurator")

    model = normalize_whitespace(name_node.get_text(" ", strip=True)) if name_node else "desconhecido"
    model = re.sub(r"^DONIC\s+", "", model, flags=re.I)
    description = normalize_whitespace(description_node.get_text(" ", strip=True)) if description_node else ""
    properties = normalize_whitespace(properties_node.get_text(" ", strip=True)) if properties_node else ""
    configurator = normalize_whitespace(config_node.get_text(" ", strip=True)) if config_node else ""

    thickness_values = parse_thicknesses(" / ".join(re.findall(r"(?:\d+,\d+\s*mm|max\.?)", description, flags=re.I)))
    if not thickness_values:
        thickness_values = parse_thicknesses(configurator)

    hardness_match = re.search(r"Schwammh[aä]rte:\s*(\d+(?:[.,]\d+)?)\s*°", description, flags=re.I)
    hardness = hardness_match.group(1) if hardness_match else None

    return [
        {
            "source": "fabricante",
            "source_url": source.source_url,
            "marca": source.brand,
            "modelo": model,
            "tipo": rubber_type,
            "fisica": {
                "espessuras_disponiveis_mm": thickness_values,
                "dureza_esponja_graus": parse_float(hardness),
                "escala_dureza": None,
                "peso_por_espessura_g": None,
                "diametro_topsheet_mm": None,
            },
            "aprovacao_ittf_declarada": "ittf" in description.lower(),
            "scraped_at": TODAY,
        }
    ]


def parse_joola_blade_listing(source: ManufacturerSource, html: str) -> list[dict]:
    detail_urls = [
        urljoin(source.source_url, link)
        for link in extract_product_links_from_boxes(html, 'a[href*="/products/"]', source.source_url)
        if "table-tennis-blade" in link or "blade" in link
    ]
    detail_urls = list(dict.fromkeys(detail_urls))

    records: list[dict] = []
    for detail_url in detail_urls:
        detail_source = ManufacturerSource(
            brand=source.brand,
            category="blade",
            source_url=detail_url,
            parser="joola_blade_detail",
            enabled=True,
            table_index=0,
        )
        records.extend(parse_joola_blade_detail(detail_source, fetch_html(detail_url)))
    return records


def parse_joola_blade_detail(source: ManufacturerSource, html: str) -> list[dict]:
    if BeautifulSoup is None:
        raise RuntimeError(
            "beautifulsoup4 nao esta instalado. Rode `pip install -r etl/requirements.txt`.",
        )
    soup = BeautifulSoup(html, "html.parser")
    title_node = soup.find("h1")
    description_node = soup.select_one(".rte")
    model = normalize_whitespace(title_node.get_text(" ", strip=True)) if title_node else "desconhecido"
    model = re.sub(r"^JOOLA\s+", "", model, flags=re.I)
    model = re.sub(r"\s+Table Tennis Blade$", "", model, flags=re.I)
    description = normalize_whitespace(description_node.get_text(" ", strip=True)) if description_node else ""

    ply_match = re.search(r"(\d+)\s*\+\s*(\d+)\s*ply", description, flags=re.I)
    composition_value = description
    record = build_blade_record_from_fields(
        source,
        brand=source.brand,
        model=model,
        plies=(f"{ply_match.group(1)}+{ply_match.group(2)}" if ply_match else None),
        composition_value=composition_value,
    )
    enrich_blade_composition_from_text(record, f"{model} {description}")
    return [record]


def parse_joola_rubber_listing(source: ManufacturerSource, html: str) -> list[dict]:
    detail_urls = [
        urljoin(source.source_url, link)
        for link in extract_product_links_from_boxes(html, 'a[href*="/products/"]', source.source_url)
        if "table-tennis-rubber" in link or "rubber" in link
    ]
    detail_urls = list(dict.fromkeys(detail_urls))

    records: list[dict] = []
    for detail_url in detail_urls:
        detail_source = ManufacturerSource(
            brand=source.brand,
            category="rubber",
            source_url=detail_url,
            parser="joola_rubber_detail",
            enabled=True,
            table_index=0,
        )
        records.extend(parse_joola_rubber_detail(detail_source, fetch_html(detail_url)))
    return records


def parse_joola_rubber_detail(source: ManufacturerSource, html: str) -> list[dict]:
    if BeautifulSoup is None:
        raise RuntimeError(
            "beautifulsoup4 nao esta instalado. Rode `pip install -r etl/requirements.txt`.",
        )
    soup = BeautifulSoup(html, "html.parser")
    title_node = soup.find("h1")
    text = extract_text(html)
    model = normalize_whitespace(title_node.get_text(" ", strip=True)) if title_node else "desconhecido"
    model = re.sub(r"^JOOLA\s+", "", model, flags=re.I)
    model = re.sub(r"\s+Table Tennis Rubber$", "", model, flags=re.I)

    thickness_match = re.search(r"Thickness:\s*([A-Z0-9.,\s]+?)\s+Quantity:", text, flags=re.I)
    hardness_match = re.search(r"Hardness\s*:\s*([A-Za-z0-9.+-]+)", text, flags=re.I)
    thicknesses = parse_thicknesses(thickness_match.group(1)) if thickness_match else []
    hardness_value = hardness_match.group(1) if hardness_match else None

    return [
        {
            "source": "fabricante",
            "source_url": source.source_url,
            "marca": source.brand,
            "modelo": model,
            "tipo": "IN",
            "fisica": {
                "espessuras_disponiveis_mm": thicknesses,
                "dureza_esponja_graus": parse_float(hardness_value),
                "escala_dureza": None,
                "peso_por_espessura_g": None,
                "diametro_topsheet_mm": None,
            },
            "aprovacao_ittf_declarada": "ittf" in text.lower(),
            "scraped_at": TODAY,
        }
    ]


def infer_rubber_type(value: str) -> str:
    """Infere o tipo de rubber a partir do texto."""

    lowered = value.lower()
    if "long" in lowered:
        return "LONG"
    if "anti" in lowered:
        return "ANTI"
    if "short" in lowered or "pips" in lowered or "out" == lowered.strip():
        return "OUT"
    return "IN"


def infer_hardness_scale(value: str) -> str | None:
    """Infere a escala de dureza declarada."""

    lowered = value.lower()
    if "chinese" in lowered or "cn" in lowered:
        return "chinesa"
    if "japan" in lowered or "jp" in lowered:
        return "japonesa"
    if value:
        return "europeia"
    return None


def process_source(source: ManufacturerSource) -> list[dict]:
    """Processa uma unica fonte configurada."""

    html = fetch_html(source.source_url)
    if source.parser == "butterfly_global_blade_detail":
        return parse_butterfly_blade_detail(source, html)
    if source.parser == "butterfly_global_blade_listing":
        return parse_butterfly_blade_listing(source, html)
    if source.parser == "butterfly_global_rubber_detail":
        return parse_butterfly_rubber_detail(source, html)
    if source.parser == "butterfly_global_rubber_listing":
        return parse_butterfly_rubber_listing(source, html)
    if source.parser == "dhs_blade_listing":
        return parse_dhs_blade_listing(source, html)
    if source.parser == "dhs_blade_detail":
        return parse_dhs_blade_detail(source, html)
    if source.parser == "dhs_rubber_listing":
        return parse_dhs_rubber_listing(source, html)
    if source.parser == "dhs_rubber_detail":
        return parse_dhs_rubber_detail(source, html)
    if source.parser == "donic_blade_listing":
        return parse_donic_blade_listing(source, html)
    if source.parser == "donic_blade_detail":
        return parse_donic_blade_detail(source, html)
    if source.parser == "donic_rubber_listing":
        return parse_donic_rubber_listing(source, html)
    if source.parser == "donic_rubber_detail":
        return parse_donic_rubber_detail(source, html, "IN")
    if source.parser == "joola_blade_listing":
        return parse_joola_blade_listing(source, html)
    if source.parser == "joola_blade_detail":
        return parse_joola_blade_detail(source, html)
    if source.parser == "joola_rubber_listing":
        return parse_joola_rubber_listing(source, html)
    if source.parser == "joola_rubber_detail":
        return parse_joola_rubber_detail(source, html)
    if source.parser == "nittaku_blade_detail":
        return parse_nittaku_blade_detail(source, html)

    rows = extract_rows_from_html(
        html,
        table_index=source.table_index,
        column_aliases=source.column_aliases,
    )

    if source.category == "blade":
        return [build_placeholder_blade_record(source, row) for row in rows]

    return [build_placeholder_rubber_record(source, row) for row in rows]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Executa scraping inicial de fabricantes com base em um arquivo de configuracao.",
    )
    parser.add_argument(
        "--config",
        default=str(CONFIG_PATH),
        help="Caminho do manufacturer_configs.json",
    )
    parser.add_argument(
        "--include-disabled",
        action="store_true",
        help="Processa tambem entradas marcadas como enabled=false",
    )
    args = parser.parse_args()

    sources = load_sources(resolve_repo_path(args.config))
    active_sources = [source for source in sources if source.enabled or args.include_disabled]

    blade_records: list[dict] = []
    rubber_records: list[dict] = []
    failures: list[dict] = []

    for source in active_sources:
        try:
            records = process_source(source)
            if source.category == "blade":
                blade_records.extend(records)
            else:
                rubber_records.extend(records)
        except Exception as exc:  # pragma: no cover - caminho operacional do scraping
            failures.append(
                {
                    "brand": source.brand,
                    "category": source.category,
                    "url": source.source_url,
                    "error": str(exc),
                }
            )

    write_json(DEFAULT_BLADE_OUTPUT, blade_records)
    write_json(DEFAULT_RUBBER_OUTPUT, rubber_records)

    print(
        "Scraping de fabricantes finalizado. "
        f"fontes={len(active_sources)}, blades={len(blade_records)}, "
        f"rubbers={len(rubber_records)}, falhas={len(failures)}",
    )

    if failures:
        print("Falhas detectadas:")
        for failure in failures:
            print(
                f'brand={failure["brand"]} '
                f'category={failure["category"]} '
                f'url={failure["url"]}',
            )
            print(f'erro={failure["error"]}')


if __name__ == "__main__":
    main()
