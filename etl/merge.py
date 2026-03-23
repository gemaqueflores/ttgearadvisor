"""Merge inicial das fontes normalizadas para os datasets unificados."""

from __future__ import annotations

import argparse
from pathlib import Path

from common import load_json, resolve_repo_path, write_json
from normalize import build_canonical_id, load_aliases


DEFAULT_BLADE_OUTPUT = resolve_repo_path("data/unified/unified_blade.json")
DEFAULT_RUBBER_OUTPUT = resolve_repo_path("data/unified/unified_rubber.json")
DEFAULT_REVSPIN_BLADES = resolve_repo_path("data/raw/revspin_merge_blades.json")
DEFAULT_REVSPIN_RUBBERS = resolve_repo_path("data/raw/revspin_merge_rubbers.json")


def build_empty_output() -> list[dict]:
    """Retorna lista vazia padrao para datasets ainda nao consolidados."""

    return []


def normalize_revspin_record(record: dict) -> dict:
    """Adapta o schema bruto do RevSpin para o formato consumido pelo merge.

    Os arquivos adicionados em `data/raw/` usam nomes como `revspin_merge_blades.json`
    e `revspin_merge_rubbers.json`, com campos como `preco_medio` e `categoria`.
    """

    return {
        "source": "revspin",
        "source_id": record.get("source_id"),
        "marca": record.get("marca"),
        "modelo": record.get("modelo"),
        "url": record.get("url"),
        "velocidade": record.get("velocidade"),
        "spin": record.get("spin"),
        "controle": record.get("controle"),
        "rigidez": record.get("rigidez"),
        "dureza_esponja": record.get("dureza_esponja"),
        "decepcao": record.get("decepcao"),
        "avaliacao_geral": record.get("avaliacao_geral"),
        "preco_medio_usd": record.get("preco_medio_usd", record.get("preco_medio")),
        "scraped_at": record.get("scraped_at"),
        "categoria": record.get("categoria"),
    }


def normalize_revspin_records(records: list[dict], *, category: str) -> list[dict]:
    """Filtra e normaliza o lote real do RevSpin por categoria."""

    normalized: list[dict] = []
    for record in records:
        record_category = str(record.get("categoria", "")).strip().lower()
        if record_category and record_category != category:
            continue
        normalized.append(normalize_revspin_record(record))
    return normalized


def index_by_id(
    records: list[dict],
    *,
    aliases: dict[str, dict[str, str]],
) -> dict[str, dict]:
    """Indexa registros por ID canônico."""

    indexed: dict[str, dict] = {}
    for record in records:
        brand = record.get("marca") or record.get("brand")
        model = record.get("modelo") or record.get("model")
        if not brand or not model:
            continue

        record_id = build_canonical_id(str(brand), str(model), aliases)
        indexed[record_id] = record

    return indexed


def index_larc(
    records: list[dict],
    *,
    aliases: dict[str, dict[str, str]],
    category: str,
) -> dict[str, dict]:
    """Indexa itens aprovados da LARC.

    A LARC persistida cobre apenas borrachas. O campo `tipo` no JSON indica
    o tipo da borracha (IN/OUT/LONG/ANTI), nao a categoria do equipamento.
    """

    indexed: dict[str, dict] = {}
    if category != "rubber":
        return indexed

    for record in records:
        if not record.get("aprovado", False):
            continue

        record_id = build_canonical_id(record["marca"], record["modelo"], aliases)
        indexed[record_id] = record

    return indexed


def build_unified_blade(
    item_id: str,
    revspin_record: dict | None,
    manufacturer_record: dict | None,
) -> dict:
    """Monta unified_blade com conteudo vindo de Revspin e fabricante.

    Laminas nao passam por aprovacao LARC.
    """

    brand = (
        (manufacturer_record or {}).get("marca")
        or (revspin_record or {}).get("marca")
    )
    model = (
        (manufacturer_record or {}).get("modelo")
        or (revspin_record or {}).get("modelo")
    )
    physical = (manufacturer_record or {}).get("fisica", {})
    composition = (manufacturer_record or {}).get("composicao", {})

    sources = []
    if revspin_record:
        sources.append("revspin")
    if manufacturer_record:
        sources.append("fabricante")

    price_usd = (revspin_record or {}).get("preco_medio_usd")

    return {
        "id": item_id,
        "meta": {
            "marca": brand,
            "modelo": model,
            "categoria": "blade",
            "codigo_ittf": None,
            "fontes_disponiveis": sources,
            "ultima_atualizacao": None,
        },
        "fisica": {
            "peso_g": physical.get("peso_g"),
            "espessura_mm": physical.get("espessura_mm"),
            "largura_mm": physical.get("largura_mm"),
            "altura_mm": physical.get("altura_mm"),
            "cabos_disponiveis": physical.get("cabos_disponiveis", []),
        },
        "composicao": {
            "total_camadas": composition.get("total_camadas"),
            "estrutura": composition.get("estrutura", []),
            "tem_carbono": composition.get("tem_carbono"),
            "tipo_carbono": composition.get("tipo_carbono"),
            "posicao_carbono": composition.get("posicao_carbono"),
            "camadas_carbono": composition.get("camadas_carbono"),
            "fibra_especial": composition.get("fibra_especial"),
        },
        "ratings": {
            "velocidade_revspin": (revspin_record or {}).get("velocidade"),
            "controle_revspin": (revspin_record or {}).get("controle"),
            "rigidez_revspin": (revspin_record or {}).get("rigidez"),
            "avaliacao_geral_revspin": (revspin_record or {}).get("avaliacao_geral"),
            "velocidade_megaspin": None,
            "controle_megaspin": None,
        },
        "lab": {
            "Ep": None,
            "Ec": None,
            "Vp": None,
            "Vl": None,
            "frequencia_hz": None,
        },
        "preco": {
            "medio_usd": price_usd,
        },
        "urls": {
            "revspin": (revspin_record or {}).get("url"),
            "fabricante": (manufacturer_record or {}).get("source_url"),
            "ttgearlab": None,
            "megaspin": None,
        },
    }


def build_unified_rubber(
    item_id: str,
    larc_record: dict,
    revspin_record: dict | None,
    manufacturer_record: dict | None,
) -> dict:
    """Monta unified_rubber apenas com conteudo vindo de LARC, Revspin e fabricante."""

    brand = (
        (manufacturer_record or {}).get("marca")
        or (revspin_record or {}).get("marca")
        or larc_record.get("marca")
    )
    model = (
        (manufacturer_record or {}).get("modelo")
        or (revspin_record or {}).get("modelo")
        or larc_record.get("modelo")
    )
    physical = (manufacturer_record or {}).get("fisica", {})

    sources = []
    if larc_record and larc_record.get("aprovado") is True:
        sources.append("ittf_larc")
    if revspin_record:
        sources.append("revspin")
    if manufacturer_record:
        sources.append("fabricante")

    price_usd = (revspin_record or {}).get("preco_medio_usd")
    rubber_type = (manufacturer_record or {}).get("tipo") or (larc_record or {}).get("tipo") or "IN"
    return {
        "id": item_id,
        "meta": {
            "marca": brand,
            "modelo": model,
            "categoria": "rubber",
            "tipo": rubber_type,
            "aprovado_larc": bool(larc_record and larc_record.get("aprovado") is True),
            "codigo_ittf": (larc_record or {}).get("codigo_ittf"),
            "fontes_disponiveis": sources,
            "ultima_atualizacao": None,
        },
        "fisica": {
            "espessuras_disponiveis_mm": physical.get("espessuras_disponiveis_mm", []),
            "dureza_esponja_graus": physical.get("dureza_esponja_graus"),
            "escala_dureza": physical.get("escala_dureza"),
            "peso_max_g": None,
            "diametro_topsheet_mm": physical.get("diametro_topsheet_mm"),
        },
        "ratings": {
            "velocidade_revspin": (revspin_record or {}).get("velocidade"),
            "spin_revspin": (revspin_record or {}).get("spin"),
            "controle_revspin": (revspin_record or {}).get("controle"),
            "dureza_revspin": (revspin_record or {}).get("dureza_esponja"),
            "decepcao_revspin": (revspin_record or {}).get("decepcao"),
            "avaliacao_geral_revspin": (revspin_record or {}).get("avaliacao_geral"),
        },
        "lab": {
            "Ep": None,
            "Ec": None,
        },
        "preco": {
            "medio_usd": price_usd,
        },
        "urls": {
            "revspin": (revspin_record or {}).get("url"),
            "fabricante": (manufacturer_record or {}).get("source_url"),
            "ttgearlab": None,
        },
    }


def build_manifest(
    revspin_blades: list[dict],
    revspin_rubbers: list[dict],
    larc: list[dict],
    manufacturer_blades: list[dict],
    manufacturer_rubbers: list[dict],
) -> dict:
    """Resume o estado das fontes efetivamente usadas no merge ativo."""

    return {
        "sources": {
            "revspin_blades": len(revspin_blades),
            "revspin_rubbers": len(revspin_rubbers),
            "larc": len(larc),
            "manufacturer_blades": len(manufacturer_blades),
            "manufacturer_rubbers": len(manufacturer_rubbers),
        },
        "status": "partial",
        "message": (
            "Merge incremental preparado apenas com conteudo vindo de LARC, Revspin "
            "e fabricantes."
        ),
    }


def load_optional_source(path: Path) -> list[dict]:
    """Carrega uma fonte opcional, retornando lista vazia se inexistente."""

    return load_json(path, default=[])


def resolve_existing_source(primary: str, fallback: Path | None = None) -> Path:
    """Resolve caminho principal e usa fallback quando o principal nao existir."""

    primary_path = resolve_repo_path(primary)
    if primary_path.exists():
        return primary_path
    if fallback is not None and fallback.exists():
        return fallback
    return primary_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Gera os datasets unificados iniciais a partir das fontes disponiveis.",
    )
    parser.add_argument(
        "--revspin-blades",
        default="data/raw/revspin_blade.json",
        help="Caminho para revspin_blade.json ou para o arquivo bruto equivalente do RevSpin",
    )
    parser.add_argument(
        "--revspin-rubbers",
        default="data/raw/revspin_rubber.json",
        help="Caminho para revspin_rubber.json ou para o arquivo bruto equivalente do RevSpin",
    )
    parser.add_argument(
        "--larc",
        default="data/raw/larc_whitelist.json",
        help="Caminho para larc_whitelist.json",
    )
    parser.add_argument(
        "--manufacturer-blades",
        default="data/raw/fabricante_blade.json",
        help="Caminho para fabricante_blade.json",
    )
    parser.add_argument(
        "--manufacturer-rubbers",
        default="data/raw/fabricante_rubber.json",
        help="Caminho para fabricante_rubber.json",
    )
    args = parser.parse_args()

    revspin_blade_path = resolve_existing_source(args.revspin_blades, DEFAULT_REVSPIN_BLADES)
    revspin_rubber_path = resolve_existing_source(args.revspin_rubbers, DEFAULT_REVSPIN_RUBBERS)

    revspin_blades = normalize_revspin_records(
        load_optional_source(revspin_blade_path),
        category="blade",
    )
    revspin_rubbers = normalize_revspin_records(
        load_optional_source(revspin_rubber_path),
        category="rubber",
    )
    larc = load_optional_source(resolve_repo_path(args.larc))
    manufacturer_blades = load_optional_source(resolve_repo_path(args.manufacturer_blades))
    manufacturer_rubbers = load_optional_source(resolve_repo_path(args.manufacturer_rubbers))
    aliases = load_aliases()

    larc_rubbers = index_larc(larc, aliases=aliases, category="rubber")
    revspin_blade_index = index_by_id(revspin_blades, aliases=aliases)
    revspin_rubber_index = index_by_id(revspin_rubbers, aliases=aliases)
    manufacturer_blade_index = index_by_id(manufacturer_blades, aliases=aliases)
    manufacturer_rubber_index = index_by_id(manufacturer_rubbers, aliases=aliases)

    blade_ids = sorted(set(revspin_blade_index) | set(manufacturer_blade_index))
    unified_blades = [
        build_unified_blade(
            item_id,
            revspin_blade_index.get(item_id),
            manufacturer_blade_index.get(item_id),
        )
        for item_id in blade_ids
        if item_id in revspin_blade_index or item_id in manufacturer_blade_index
    ]
    rubber_ids = sorted(set(larc_rubbers) | set(revspin_rubber_index) | set(manufacturer_rubber_index))
    unified_rubbers = [
        build_unified_rubber(
            item_id,
            larc_rubbers.get(item_id),
            revspin_rubber_index.get(item_id),
            manufacturer_rubber_index.get(item_id),
        )
        for item_id in rubber_ids
        if item_id in revspin_rubber_index or item_id in manufacturer_rubber_index
    ]

    write_json(DEFAULT_BLADE_OUTPUT, unified_blades if unified_blades else build_empty_output())
    write_json(DEFAULT_RUBBER_OUTPUT, unified_rubbers if unified_rubbers else build_empty_output())
    write_json(
        resolve_repo_path("data/unified/manifest.json"),
        build_manifest(
            revspin_blades,
            revspin_rubbers,
            larc,
            manufacturer_blades,
            manufacturer_rubbers,
        ),
    )

    print(
        "Merge incremental concluido. "
        f"Entradas detectadas: blades_revspin={len(revspin_blades)}, "
        f"rubbers_revspin={len(revspin_rubbers)}, larc={len(larc)}, "
        f"manufacturer_blades={len(manufacturer_blades)}, "
        f"manufacturer_rubbers={len(manufacturer_rubbers)}, "
        f"unified_blades={len(unified_blades)}, unified_rubbers={len(unified_rubbers)}.",
    )


if __name__ == "__main__":
    main()
