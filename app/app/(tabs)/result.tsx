import { ScrollView, StyleSheet, Text, View } from "react-native";

import { AppCard } from "@/src/components/AppCard";
import { useAppTranslation } from "@/src/i18n/provider";
import { sampleRecommendations } from "@/src/mock/recommendations";

export default function ResultScreen() {
  const { t } = useAppTranslation();

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
      <AppCard title={t("result.profileAnalysis")}>
        <Text style={styles.copy}>{t("mock.profileAnalysis")}</Text>
      </AppCard>

      <AppCard title={t("result.currentSetupAnalysis")}>
        <Text style={styles.bullet}>{`\u2022 ${t("mock.currentSetupPositive")}`}</Text>
        <Text style={styles.bullet}>{`\u2022 ${t("mock.currentSetupLimitation")}`}</Text>
        <Text style={styles.bullet}>{`\u2022 ${t("mock.currentSetupRisk")}`}</Text>
      </AppCard>

      <AppCard title={t("result.recommendations")}>
        <View style={styles.stack}>
          {sampleRecommendations.map((item) => (
            <View key={item.rank} style={styles.recommendation}>
              <View style={styles.headerRow}>
                <Text style={styles.rank}>#{item.rank}</Text>
                <Text style={styles.score}>{item.score}</Text>
              </View>
              <Text style={styles.title}>{item.title}</Text>
              <Text style={styles.copy}>{item.summary}</Text>
            </View>
          ))}
        </View>
      </AppCard>

      <AppCard title={t("result.roadmap")}>
        <Text style={styles.bullet}>{`\u2022 ${t("mock.roadmapNow")}`}</Text>
        <Text style={styles.bullet}>{`\u2022 ${t("mock.roadmapLater")}`}</Text>
      </AppCard>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: "#f3ecdf" },
  content: { gap: 16, padding: 20, paddingBottom: 120 },
  stack: { gap: 12 },
  recommendation: {
    backgroundColor: "#fffaf1",
    borderColor: "#e2d4be",
    borderRadius: 18,
    borderWidth: 1,
    gap: 8,
    padding: 14,
  },
  headerRow: { flexDirection: "row", justifyContent: "space-between" },
  rank: { color: "#18242d", fontSize: 16, fontWeight: "800" },
  score: { color: "#8c4307", fontSize: 14, fontWeight: "700" },
  title: { color: "#18242d", fontSize: 16, fontWeight: "700" },
  copy: { color: "#55656f", fontSize: 14, lineHeight: 21 },
  bullet: { color: "#44545d", fontSize: 14, lineHeight: 22 },
});
