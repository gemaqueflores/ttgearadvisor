export type AthleteProfileInput = {
  nivel: "iniciante" | "intermediario" | "avancado" | "federado";
  estilo: "ofensivo" | "defensivo" | "all-round";
  empunhadura: "shakehand" | "penhold-classico" | "classineta";
  lado_dominante: "destro" | "canhoto";
  frequencia: "ocasional" | "1-2x/semana" | "3-4x/semana" | "diario" | "federado";
  pontos_fortes: string[];
  pontos_fracos: string[];
  material_atual: {
    lamina_marca: string;
    lamina_modelo: string;
    borracha_fh_marca: string;
    borracha_fh_modelo: string;
    borracha_fh_espessura: string;
    borracha_bh_marca?: string | null;
    borracha_bh_modelo?: string | null;
    borracha_bh_espessura?: string | null;
    borracha_bh_tipo: "convencional" | "dorso-liso";
    tempo_setup_atual: string;
  };
  materiais_anteriores: string;
  problemas_percebidos: string[];
  observacoes: string;
  objetivo:
    | "mais-velocidade"
    | "mais-spin"
    | "mais-controle"
    | "equilibrio"
    | "competicao-federada";
};

export type AnalyzeResponse = {
  analise_perfil: {
    resumo: string;
    compatibilidade_estilo_nivel: string;
    pontos_atencao: string[];
  };
  analise_setup_atual: {
    lamina: {
      confianca: "alta" | "media" | "baixa" | "insuficiente";
      campos_utilizados: string[];
      campos_ausentes: string[];
      avaliacao: string;
      pontos_positivos: string[];
      limitacoes: string[];
    };
    borracha_fh: {
      confianca: "alta" | "media" | "baixa" | "insuficiente";
      campos_utilizados: string[];
      campos_ausentes: string[];
      avaliacao: string;
      aprovado_competicao: boolean;
      alerta_larc?: string | null;
      pontos_positivos: string[];
      limitacoes: string[];
    };
    borracha_bh: {
      confianca: "alta" | "media" | "baixa" | "insuficiente";
      campos_utilizados: string[];
      campos_ausentes: string[];
      avaliacao: string;
      aprovado_competicao: boolean;
      alerta_larc?: string | null;
      pontos_positivos: string[];
      limitacoes: string[];
    };
    sinergia_combinacao: string;
    riscos: string[];
  };
};
