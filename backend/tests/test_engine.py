from __future__ import annotations

import sys
import unittest
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from engine import build_local_response  # noqa: E402
from models import AnalysisConfidence  # noqa: E402
from schemas import AthleteProfileInput  # noqa: E402
from enrich import enrich_setup  # noqa: E402


class EngineTests(unittest.TestCase):
    def test_response_includes_confidence_and_field_lists(self) -> None:
        profile = AthleteProfileInput.model_validate(
            {
                "nivel": "intermediario",
                "estilo": "ofensivo",
                "empunhadura": "shakehand",
                "lado_dominante": "destro",
                "frequencia": "3-4x/semana",
                "pontos_fortes": ["topspin"],
                "pontos_fracos": ["recepcao"],
                "material_atual": {
                    "lamina_marca": "Butterfly",
                    "lamina_modelo": "Viscaria",
                    "borracha_fh_marca": "Butterfly",
                    "borracha_fh_modelo": "Tenergy 05",
                    "borracha_fh_espessura": "2.1",
                    "borracha_bh_marca": "Butterfly",
                    "borracha_bh_modelo": "Rozena",
                    "borracha_bh_espessura": "1.9",
                    "borracha_bh_tipo": "convencional",
                    "tempo_setup_atual": "1 ano",
                },
                "materiais_anteriores": "",
                "problemas_percebidos": ["controle"],
                "observacoes": "",
                "objetivo": "equilibrio",
            }
        )
        enriched = enrich_setup(profile)
        response = build_local_response(profile, enriched)

        self.assertIn(response.analise_setup_atual.lamina.confianca, set(AnalysisConfidence))
        self.assertIsInstance(response.analise_setup_atual.lamina.campos_utilizados, list)
        self.assertIsInstance(response.analise_setup_atual.lamina.campos_ausentes, list)
        self.assertIn(response.analise_setup_atual.borracha_fh.confianca, set(AnalysisConfidence))
        self.assertIsInstance(response.analise_setup_atual.borracha_fh.campos_utilizados, list)
        self.assertIsInstance(response.analise_setup_atual.borracha_fh.campos_ausentes, list)

    def test_missing_item_yields_insufficient_confidence(self) -> None:
        profile = AthleteProfileInput.model_validate(
            {
                "nivel": "intermediario",
                "estilo": "ofensivo",
                "empunhadura": "shakehand",
                "lado_dominante": "destro",
                "frequencia": "3-4x/semana",
                "pontos_fortes": ["topspin"],
                "pontos_fracos": ["recepcao"],
                "material_atual": {
                    "lamina_marca": "Marca Inexistente",
                    "lamina_modelo": "Modelo Inexistente",
                    "borracha_fh_marca": "Marca Inexistente",
                    "borracha_fh_modelo": "Modelo Inexistente",
                    "borracha_fh_espessura": "2.1",
                    "borracha_bh_marca": "Marca Inexistente",
                    "borracha_bh_modelo": "Modelo Inexistente",
                    "borracha_bh_espessura": "2.0",
                    "borracha_bh_tipo": "convencional",
                    "tempo_setup_atual": "6 meses",
                },
                "materiais_anteriores": "",
                "problemas_percebidos": ["controle"],
                "observacoes": "",
                "objetivo": "equilibrio",
            }
        )
        response = build_local_response(profile, enrich_setup(profile))

        self.assertEqual(response.analise_setup_atual.lamina.confianca, AnalysisConfidence.INSUFICIENTE)
        self.assertEqual(response.analise_setup_atual.borracha_fh.confianca, AnalysisConfidence.INSUFICIENTE)


if __name__ == "__main__":
    unittest.main()
