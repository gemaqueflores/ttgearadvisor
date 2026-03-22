import { ScrollView, StyleSheet, Text, TextInput, View } from "react-native";

import { AppCard } from "@/src/components/AppCard";
import { AppChipRow } from "@/src/components/AppChipRow";
import { AppPrimaryButton } from "@/src/components/AppPrimaryButton";
import { useAppTranslation } from "@/src/i18n/provider";
import {
  evolutionGoalOptions,
  frequencyOptions,
  gripOptions,
  issueOptions,
  levelOptions,
  strengthOptions,
  styleOptions,
  weaknessOptions,
} from "@/src/mock/options";

export default function ProfileScreen() {
  const { t } = useAppTranslation();

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
      <View style={styles.hero}>
        <Text style={styles.eyebrow}>{t("hero.eyebrow")}</Text>
        <Text style={styles.title}>{t("hero.title")}</Text>
        <Text style={styles.description}>{t("hero.description")}</Text>
      </View>

      <AppCard title={t("sections.playingProfile")}>
        <AppChipRow label={t("fields.level")} options={levelOptions} />
        <AppChipRow label={t("fields.style")} options={styleOptions} />
        <AppChipRow label={t("fields.grip")} options={gripOptions} />
        <AppChipRow label={t("fields.frequency")} options={frequencyOptions} />
        <AppChipRow label={t("fields.strengths")} options={strengthOptions} />
        <AppChipRow label={t("fields.weaknesses")} options={weaknessOptions} />
      </AppCard>

      <AppCard title={t("sections.currentSetup")}>
        <Text style={styles.fieldLabel}>{t("fields.blade")}</Text>
        <TextInput style={styles.input} value="Butterfly Primorac Carbon" />
        <Text style={styles.fieldLabel}>{t("fields.forehandRubber")}</Text>
        <TextInput style={styles.input} value="DHS Hurricane 3 Neo 2.1" />
        <Text style={styles.fieldLabel}>{t("fields.backhandRubber")}</Text>
        <TextInput style={styles.input} value="Xiom Vega Intro 2.0" />
      </AppCard>

      <AppCard title={t("sections.history")}>
        <AppChipRow label={t("fields.issues")} options={issueOptions} />
        <AppChipRow label={t("fields.goal")} options={evolutionGoalOptions} />
        <Text style={styles.fieldLabel}>{t("fields.notes")}</Text>
        <TextInput
          style={[styles.input, styles.textArea]}
          multiline
          value={t("mock.notes")}
        />
      </AppCard>

      <AppPrimaryButton label={t("actions.generate")} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: "#f3ecdf" },
  content: { gap: 16, padding: 20, paddingBottom: 120 },
  hero: { gap: 8, paddingTop: 18 },
  eyebrow: {
    alignSelf: "flex-start",
    backgroundColor: "#f7d8b8",
    borderRadius: 999,
    color: "#8c4307",
    fontSize: 12,
    fontWeight: "700",
    letterSpacing: 1,
    paddingHorizontal: 12,
    paddingVertical: 6,
    textTransform: "uppercase",
  },
  title: { color: "#18242d", fontSize: 30, fontWeight: "800", lineHeight: 34 },
  description: { color: "#55656f", fontSize: 15, lineHeight: 22 },
  fieldLabel: {
    color: "#22343f",
    fontSize: 14,
    fontWeight: "700",
    marginBottom: 8,
    marginTop: 2,
  },
  input: {
    backgroundColor: "#fffaf1",
    borderColor: "#dfd2bf",
    borderRadius: 16,
    borderWidth: 1,
    color: "#22343f",
    marginBottom: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
  },
  textArea: { minHeight: 96, textAlignVertical: "top" },
});
