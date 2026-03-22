from models import AnalyzeResponse
from schemas import AthleteProfileInput


def build_mock_response(profile: AthleteProfileInput) -> AnalyzeResponse:
    """Retorna resposta estruturada temporaria ate a integracao com a Anthropic."""

    return AnalyzeResponse.model_validate(
        {
            "analise_perfil": (
                f"Perfil {profile.estilo} com empunhadura {profile.empunhadura}, "
                "orientado para um setup de progressao controlada."
            ),
            "analise_setup_atual": {
                "pontos_positivos": [
                    "O setup atual ja oferece base ofensiva para o FH."
                ],
                "limitacoes": [
                    "O controle fino do jogo curto ainda parece abaixo do ideal."
                ],
                "riscos": [
                    "A distribuicao de peso pode prejudicar o BH em treinos longos."
                ],
            },
            "recomendacoes": [
                {
                    "rank": 1,
                    "lamina": {"marca": "Nittaku", "modelo": "Acoustic"},
                    "borracha_fh": {
                        "marca": "DHS",
                        "modelo": "Hurricane 3 Neo",
                        "espessura": "2.1",
                    },
                    "borracha_bh": {
                        "tipo": "convencional",
                        "marca": "Yasaka",
                        "modelo": "Rakza 7 Soft",
                        "espessura": "2.0",
                        "observacao": None,
                    },
                    "justificativa_lamina": "Mais dwell e melhor controle para topspin de progressao.",
                    "justificativa_fh": "Mantem spin forte no FH sem descaracterizar o estilo ofensivo.",
                    "justificativa_bh": "Entrega mais estabilidade e controle no BH moderno.",
                    "justificativa_combinacao": "A combinacao reduz rigidez excessiva e melhora equilibrio geral.",
                    "faixa_preco_total_usd": "premium",
                }
            ],
            "roadmap": {
                "trocar_agora": ["Borracha BH"],
                "trocar_depois": ["Lamina"],
                "justificativa": "Comecar pela peca de menor custo para corrigir controle e peso.",
            },
        }
    )
