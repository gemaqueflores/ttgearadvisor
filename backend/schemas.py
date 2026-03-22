from typing import Literal

from pydantic import BaseModel


class CurrentSetupInput(BaseModel):
    lamina_marca: str
    lamina_modelo: str
    borracha_fh_marca: str
    borracha_fh_modelo: str
    borracha_fh_espessura: str
    borracha_bh_marca: str | None = None
    borracha_bh_modelo: str | None = None
    borracha_bh_espessura: str | None = None
    borracha_bh_tipo: Literal["convencional", "dorso-liso"] = "convencional"
    tempo_setup_atual: str


class AthleteProfileInput(BaseModel):
    nivel: Literal["iniciante", "intermediario", "avancado", "federado"]
    estilo: Literal["ofensivo", "defensivo", "all-round"]
    empunhadura: Literal["shakehand", "penhold-classico", "classineta"]
    lado_dominante: Literal["destro", "canhoto"]
    frequencia: Literal["ocasional", "1-2x/semana", "3-4x/semana", "diario", "federado"]
    pontos_fortes: list[str]
    pontos_fracos: list[str]
    material_atual: CurrentSetupInput
    materiais_anteriores: str = ""
    problemas_percebidos: list[str]
    observacoes: str = ""
    objetivo: Literal[
        "mais-velocidade",
        "mais-spin",
        "mais-controle",
        "equilibrio",
        "competicao-federada",
    ]
