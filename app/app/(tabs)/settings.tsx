import { StyleSheet, Text, View } from "react-native";

import { AppCard } from "@/src/components/AppCard";
import { AppChipRow } from "@/src/components/AppChipRow";
import { useAppTranslation } from "@/src/i18n/provider";

export default function SettingsScreen() {
  const { t, i18n } = useAppTranslation();

  const localeOptions = [
    { value: "pt-BR", label: "pt-BR" },
    { value: "en-US", label: "en-US" },
  ];

  return (
    <View style={styles.screen}>
      <AppCard title={t("settings.languageTitle")}>
        <Text style={styles.copy}>{t("settings.languageDescription")}</Text>
        <AppChipRow
          label={t("settings.languageLabel")}
          options={localeOptions}
          value={i18n.language}
          onChange={(value) => {
            void i18n.changeLanguage(value as string);
          }}
        />
      </AppCard>

      <AppCard title={t("settings.profileTitle")}>
        <Text style={styles.copy}>{t("settings.profileDescription")}</Text>
      </AppCard>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: "#f3ecdf",
    gap: 16,
    padding: 20,
    paddingTop: 28,
  },
  copy: { color: "#55656f", fontSize: 14, lineHeight: 21 },
});
