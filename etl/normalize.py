"""Normalizacao de nomes com aliases versionados e diagnostico de matching."""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

from common import (
    build_normalized_id,
    load_json,
    normalize_brand_name,
    normalize_model_name,
    resolve_repo_path,
)

try:
    from rapidfuzz import fuzz
except ImportError:  # pragma: no cover - fallback quando a dependencia ainda nao foi instalada
    fuzz = None


AliasMap = dict[str, dict[str, str]]


def _alias_map_from_legacy_format(raw_aliases: dict) -> AliasMap:
    alias_map: AliasMap = {}
    for brand, brand_aliases in raw_aliases.items():
        normalized_brand = normalize_brand_name(brand)
        alias_map.setdefault(normalized_brand, {})
        for alias, canonical in brand_aliases.items():
            alias_map[normalized_brand][normalize_model_name(alias)] = normalize_model_name(canonical)
    return alias_map


def _alias_map_from_canonical_id_format(raw_aliases: dict) -> AliasMap:
    alias_map: AliasMap = {}
    for canonical_id, variants in raw_aliases.items():
        normalized_canonical_id = build_normalized_id(*split_canonical_id(canonical_id))
        canonical_brand, canonical_model = split_canonical_id(normalized_canonical_id)
        alias_map.setdefault(canonical_brand, {})
        alias_map[canonical_brand][canonical_model] = canonical_model
        for variant in variants:
            variant_id = build_normalized_id(canonical_brand, variant)
            _, variant_model = split_canonical_id(variant_id)
            alias_map[canonical_brand][variant_model] = canonical_model
    return alias_map


def split_canonical_id(canonical_id: str) -> tuple[str, str]:
    normalized_id = normalize_model_name(canonical_id)
    parts = normalized_id.split("-", 1)
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], parts[1]


def load_aliases(path: Path | None = None) -> AliasMap:
    """Carrega o dicionario central de aliases.

    Formatos aceitos:
    - legado: { "dhs": { "hurricane iii": "hurricane-3" } }
    - canonico: { "dhs-hurricane-3": ["Hurricane III", "Hurricane 3"] }
    """

    alias_path = path or Path(__file__).with_name("aliases.json")
    raw_aliases = load_json(alias_path, default={})
    if not raw_aliases:
        return {}

    sample_value = next(iter(raw_aliases.values()))
    if isinstance(sample_value, dict):
        return _alias_map_from_legacy_format(raw_aliases)
    if isinstance(sample_value, list):
        return _alias_map_from_canonical_id_format(raw_aliases)

    raise ValueError("Formato de aliases.json nao suportado.")


def canonicalize_model(brand: str, model: str, aliases: AliasMap) -> str:
    """Resolve aliases explicitos para um modelo canonico."""

    normalized_brand = normalize_brand_name(brand)
    normalized_model = normalize_model_name(model)
    return aliases.get(normalized_brand, {}).get(normalized_model, normalized_model)


def score_similarity(left: str, right: str) -> int | None:
    """Retorna score de similaridade se RapidFuzz estiver disponivel."""

    if fuzz is None:
        return None
    return int(fuzz.ratio(left, right))


def build_canonical_id(brand: str, model: str, aliases: AliasMap) -> str:
    """Gera ID canonico usando aliases quando existirem."""

    canonical_model = canonicalize_model(brand, model, aliases)
    return build_normalized_id(brand, canonical_model)


def normalize_revspin_record(record: dict) -> dict:
    return {
        "marca": record.get("marca"),
        "modelo": record.get("modelo"),
        "categoria": str(record.get("categoria", "")).strip().lower(),
    }


def diagnose_matching(aliases: AliasMap, brands: list[str]) -> None:
    """Mostra diagnostico de matching fabricante x Revspin por marca."""

    target_brands = {normalize_brand_name(brand) for brand in brands}
    manufacturer_blades = load_json(resolve_repo_path("data/raw/fabricante_blade.json"), default=[])
    manufacturer_rubbers = load_json(resolve_repo_path("data/raw/fabricante_rubber.json"), default=[])
    revspin_raw = load_json(resolve_repo_path("data/raw/revspin_merge_blades.json"), default=[])
    revspin_raw += load_json(resolve_repo_path("data/raw/revspin_merge_rubbers.json"), default=[])
    revspin_records = [normalize_revspin_record(record) for record in revspin_raw]

    for category, manufacturer_records in (("blade", manufacturer_blades), ("rubber", manufacturer_rubbers)):
        print(f"\n[{category.upper()}]")
        rev_by_brand: dict[str, dict[str, str]] = defaultdict(dict)
        for record in revspin_records:
            if record["categoria"] and record["categoria"] != category:
                continue
            brand = normalize_brand_name(str(record.get("marca", "")))
            if brand not in target_brands:
                continue
            model = str(record.get("modelo", ""))
            rev_by_brand[brand][build_canonical_id(brand, model, aliases)] = model

        for brand in sorted(target_brands):
            manufacturer_by_brand = [
                record for record in manufacturer_records if normalize_brand_name(str(record.get("marca", ""))) == brand
            ]
            if not manufacturer_by_brand:
                continue

            rev_ids = rev_by_brand.get(brand, {})
            matched = 0
            unmatched: list[tuple[str, str | None, str]] = []

            for record in manufacturer_by_brand:
                model = str(record.get("modelo", ""))
                canonical_id = build_canonical_id(brand, model, aliases)
                if canonical_id in rev_ids:
                    matched += 1
                    continue

                closest = suggest_closest_match(canonical_id, rev_ids)
                unmatched.append((model, closest, canonical_id))

            print(
                f"marca={brand} fabricante={len(manufacturer_by_brand)} "
                f"casou={matched} sem_match={len(unmatched)}"
            )
            for manufacturer_model, suggestion, canonical_id in unmatched[:15]:
                if suggestion:
                    print(
                        f"  - fabricante='{manufacturer_model}' "
                        f"-> sugestao_revspin='{suggestion}' id='{canonical_id}'"
                    )
                else:
                    print(
                        f"  - fabricante='{manufacturer_model}' "
                        f"-> sugestao_revspin=<nenhuma> id='{canonical_id}'"
                    )


def suggest_closest_match(canonical_id: str, rev_ids: dict[str, str]) -> str | None:
    if not rev_ids:
        return None
    _, model = split_canonical_id(canonical_id)
    best_score = -1
    best_label: str | None = None
    for rev_id, rev_model in rev_ids.items():
        _, rev_model_slug = split_canonical_id(rev_id)
        score = score_similarity(model, rev_model_slug)
        if score is None:
            score = 100 if model == rev_model_slug else 0
        if score > best_score:
            best_score = score
            best_label = rev_model
    if best_score < 60:
        return None
    return best_label


def normalize_larc_match(value: str) -> str:
    normalized = normalize_model_name(value).replace("-", "")
    aliases = {
        "doublehappinessdhs": "dhs",
        "doublehappiness": "dhs",
        "tamasu": "butterfly",
        "tenergy05": "tenergy05",
        "tenergy64": "tenergy64",
        "tenergy80": "tenergy80",
        "tenergy09c": "tenergy09c",
        "dignics05": "dignics05",
        "dignics09c": "dignics09c",
        "vegaeurope": "vegaeurope",
        "vegapro": "vegapro",
        "vegaasia": "vegaasia",
        "rakza7": "rakza7",
        "rakza7soft": "rakza7soft",
        "markv": "markv",
        "evolutionmxp": "evolutionmxp",
        "hurricane3neo": "hurricane3",
        "neohurricane3": "hurricane3",
        "hurricaneiii": "hurricane3",
        "hurricaneiiineo": "hurricane3",
        "hurricane8": "hurricane8",
    }
    return aliases.get(normalized, normalized)


def diagnose_larc_matching(brand: str, models: list[str]) -> None:
    larc = load_json(resolve_repo_path("data/raw/larc_whitelist.json"), default=[])
    normalized_brand = normalize_larc_match(brand)
    print(f"marca_input={brand} marca_normalizada={normalized_brand}")

    brand_records = [record for record in larc if normalize_larc_match(str(record.get("marca", ""))) == normalized_brand]
    print(f"registros_larc_mesma_marca={len(brand_records)}")

    for model in models:
        normalized_model = normalize_larc_match(model)
        exact_brand_rows = [
            record
            for record in brand_records
            if normalize_larc_match(str(record.get("modelo", ""))) == normalized_model and record.get("aprovado") is True
        ]
        fuzzy_rows = [
            record
            for record in brand_records
            if normalized_model in normalize_larc_match(str(record.get("modelo", "")))
            or normalize_larc_match(str(record.get("modelo", ""))) in normalized_model
        ]

        print(f"\nmodelo_input={model}")
        print(f"modelo_normalizado={normalized_model}")
        if exact_brand_rows:
            print("match=OK")
            for row in exact_brand_rows[:5]:
                print(
                    f"  larc='{row.get('marca')} | {row.get('modelo')} | {row.get('codigo_ittf')} | {row.get('tipo')}'"
                )
        else:
            print("match=FALHOU")
            print("  exemplos_larc_mesma_marca:")
            for row in fuzzy_rows[:5] or brand_records[:5]:
                print(
                    f"  larc='{row.get('marca')} | {row.get('modelo')} | {row.get('codigo_ittf')} | {row.get('tipo')}' "
                    f"norm='{normalize_larc_match(str(row.get('modelo', '')))}'"
                )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Normaliza um par marca/modelo usando aliases versionados.",
    )
    parser.add_argument("--brand", help="Marca original")
    parser.add_argument("--model", help="Modelo original")
    parser.add_argument(
        "--aliases",
        default=str(Path(__file__).with_name("aliases.json")),
        help="Caminho alternativo para aliases.json",
    )
    parser.add_argument(
        "--diagnose",
        action="store_true",
        help="Gera diagnostico de matching entre fabricante e Revspin",
    )
    parser.add_argument(
        "--brands",
        help='Lista de marcas separadas por virgula para diagnostico, ex: "Butterfly,DHS"',
    )
    parser.add_argument("--diagnose-larc", action="store_true", help="Diagnostica matching contra larc_whitelist.json")
    parser.add_argument("--models", help='Lista de modelos separada por virgula, ex: "Tenergy 05,Rozena"')
    args = parser.parse_args()

    aliases = load_aliases(Path(args.aliases))

    if args.diagnose_larc:
        if not args.brand or not args.models:
            raise SystemExit("--brand e --models sao obrigatorios com --diagnose-larc")
        models = [model.strip() for model in args.models.split(",") if model.strip()]
        diagnose_larc_matching(args.brand, models)
        return

    if args.diagnose:
        if not args.brands:
            raise SystemExit("--brands e obrigatorio com --diagnose")
        brands = [brand.strip() for brand in args.brands.split(",") if brand.strip()]
        diagnose_matching(aliases, brands)
        return

    if not args.brand or not args.model:
        raise SystemExit("--brand e --model sao obrigatorios quando --diagnose nao for usado")

    canonical_model = canonicalize_model(args.brand, args.model, aliases)
    canonical_id = build_canonical_id(args.brand, args.model, aliases)

    print(f"marca_normalizada={normalize_brand_name(args.brand)}")
    print(f"modelo_normalizado={normalize_model_name(args.model)}")
    print(f"modelo_canonico={canonical_model}")
    print(f"id={canonical_id}")


if __name__ == "__main__":
    main()
