from __future__ import annotations

import re
import unicodedata

from pydantic import BaseModel

from dataset import load_blades, load_larc, load_rubbers
from schemas import AthleteProfileInput


LARC_ALERT_PT = (
    "Este equipamento nao consta na lista LARC ITTF vigente e nao e permitido em competicoes federadas."
)


def _normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    lowered = ascii_value.lower()
    lowered = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    return re.sub(r"-{2,}", "-", lowered)


def _normalize_for_match(value: str) -> str:
    slug = _normalize(value)
    replacements = {
        "iii": "3",
        "ii": "2",
        "iv": "4",
    }
    for source, target in replacements.items():
        slug = slug.replace(source, target)

    brand_aliases = {
        "doublehappiness-dhs": "dhs",
        "double-happiness-dhs": "dhs",
        "double-happiness": "dhs",
        "tamasu": "butterfly",
    }
    aliases = {
        "hurricane-3-neo": "hurricane-3",
        "neo-hurricane-3": "hurricane-3",
        "hurricane-3-h3": "hurricane-3",
        "hurricane-iii": "hurricane-3",
        "hurricane-iii-neo": "hurricane-3",
        "hurricaneiii": "hurricane3",
        "hurricaneii": "hurricane2",
        "tenergy-05": "tenergy05",
        "tenergy-64": "tenergy64",
        "tenergy-80": "tenergy80",
        "tenergy-09c": "tenergy09c",
        "tenergy-05fx": "tenergy05fx",
        "tenergy-25fx": "tenergy25fx",
        "tenergy-64fx": "tenergy64fx",
        "tenergy-80fx": "tenergy80fx",
        "tenergy-05hard": "tenergy05hard",
        "dignics-05": "dignics05",
        "dignics-09c": "dignics09c",
        "dignics-64": "dignics64",
        "dignics-80": "dignics80",
        "vega-europe": "vegaeurope",
        "vega-pro": "vegapro",
        "vega-asia": "vegaasia",
        "rakza-7": "rakza7",
        "rakza-7-soft": "rakza7soft",
        "mark-v": "markv",
        "evolution-mx-p": "evolutionmx-p",
        "hurricane-8": "hurricane8",
    }
    slug = brand_aliases.get(slug, aliases.get(slug, slug))
    return slug.replace("-", "")


def _lookup_dataset_item(brand: str, model: str, dataset: list[dict]) -> dict | None:
    target_brand = _normalize_for_match(brand)
    target_model = _normalize_for_match(model)
    target_id = f"{target_brand}-{target_model}".strip("-")

    for item in dataset:
        if item.get("id") == target_id:
            return item

        meta = item.get("meta", {})
        meta_brand = _normalize_for_match(str(meta.get("marca", "")))
        meta_model = _normalize_for_match(str(meta.get("modelo", "")))
        if meta_brand == target_brand and meta_model == target_model:
            return item

    return None


def check_larc(marca: str, modelo: str, larc: list[dict]) -> tuple[bool, str | None]:
    target_brand = _normalize_for_match(marca)
    target_model = _normalize_for_match(modelo)

    aprovado = any(
        _normalize_for_match(str(record.get("marca", ""))) == target_brand
        and _normalize_for_match(str(record.get("modelo", ""))) == target_model
        and record.get("aprovado") is True
        for record in larc
    )

    return aprovado, None if aprovado else LARC_ALERT_PT


class BladeEnriched(BaseModel):
    blade: dict | None = None
    categoria_velocidade: str | None = None
    tem_fibra_especial: bool | None = None
    dwell_time_estimado: str | None = None
    disponivel_classineta: bool | None = None
    faixa_preco: str | None = None


class RubberEnriched(BaseModel):
    rubber: dict | None = None
    aprovado_larc: bool = False
    alerta_larc: str | None = None
    equivalencia_dureza_europeia: float | None = None
    indicado_classineta: bool | None = None
    exige_tecnica: bool | None = None
    faixa_preco: str | None = None


class SetupEnriched(BaseModel):
    lamina: BladeEnriched
    borracha_fh: RubberEnriched
    borracha_bh: RubberEnriched | None = None


def _faixa_preco(price: float | None) -> str | None:
    if price is None:
        return None
    if price < 15:
        return "economico"
    if price <= 40:
        return "medio"
    if price <= 80:
        return "premium"
    return "profissional"


def _equivalencia_dureza(rubber: dict | None) -> float | None:
    if not rubber:
        return None
    fisica = rubber.get("fisica", {})
    dureza = fisica.get("dureza_esponja_graus")
    escala = fisica.get("escala_dureza")
    if dureza is None or escala != "chinesa":
        return None
    return round(float(dureza) + 8.0, 1)


def enrich_setup(profile: AthleteProfileInput) -> SetupEnriched:
    blades = load_blades()
    rubbers = load_rubbers()
    larc = load_larc()
    setup = profile.material_atual

    blade = _lookup_dataset_item(setup.lamina_marca, setup.lamina_modelo, blades)
    fh = _lookup_dataset_item(setup.borracha_fh_marca, setup.borracha_fh_modelo, rubbers)

    fh_aprovado, fh_alerta = check_larc(setup.borracha_fh_marca, setup.borracha_fh_modelo, larc)

    bh_enriched: RubberEnriched | None
    if setup.borracha_bh_tipo == "dorso-liso":
        bh_enriched = RubberEnriched(
            rubber=None,
            aprovado_larc=True,
            alerta_larc=None,
        )
    else:
        bh = _lookup_dataset_item(setup.borracha_bh_marca or "", setup.borracha_bh_modelo or "", rubbers)
        bh_aprovado, bh_alerta = check_larc(setup.borracha_bh_marca or "", setup.borracha_bh_modelo or "", larc)
        bh_enriched = RubberEnriched(
            rubber=bh,
            aprovado_larc=bh_aprovado,
            alerta_larc=bh_alerta,
            equivalencia_dureza_europeia=_equivalencia_dureza(bh),
            faixa_preco=_faixa_preco((bh or {}).get("preco", {}).get("medio_usd")),
        )

    return SetupEnriched(
        lamina=BladeEnriched(
            blade=blade,
            tem_fibra_especial=((blade or {}).get("composicao", {}) or {}).get("fibra_especial") is not None,
            disponivel_classineta=None,
            faixa_preco=_faixa_preco((blade or {}).get("preco", {}).get("medio_usd")),
        ),
        borracha_fh=RubberEnriched(
            rubber=fh,
            aprovado_larc=fh_aprovado,
            alerta_larc=fh_alerta,
            equivalencia_dureza_europeia=_equivalencia_dureza(fh),
            faixa_preco=_faixa_preco((fh or {}).get("preco", {}).get("medio_usd")),
        ),
        borracha_bh=bh_enriched,
    )
