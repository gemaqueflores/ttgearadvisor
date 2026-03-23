from __future__ import annotations

import sys
import unittest
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from dataset import load_larc  # noqa: E402
from enrich import check_larc, enrich_setup  # noqa: E402
from schemas import AthleteProfileInput  # noqa: E402


class EnrichSetupTests(unittest.TestCase):
    def test_priority_larc_rubbers_are_approved(self) -> None:
        priority_rubbers = [
            ("Butterfly", "Tenergy 05"),
            ("Butterfly", "Tenergy 64"),
            ("Butterfly", "Tenergy 80"),
            ("Butterfly", "Rozena"),
            ("Butterfly", "Dignics 05"),
            ("Butterfly", "Dignics 09C"),
            ("DHS", "Hurricane 3"),
            ("DHS", "Hurricane 3 Neo"),
            ("DHS", "Hurricane 8"),
            ("Xiom", "Vega Europe"),
            ("Xiom", "Vega Pro"),
            ("Xiom", "Vega Asia"),
            ("Yasaka", "Mark V"),
            ("Yasaka", "Rakza 7"),
            ("Tibhar", "Evolution MX-P"),
            ("Tibhar", "Aurus"),
        ]

        larc = load_larc()

        for brand, model in priority_rubbers:
            with self.subTest(brand=brand, model=model):
                approved, alert = check_larc(brand, model, larc)
                self.assertTrue(approved)
                self.assertIsNone(alert)

    def test_larc_is_checked_only_for_rubbers(self) -> None:
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
                    "lamina_marca": "61 Second",
                    "lamina_modelo": "3004",
                    "borracha_fh_marca": "61 Second",
                    "borracha_fh_modelo": "Eagle",
                    "borracha_fh_espessura": "2.1",
                    "borracha_bh_marca": "61 Second",
                    "borracha_bh_modelo": "Kangaroo",
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

        enriched = enrich_setup(profile)

        self.assertIsNone(getattr(enriched.lamina, "aprovado_larc", None))
        self.assertFalse(enriched.borracha_fh.aprovado_larc)
        self.assertIsNotNone(enriched.borracha_fh.alerta_larc)

    def test_dorso_liso_short_circuits_backhand_lookup(self) -> None:
        profile = AthleteProfileInput.model_validate(
            {
                "nivel": "intermediario",
                "estilo": "ofensivo",
                "empunhadura": "penhold-classico",
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
                    "borracha_bh_marca": None,
                    "borracha_bh_modelo": None,
                    "borracha_bh_espessura": None,
                    "borracha_bh_tipo": "dorso-liso",
                    "tempo_setup_atual": "1 ano",
                },
                "materiais_anteriores": "",
                "problemas_percebidos": ["controle"],
                "observacoes": "",
                "objetivo": "equilibrio",
            }
        )

        enriched = enrich_setup(profile)

        self.assertIsNotNone(enriched.borracha_bh)
        self.assertTrue(enriched.borracha_bh.aprovado_larc)
        self.assertIsNone(enriched.borracha_bh.rubber)


if __name__ == "__main__":
    unittest.main()
