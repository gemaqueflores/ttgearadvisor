from schemas import AthleteProfileInput


def select_candidates(profile: AthleteProfileInput) -> dict:
    """Aplica um pre-filtro inicial sobre o dataset unificado.

    Esta funcao ainda e um placeholder para a Fase 2 e retornara
    candidatos simulados ate o ETL entregar os datasets finais.
    """

    return {
        "laminas": [],
        "borrachas_fh": [],
        "borrachas_bh": [],
        "perfil_recebido": profile.model_dump(),
    }
