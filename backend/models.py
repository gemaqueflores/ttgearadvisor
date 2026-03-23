from enum import Enum

from pydantic import BaseModel


class AnalysisConfidence(str, Enum):
    ALTA = "alta"
    MEDIA = "media"
    BAIXA = "baixa"
    INSUFICIENTE = "insuficiente"


class ProfileAnalysis(BaseModel):
    resumo: str
    compatibilidade_estilo_nivel: str
    pontos_atencao: list[str]


class ItemAnalysis(BaseModel):
    confianca: AnalysisConfidence
    campos_utilizados: list[str]
    campos_ausentes: list[str]
    avaliacao: str
    pontos_positivos: list[str]
    limitacoes: list[str]


class BladeAnalysis(ItemAnalysis):
    pass


class RubberAnalysis(ItemAnalysis):
    aprovado_competicao: bool
    alerta_larc: str | None = None


class CurrentSetupAnalysis(BaseModel):
    lamina: BladeAnalysis
    borracha_fh: RubberAnalysis
    borracha_bh: RubberAnalysis
    sinergia_combinacao: str
    riscos: list[str]


class AnalyzeResponse(BaseModel):
    analise_perfil: ProfileAnalysis
    analise_setup_atual: CurrentSetupAnalysis


class ErrorResponse(BaseModel):
    error: str
    detail: str
