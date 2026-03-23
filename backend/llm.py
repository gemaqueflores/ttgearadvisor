from models import AnalyzeResponse

from engine import build_local_response


def build_sonnet_prompt(athlete_profile: dict, enriched_setup: dict, user_language: str = "pt-BR") -> str:
    """Prompt base para a futura integracao com Sonnet.

    O nivel de confianca deve calibrar a assertividade da linguagem:
    - alta: afirmacoes diretas
    - media: afirmacoes diretas, mas sem extrapolar dados fisicos ausentes
    - baixa: linguagem cautelosa, com base nos dados disponiveis
    - insuficiente: deixar claro que a leitura ficou parcial
    """

    return f"""Voce e um especialista tecnico em equipamentos de tenis de mesa.

Perfil do atleta:
{athlete_profile}

Dados tecnicos do setup atual:
{enriched_setup}

Responda em {user_language}.
Retorne exclusivamente JSON valido no formato do contrato AnalyzeResponse, sem texto adicional.

Analise tecnicamente o setup atual do atleta:
- avalie a lamina individualmente
- avalie a borracha FH individualmente
- avalie a borracha BH individualmente
- avalie a sinergia da combinacao completa
- identifique pontos positivos, limitacoes e riscos

Calibre a linguagem pelo campo confianca de cada peca:
- alta: afirmacoes diretas
- media: afirmacoes diretas sem extrapolar dados ausentes
- baixa: use linguagem cautelosa como 'com base nos dados disponiveis'
- insuficiente: deixe explicito que faltam dados minimos

Se aprovado_competicao for false em borracha_fh ou borracha_bh,
inclua o alerta_larc correspondente na avaliacao daquela borracha.
Nunca gere alerta de irregularidade para a lamina.
"""


def validate_analysis_payload(payload: dict) -> AnalyzeResponse:
    """Valida o payload de analise antes de enviar ao app."""

    return AnalyzeResponse.model_validate(payload)


__all__ = ["build_local_response", "build_sonnet_prompt", "validate_analysis_payload"]
