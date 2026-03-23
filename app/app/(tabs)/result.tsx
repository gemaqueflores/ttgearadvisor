import { ScrollView, StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";

import { AppCard } from "@/src/components/AppCard";
import { AppPrimaryButton } from "@/src/components/AppPrimaryButton";
import { useAppTranslation } from "@/src/i18n/provider";
import { useAdvisor } from "@/src/state/advisor-provider";
import type { AnalyzeResponse } from "@/src/types/api";

function getConfidenceTone(confidence: AnalyzeResponse["analise_setup_atual"]["lamina"]["confianca"]) {
  switch (confidence) {
    case "alta":
      return {
        container: styles.confidenceHigh,
        title: styles.confidenceHighTitle,
      };
    case "media":
      return {
        container: styles.confidenceMedium,
        title: styles.confidenceMediumTitle,
      };
    case "baixa":
      return {
        container: styles.confidenceLow,
        title: styles.confidenceLowTitle,
      };
    default:
      return {
        container: styles.confidenceInsufficient,
        title: styles.confidenceInsufficientTitle,
      };
  }
}

function PieceAnalysisCard({
  title,
  piece,
  t,
  showCompetitionStatus = true,
}: {
  title: string;
  piece:
    | AnalyzeResponse["analise_setup_atual"]["lamina"]
    | AnalyzeResponse["analise_setup_atual"]["borracha_fh"];
  t: (key: string) => string;
  showCompetitionStatus?: boolean;
}) {
  const confidenceTone = getConfidenceTone(piece.confianca);

  return (
    <AppCard title={title}>
      <Text style={styles.copy}>{piece.avaliacao}</Text>
      <View style={[styles.confidenceBox, confidenceTone.container]}>
        <Text style={[styles.confidenceTitle, confidenceTone.title]}>
          {t("result.confidence")}: {t(`result.confidenceLevels.${piece.confianca}`)}
        </Text>
        <Text style={styles.confidenceCopy}>{t(`result.confidenceDescriptions.${piece.confianca}`)}</Text>
      </View>
      <Text style={styles.subTitle}>{t("result.usedFields")}</Text>
      {piece.campos_utilizados.length > 0 ? (
        piece.campos_utilizados.map((item) => (
          <Text key={`${title}-u-${item}`} style={styles.bullet}>{`\u2022 ${item}`}</Text>
        ))
      ) : (
        <Text style={styles.copy}>-</Text>
      )}
      <Text style={styles.subTitle}>{t("result.missingFields")}</Text>
      {piece.campos_ausentes.length > 0 ? (
        piece.campos_ausentes.map((item) => (
          <Text key={`${title}-m-${item}`} style={styles.bullet}>{`\u2022 ${item}`}</Text>
        ))
      ) : (
        <Text style={styles.copy}>-</Text>
      )}
      {showCompetitionStatus ? (
        <Text style={styles.meta}>
          {t("result.competitionApproval")}:{" "}
          {"aprovado_competicao" in piece && piece.aprovado_competicao ? t("result.approved") : t("result.notApproved")}
        </Text>
      ) : null}
      {showCompetitionStatus && "alerta_larc" in piece && piece.alerta_larc ? (
        <View style={styles.alertBox}>
          <Text style={styles.alertTitle}>{t("result.larcAlertTitle")}</Text>
          <Text style={styles.alertCopy}>{piece.alerta_larc}</Text>
        </View>
      ) : null}
      <Text style={styles.subTitle}>{t("result.positives")}</Text>
      {piece.pontos_positivos.map((item) => (
        <Text key={`${title}-p-${item}`} style={styles.bullet}>{`\u2022 ${item}`}</Text>
      ))}
      <Text style={styles.subTitle}>{t("result.limitations")}</Text>
      {piece.limitacoes.map((item) => (
        <Text key={`${title}-l-${item}`} style={styles.bullet}>{`\u2022 ${item}`}</Text>
      ))}
    </AppCard>
  );
}

export default function ResultScreen() {
  const { t } = useAppTranslation();
  const router = useRouter();
  const { result, isLoading } = useAdvisor();

  if (!result) {
    return (
      <View style={styles.emptyState}>
        <Text style={styles.emptyTitle}>{t("result.emptyTitle")}</Text>
        <Text style={styles.emptyCopy}>{t("result.emptyDescription")}</Text>
        <AppPrimaryButton label={t("result.emptyAction")} onPress={() => router.push("/")} />
      </View>
    );
  }

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
      <AppCard title={t("result.profileAnalysis")}>
        <Text style={styles.copy}>{result.analise_perfil.resumo}</Text>
        <Text style={styles.copy}>{result.analise_perfil.compatibilidade_estilo_nivel}</Text>
        {result.analise_perfil.pontos_atencao.map((item) => (
          <Text key={`profile-${item}`} style={styles.bullet}>{`\u2022 ${item}`}</Text>
        ))}
      </AppCard>

      <PieceAnalysisCard
        title={t("result.blade")}
        piece={result.analise_setup_atual.lamina}
        t={t}
        showCompetitionStatus={false}
      />
      <PieceAnalysisCard title={t("result.forehandRubber")} piece={result.analise_setup_atual.borracha_fh} t={t} />
      <PieceAnalysisCard title={t("result.backhandRubber")} piece={result.analise_setup_atual.borracha_bh} t={t} />

      <AppCard title={t("result.currentSetupAnalysis")}>
        <Text style={styles.subTitle}>{t("result.synergy")}</Text>
        <Text style={styles.copy}>{result.analise_setup_atual.sinergia_combinacao}</Text>
        <Text style={styles.subTitle}>{t("result.risks")}</Text>
        {result.analise_setup_atual.riscos.map((item) => (
          <Text key={`r-${item}`} style={styles.bullet}>{`\u2022 ${item}`}</Text>
        ))}
      </AppCard>

      <AppCard title={t("result.scopeTitle")}>
        <Text style={styles.copy}>{t("result.scopeDescription")}</Text>
      </AppCard>

      {isLoading ? <Text style={styles.loadingText}>{t("actions.generating")}</Text> : null}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: "#f3ecdf" },
  content: { gap: 16, padding: 20, paddingBottom: 120 },
  copy: { color: "#55656f", fontSize: 14, lineHeight: 21 },
  bullet: { color: "#44545d", fontSize: 14, lineHeight: 22 },
  subTitle: { color: "#18242d", fontSize: 13, fontWeight: "800", marginTop: 10, marginBottom: 4 },
  meta: { color: "#8c4307", fontSize: 13, fontWeight: "700", marginTop: 8 },
  confidenceBox: {
    borderRadius: 14,
    gap: 4,
    marginTop: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  confidenceTitle: { fontSize: 13, fontWeight: "800" },
  confidenceCopy: { color: "#55656f", fontSize: 13, lineHeight: 19 },
  confidenceHigh: {
    backgroundColor: "#f7efe4",
    borderColor: "#ead6bc",
    borderWidth: 1,
  },
  confidenceHighTitle: { color: "#61452a" },
  confidenceMedium: {
    backgroundColor: "#eef4f7",
    borderColor: "#bfd3df",
    borderWidth: 1,
  },
  confidenceMediumTitle: { color: "#2f6179" },
  confidenceLow: {
    backgroundColor: "#fff6dc",
    borderColor: "#e2bf58",
    borderWidth: 1,
  },
  confidenceLowTitle: { color: "#8a5b00" },
  confidenceInsufficient: {
    backgroundColor: "#ececec",
    borderColor: "#c8c8c8",
    borderWidth: 1,
  },
  confidenceInsufficientTitle: { color: "#636363" },
  alertBox: {
    backgroundColor: "#fff1db",
    borderColor: "#e8b36a",
    borderWidth: 1,
    borderRadius: 12,
    gap: 6,
    marginTop: 10,
    padding: 12,
  },
  alertTitle: { color: "#8c4307", fontSize: 12, fontWeight: "800" },
  alertCopy: { color: "#6d5126", fontSize: 13, lineHeight: 20 },
  loadingText: { color: "#8c4307", fontSize: 14, fontWeight: "700" },
  emptyState: {
    flex: 1,
    backgroundColor: "#f3ecdf",
    gap: 16,
    justifyContent: "center",
    padding: 24,
  },
  emptyTitle: { color: "#18242d", fontSize: 24, fontWeight: "800" },
  emptyCopy: { color: "#55656f", fontSize: 15, lineHeight: 24 },
});
