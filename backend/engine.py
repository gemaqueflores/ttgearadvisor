from __future__ import annotations

from enrich import SetupEnriched
from models import AnalysisConfidence, AnalyzeResponse
from schemas import AthleteProfileInput


def _build_profile_analysis(profile: AthleteProfileInput) -> dict[str, object]:
    points = [
        f"Objetivo atual declarado: {profile.objetivo}.",
        "O MVP avalia compatibilidade e conformidade do setup atual, sem sugerir troca de material.",
    ]
    if profile.frequencia in {"ocasional", "1-2x/semana"}:
        points.append("Com menor volume de treino, setups muito exigentes tendem a cobrar mais consistencia tecnica.")
    if profile.empunhadura == "classineta":
        points.append("Na classineta, peso e equilibrio do conjunto impactam diretamente a qualidade do BH moderno.")
    if profile.empunhadura == "penhold-classico":
        points.append("No penhold classico, o BH com dorso-liso precisa ser respeitado na leitura do setup.")

    return {
        "resumo": (
            f"Perfil {profile.estilo} de nivel {profile.nivel}, com empunhadura {profile.empunhadura} "
            f"e objetivo {profile.objetivo}."
        ),
        "compatibilidade_estilo_nivel": (
            "A leitura atual verifica se o material declarado parece coerente com a fase tecnica do atleta "
            "e com a demanda de treino informada."
        ),
        "pontos_atencao": points,
    }


def _collect_field_presence(item: dict | None, field_paths: list[tuple[str, str]]) -> tuple[list[str], list[str]]:
    if not item:
        return [], [label for label, _ in field_paths]

    used: list[str] = []
    missing: list[str] = []
    for label, path in field_paths:
        current = item
        found = True
        for part in path.split("."):
            if not isinstance(current, dict):
                found = False
                break
            current = current.get(part)
        if current is None or current == [] or current == "":
            missing.append(label)
        else:
            used.append(label)
    return used, missing


def _confidence_from_fields(used: list[str], missing: list[str], *, require_complete_ratings: bool) -> AnalysisConfidence:
    rating_fields = {"velocidade", "controle", "spin", "rigidez"}
    used_ratings = rating_fields.intersection(used)
    missing_ratings = rating_fields.intersection(missing)
    physical_or_composition = {"peso", "espessura", "camadas", "carbono", "posicao_carbono"}
    used_context = physical_or_composition.intersection(used)

    if not used_ratings:
        return AnalysisConfidence.INSUFICIENTE
    if require_complete_ratings and missing_ratings:
        return AnalysisConfidence.BAIXA
    if not require_complete_ratings and len(used_ratings) < 2:
        return AnalysisConfidence.BAIXA
    if used_context:
        return AnalysisConfidence.ALTA
    return AnalysisConfidence.MEDIA


def _evaluation_prefix(confidence: AnalysisConfidence) -> str:
    if confidence == AnalysisConfidence.ALTA:
        return "Com base em ratings e dados fisicos disponiveis"
    if confidence == AnalysisConfidence.MEDIA:
        return "Com base nos ratings disponiveis"
    if confidence == AnalysisConfidence.BAIXA:
        return "Com base nos dados parciais disponiveis"
    return "Os dados atuais sao insuficientes para uma leitura tecnica forte"


def _blade_analysis(title: str, item: dict | None) -> dict[str, object]:
    field_paths = [
        ("velocidade", "ratings.velocidade_revspin"),
        ("controle", "ratings.controle_revspin"),
        ("rigidez", "ratings.rigidez_revspin"),
        ("peso", "fisica.peso_g"),
        ("espessura", "fisica.espessura_mm"),
        ("camadas", "composicao.total_camadas"),
        ("carbono", "composicao.tem_carbono"),
        ("posicao_carbono", "composicao.posicao_carbono"),
    ]
    used, missing = _collect_field_presence(item, field_paths)
    confidence = _confidence_from_fields(used, missing, require_complete_ratings=False)
    positives: list[str] = []
    limitations: list[str] = []

    if not item:
        limitations.append(f"{title} nao foi encontrado(a) no dataset consolidado atual.")
        return {
            "confianca": AnalysisConfidence.INSUFICIENTE,
            "campos_utilizados": used,
            "campos_ausentes": missing,
            "avaliacao": f"{_evaluation_prefix(AnalysisConfidence.INSUFICIENTE)} para {title.lower()}.",
            "pontos_positivos": positives,
            "limitacoes": limitations,
        }

    ratings = item.get("ratings", {})
    fisica = item.get("fisica", {})
    if ratings.get("velocidade_revspin") is not None:
        positives.append(f"Velocidade Revspin: {ratings['velocidade_revspin']}.")
    if ratings.get("controle_revspin") is not None:
        positives.append(f"Controle Revspin: {ratings['controle_revspin']}.")
    if ratings.get("rigidez_revspin") is not None:
        positives.append(f"Rigidez Revspin: {ratings['rigidez_revspin']}.")
    if fisica.get("peso_g") is not None:
        positives.append(f"Peso declarado: {fisica['peso_g']} g.")

    if ratings.get("controle_revspin") is not None and ratings["controle_revspin"] < 8.0:
        limitations.append(f"Controle {ratings['controle_revspin']} no Revspin indica margem menor para consistencia.")
    if ratings.get("rigidez_revspin") is not None and ratings["rigidez_revspin"] > 8.5:
        limitations.append(f"Rigidez {ratings['rigidez_revspin']} sugere resposta mais seca e menos tolerante.")
    if confidence in {AnalysisConfidence.BAIXA, AnalysisConfidence.INSUFICIENTE}:
        limitations.append("A leitura desta lamina e parcial por falta de dados suficientes no dataset.")
    if not limitations:
        limitations.append("Nao ha limitacao numerica dominante nos dados atuais da lamina.")

    return {
        "confianca": confidence,
        "campos_utilizados": used,
        "campos_ausentes": missing,
        "avaliacao": f"{_evaluation_prefix(confidence)} a lamina parece apta a leitura tecnica do MVP.",
        "pontos_positivos": positives,
        "limitacoes": limitations,
    }


def _rubber_analysis(
    title: str,
    item: dict | None,
    *,
    approved: bool,
    alerta_larc: str | None,
    dorsoliso: bool = False,
) -> dict[str, object]:
    if dorsoliso:
        return {
            "confianca": AnalysisConfidence.MEDIA,
            "campos_utilizados": ["dorso_liso"],
            "campos_ausentes": ["velocidade", "spin", "controle"],
            "avaliacao": "O BH foi declarado como dorso-liso, coerente com o uso classico do penhold.",
            "aprovado_competicao": True,
            "alerta_larc": None,
            "pontos_positivos": ["A declaracao do BH esta coerente com a empunhadura informada."],
            "limitacoes": ["Nao ha borracha BH para cruzar com dados tecnicos do dataset."],
        }

    field_paths = [
        ("velocidade", "ratings.velocidade_revspin"),
        ("spin", "ratings.spin_revspin"),
        ("controle", "ratings.controle_revspin"),
        ("dureza", "ratings.dureza_revspin"),
        ("espessura", "fisica.espessuras_disponiveis_mm"),
        ("dureza_esponja", "fisica.dureza_esponja_graus"),
        ("escala_dureza", "fisica.escala_dureza"),
    ]
    used, missing = _collect_field_presence(item, field_paths)
    confidence = _confidence_from_fields(used, missing, require_complete_ratings=True)
    positives: list[str] = []
    limitations: list[str] = []

    if not item:
        limitations.append(f"{title} nao foi encontrado(a) no dataset consolidado atual.")
        return {
            "confianca": AnalysisConfidence.INSUFICIENTE,
            "campos_utilizados": used,
            "campos_ausentes": missing,
            "avaliacao": f"{_evaluation_prefix(AnalysisConfidence.INSUFICIENTE)} para {title.lower()}.",
            "aprovado_competicao": approved,
            "alerta_larc": alerta_larc,
            "pontos_positivos": positives,
            "limitacoes": limitations,
        }

    ratings = item.get("ratings", {})
    if ratings.get("velocidade_revspin") is not None:
        positives.append(f"Velocidade Revspin: {ratings['velocidade_revspin']}.")
    if ratings.get("controle_revspin") is not None:
        positives.append(f"Controle Revspin: {ratings['controle_revspin']}.")
    if ratings.get("spin_revspin") is not None:
        positives.append(f"Spin Revspin: {ratings['spin_revspin']}.")

    if ratings.get("controle_revspin") is not None and ratings["controle_revspin"] < 8.0:
        limitations.append(f"Controle {ratings['controle_revspin']} no Revspin indica margem menor para consistencia.")
    if ratings.get("spin_revspin") is not None and ratings["spin_revspin"] < 8.0:
        limitations.append(f"Spin {ratings['spin_revspin']} no Revspin sugere teto menor para geracao de rotacao.")
    if confidence in {AnalysisConfidence.BAIXA, AnalysisConfidence.INSUFICIENTE}:
        limitations.append("A leitura desta borracha e parcial por falta de dados suficientes no dataset.")
    if not limitations:
        limitations.append("Nao ha limitacao numerica dominante nos dados atuais da borracha.")

    approval_suffix = (
        " Ha conformidade LARC para competicoes."
        if approved
        else " Nao ha conformidade LARC para competicoes."
    )
    return {
        "confianca": confidence,
        "campos_utilizados": used,
        "campos_ausentes": missing,
        "avaliacao": f"{_evaluation_prefix(confidence)} a {title.lower()} parece apta a leitura tecnica do MVP.{approval_suffix}",
        "aprovado_competicao": approved,
        "alerta_larc": alerta_larc,
        "pontos_positivos": positives,
        "limitacoes": limitations,
    }


def _build_setup_analysis(profile: AthleteProfileInput, enriched: SetupEnriched) -> dict[str, object]:
    blade = enriched.lamina.blade
    fh = enriched.borracha_fh.rubber
    bh = enriched.borracha_bh.rubber if enriched.borracha_bh else None
    blade_weight = ((blade or {}).get("fisica", {}) or {}).get("peso_g")

    risks: list[str] = []
    if enriched.borracha_fh.alerta_larc:
        risks.append(enriched.borracha_fh.alerta_larc)
    if enriched.borracha_bh and enriched.borracha_bh.alerta_larc:
        risks.append(enriched.borracha_bh.alerta_larc)
    if profile.empunhadura == "classineta" and blade_weight is not None and blade_weight >= 88:
        risks.append("Na classineta, peso alto da lamina pode prejudicar velocidade de recuperacao no BH.")
    if not risks:
        risks.append("Nao ha risco numerico dominante no dataset atual, mas a leitura segue dependente da cobertura das fontes.")

    return {
        "lamina": _blade_analysis("Lamina", blade),
        "borracha_fh": _rubber_analysis(
            "Borracha FH",
            fh,
            approved=enriched.borracha_fh.aprovado_larc,
            alerta_larc=enriched.borracha_fh.alerta_larc,
        ),
        "borracha_bh": _rubber_analysis(
            "Borracha BH",
            bh,
            approved=(enriched.borracha_bh.aprovado_larc if enriched.borracha_bh else True),
            alerta_larc=(enriched.borracha_bh.alerta_larc if enriched.borracha_bh else None),
            dorsoliso=profile.material_atual.borracha_bh_tipo == "dorso-liso",
        ),
        "sinergia_combinacao": (
            "A sinergia atual depende principalmente do equilibrio entre controle das borrachas e manobrabilidade da lamina."
        ),
        "riscos": risks,
    }


def build_local_response(profile: AthleteProfileInput, enriched: SetupEnriched) -> AnalyzeResponse:
    return AnalyzeResponse.model_validate(
        {
            "analise_perfil": _build_profile_analysis(profile),
            "analise_setup_atual": _build_setup_analysis(profile, enriched),
        }
    )
