from typing import Literal

from pydantic import BaseModel, Field


class SetupSide(BaseModel):
    marca: str | None = None
    modelo: str | None = None
    espessura: str | None = None


class BackhandRecommendation(BaseModel):
    tipo: Literal["convencional", "dorso-liso"]
    marca: str | None = None
    modelo: str | None = None
    espessura: str | None = None
    observacao: str | None = None


class RankedRecommendation(BaseModel):
    rank: int = Field(ge=1, le=3)
    lamina: SetupSide
    borracha_fh: SetupSide
    borracha_bh: BackhandRecommendation
    justificativa_lamina: str
    justificativa_fh: str
    justificativa_bh: str | None = None
    justificativa_combinacao: str
    faixa_preco_total_usd: str


class SetupAnalysis(BaseModel):
    pontos_positivos: list[str]
    limitacoes: list[str]
    riscos: list[str]


class Roadmap(BaseModel):
    trocar_agora: list[str]
    trocar_depois: list[str]
    justificativa: str


class AnalyzeResponse(BaseModel):
    analise_perfil: str
    analise_setup_atual: SetupAnalysis
    recomendacoes: list[RankedRecommendation]
    roadmap: Roadmap
