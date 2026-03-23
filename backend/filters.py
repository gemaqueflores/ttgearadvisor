from __future__ import annotations

import re
import unicodedata

from dataset import load_blades, load_rubbers
from schemas import AthleteProfileInput


def _slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_value.lower()).strip("-")
    return re.sub(r"-{2,}", "-", slug)


def _find_by_setup(brand: str, model: str, dataset: list[dict]) -> dict | None:
    target_id = f"{_slugify(brand)}-{_slugify(model)}".strip("-")
    for item in dataset:
        if item.get("id") == target_id:
            return item
    return None


def select_candidates(profile: AthleteProfileInput) -> dict[str, dict | None]:
    blades = load_blades()
    rubbers = load_rubbers()

    blade = _find_by_setup(profile.material_atual.lamina_marca, profile.material_atual.lamina_modelo, blades)
    fh = _find_by_setup(profile.material_atual.borracha_fh_marca, profile.material_atual.borracha_fh_modelo, rubbers)
    bh = None
    if profile.material_atual.borracha_bh_tipo != "dorso-liso":
        bh = _find_by_setup(
            profile.material_atual.borracha_bh_marca or "",
            profile.material_atual.borracha_bh_modelo or "",
            rubbers,
        )

    limitacoes: list[str] = []
    riscos: list[str] = []

    if blade is None:
        limitacoes.append("A lamina atual nao foi encontrada no dataset consolidado.")
    if fh is None:
        limitacoes.append("A borracha de FH atual nao foi encontrada no dataset consolidado.")
    if profile.material_atual.borracha_bh_tipo == "dorso-liso":
        riscos.append("O BH foi mantido como dorso-liso por causa da empunhadura declarada.")
    elif bh is None:
        limitacoes.append("A borracha de BH atual nao foi encontrada no dataset consolidado.")

    if blade and (blade.get("fisica", {}) or {}).get("peso_g"):
        blade_weight = blade["fisica"]["peso_g"]
        if blade_weight >= 88:
            riscos.append(f"A lamina atual tem {blade_weight} g no dataset, ponto de atencao para fadiga e manobrabilidade.")
    if fh and (fh.get("ratings", {}) or {}).get("controle_revspin") is not None:
        fh_control = fh["ratings"]["controle_revspin"]
        if fh_control < 8.0:
            limitacoes.append(f"O FH atual aparece com controle {fh_control} no Revspin, abaixo de uma faixa mais segura para consistencia.")
    if bh and (bh.get("ratings", {}) or {}).get("controle_revspin") is not None:
        bh_control = bh["ratings"]["controle_revspin"]
        if bh_control < 8.0:
            riscos.append(f"O BH atual aparece com controle {bh_control} no Revspin, o que pode cobrar mais precisao em dias irregulares.")

    return {
        "lamina_atual": blade,
        "borracha_fh_atual": fh,
        "borracha_bh_atual": bh,
        "limitacoes": limitacoes,
        "riscos": riscos,
    }
