import { useMemo, useState } from "react";
import { ScrollView, StyleSheet, Text, TextInput, View } from "react-native";
import { useRouter } from "expo-router";

import autocompleteOptions from "@/src/data/setup-autocomplete.json";
import { AppAutocompleteField } from "@/src/components/AppAutocompleteField";
import { AppCard } from "@/src/components/AppCard";
import { AppChipRow } from "@/src/components/AppChipRow";
import { AppPrimaryButton } from "@/src/components/AppPrimaryButton";
import { useAppTranslation } from "@/src/i18n/provider";
import { useAdvisor } from "@/src/state/advisor-provider";
import type { AthleteProfileInput } from "@/src/types/api";

type Option = { label: string; value: string };

type SetupAutocompleteOptions = typeof autocompleteOptions;

const defaultProfile: AthleteProfileInput = {
  nivel: "intermediario",
  estilo: "ofensivo",
  empunhadura: "classineta",
  lado_dominante: "destro",
  frequencia: "3-4x/semana",
  pontos_fortes: ["topspin-fh"],
  pontos_fracos: ["peso-setup"],
  material_atual: {
    lamina_marca: "Butterfly",
    lamina_modelo: "Primorac Carbon",
    borracha_fh_marca: "DHS",
    borracha_fh_modelo: "Hurricane 3 Neo",
    borracha_fh_espessura: "2.1",
    borracha_bh_marca: "Xiom",
    borracha_bh_modelo: "Vega Intro",
    borracha_bh_espessura: "2.0",
    borracha_bh_tipo: "convencional",
    tempo_setup_atual: "8 meses",
  },
  materiais_anteriores: "",
  problemas_percebidos: ["peso-alto", "pouco-controle"],
  observacoes: "Sensacao rigida no jogo curto e BH cansando ao fim do treino.",
  objetivo: "equilibrio",
};

function useProfileOptions(t: (key: string) => string) {
  return useMemo(
    () => ({
      levels: [
        { value: "iniciante", label: t("options.level.iniciante") },
        { value: "intermediario", label: t("options.level.intermediario") },
        { value: "avancado", label: t("options.level.avancado") },
        { value: "federado", label: t("options.level.federado") },
      ] satisfies Option[],
      styles: [
        { value: "ofensivo", label: t("options.style.ofensivo") },
        { value: "defensivo", label: t("options.style.defensivo") },
        { value: "all-round", label: t("options.style.allRound") },
      ] satisfies Option[],
      grips: [
        { value: "shakehand", label: t("options.grip.shakehand") },
        { value: "penhold-classico", label: t("options.grip.penholdClassico") },
        { value: "classineta", label: t("options.grip.classineta") },
      ] satisfies Option[],
      dominantSides: [
        { value: "destro", label: t("options.dominantSide.destro") },
        { value: "canhoto", label: t("options.dominantSide.canhoto") },
      ] satisfies Option[],
      frequencies: [
        { value: "ocasional", label: t("options.frequency.ocasional") },
        { value: "1-2x/semana", label: t("options.frequency.x1_2") },
        { value: "3-4x/semana", label: t("options.frequency.x3_4") },
        { value: "diario", label: t("options.frequency.diario") },
        { value: "federado", label: t("options.frequency.federado") },
      ] satisfies Option[],
      strengths: [
        { value: "topspin-fh", label: t("options.strength.topspinFh") },
        { value: "recepcao", label: t("options.strength.recepcao") },
        { value: "bloqueio", label: t("options.strength.bloqueio") },
        { value: "jogo-curto", label: t("options.strength.jogoCurto") },
      ] satisfies Option[],
      weaknesses: [
        { value: "bh-passivo", label: t("options.weakness.bhPassivo") },
        { value: "arco-baixo", label: t("options.weakness.arcoBaixo") },
        { value: "peso-setup", label: t("options.weakness.pesoSetup") },
        { value: "inconstancia", label: t("options.weakness.inconstancia") },
      ] satisfies Option[],
      issues: [
        { value: "toque-duro", label: t("options.issue.toqueDuro") },
        { value: "pouco-controle", label: t("options.issue.poucoControle") },
        { value: "peso-alto", label: t("options.issue.pesoAlto") },
        { value: "falta-spin", label: t("options.issue.faltaSpin") },
      ] satisfies Option[],
      goals: [
        { value: "mais-velocidade", label: t("options.goal.maisVelocidade") },
        { value: "mais-spin", label: t("options.goal.maisSpin") },
        { value: "mais-controle", label: t("options.goal.maisControle") },
        { value: "equilibrio", label: t("options.goal.equilibrio") },
        { value: "competicao-federada", label: t("options.goal.competicaoFederada") },
      ] satisfies Option[],
      backhandTypes: [
        { value: "convencional", label: t("options.backhandType.convencional") },
        { value: "dorso-liso", label: t("options.backhandType.dorsoLiso") },
      ] satisfies Option[],
    }),
    [t],
  );
}

function normalizeForSearch(value: string) {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();
}

export default function ProfileScreen() {
  const { t } = useAppTranslation();
  const router = useRouter();
  const { analyze, isLoading, error } = useAdvisor();
  const options = useProfileOptions(t);
  const [profile, setProfile] = useState<AthleteProfileInput>(defaultProfile);

  const bladeModelOptions = useMemo(() => {
    const selectedBrand = normalizeForSearch(profile.material_atual.lamina_marca);
    return (autocompleteOptions as SetupAutocompleteOptions).bladeModels
      .filter((item) => !selectedBrand || normalizeForSearch(item.brand).includes(selectedBrand))
      .map((item) => item.model);
  }, [profile.material_atual.lamina_marca]);

  const forehandModelOptions = useMemo(() => {
    const selectedBrand = normalizeForSearch(profile.material_atual.borracha_fh_marca);
    return (autocompleteOptions as SetupAutocompleteOptions).rubberModels
      .filter((item) => !selectedBrand || normalizeForSearch(item.brand).includes(selectedBrand))
      .map((item) => item.model);
  }, [profile.material_atual.borracha_fh_marca]);

  const backhandModelOptions = useMemo(() => {
    const selectedBrand = normalizeForSearch(profile.material_atual.borracha_bh_marca ?? "");
    return (autocompleteOptions as SetupAutocompleteOptions).rubberModels
      .filter((item) => !selectedBrand || normalizeForSearch(item.brand).includes(selectedBrand))
      .map((item) => item.model);
  }, [profile.material_atual.borracha_bh_marca]);

  function updateMaterialField(
    field: keyof AthleteProfileInput["material_atual"],
    value: string | null,
  ) {
    setProfile((current) => ({
      ...current,
      material_atual: { ...current.material_atual, [field]: value },
    }));
  }

  function selectMaterialFields(
    fields: Partial<AthleteProfileInput["material_atual"]>,
  ) {
    setProfile((current) => ({
      ...current,
      material_atual: {
        ...current.material_atual,
        ...fields,
      },
    }));
  }

  function updateBackhandType(value: "convencional" | "dorso-liso") {
    setProfile((current) => ({
      ...current,
      material_atual: {
        ...current.material_atual,
        borracha_bh_tipo: value,
        borracha_bh_marca: value === "dorso-liso" ? null : current.material_atual.borracha_bh_marca ?? "",
        borracha_bh_modelo: value === "dorso-liso" ? null : current.material_atual.borracha_bh_modelo ?? "",
        borracha_bh_espessura: value === "dorso-liso" ? null : current.material_atual.borracha_bh_espessura ?? "",
      },
    }));
  }

  async function handleAnalyze() {
    try {
      await analyze(profile);
      router.push("/result");
    } catch {
      // O erro ja fica exposto pelo provider para a UI.
    }
  }

  return (
    <ScrollView
      style={styles.screen}
      contentContainerStyle={styles.content}
      keyboardShouldPersistTaps="handled"
    >
      <View style={styles.hero}>
        <Text style={styles.eyebrow}>{t("hero.eyebrow")}</Text>
        <Text style={styles.title}>{t("hero.title")}</Text>
        <Text style={styles.description}>{t("hero.description")}</Text>
      </View>

      <AppCard title={t("sections.playingProfile")}>
        <AppChipRow
          label={t("fields.level")}
          options={options.levels}
          value={profile.nivel}
          onChange={(value) => setProfile((current) => ({ ...current, nivel: value as AthleteProfileInput["nivel"] }))}
        />
        <AppChipRow
          label={t("fields.style")}
          options={options.styles}
          value={profile.estilo}
          onChange={(value) => setProfile((current) => ({ ...current, estilo: value as AthleteProfileInput["estilo"] }))}
        />
        <AppChipRow
          label={t("fields.grip")}
          options={options.grips}
          value={profile.empunhadura}
          onChange={(value) =>
            setProfile((current) => ({
              ...current,
              empunhadura: value as AthleteProfileInput["empunhadura"],
              material_atual: {
                ...current.material_atual,
                borracha_bh_tipo: value === "penhold-classico" ? "dorso-liso" : "convencional",
                borracha_bh_marca:
                  value === "penhold-classico" ? null : current.material_atual.borracha_bh_marca ?? "",
                borracha_bh_modelo:
                  value === "penhold-classico" ? null : current.material_atual.borracha_bh_modelo ?? "",
                borracha_bh_espessura:
                  value === "penhold-classico" ? null : current.material_atual.borracha_bh_espessura ?? "",
              },
            }))
          }
        />
        <AppChipRow
          label={t("fields.dominantSide")}
          options={options.dominantSides}
          value={profile.lado_dominante}
          onChange={(value) =>
            setProfile((current) => ({
              ...current,
              lado_dominante: value as AthleteProfileInput["lado_dominante"],
            }))
          }
        />
        <AppChipRow
          label={t("fields.frequency")}
          options={options.frequencies}
          value={profile.frequencia}
          onChange={(value) =>
            setProfile((current) => ({
              ...current,
              frequencia: value as AthleteProfileInput["frequencia"],
            }))
          }
        />
        <AppChipRow
          label={t("fields.strengths")}
          options={options.strengths}
          value={profile.pontos_fortes}
          onChange={(value) => setProfile((current) => ({ ...current, pontos_fortes: value as string[] }))}
          multiple
        />
        <AppChipRow
          label={t("fields.weaknesses")}
          options={options.weaknesses}
          value={profile.pontos_fracos}
          onChange={(value) => setProfile((current) => ({ ...current, pontos_fracos: value as string[] }))}
          multiple
        />
      </AppCard>

      <AppCard title={t("sections.currentSetup")}>
        <AppAutocompleteField
          label={t("fields.bladeBrand")}
          value={profile.material_atual.lamina_marca}
          onChangeText={(value) => updateMaterialField("lamina_marca", value)}
          onSelectSuggestion={(value) =>
            selectMaterialFields({
              lamina_marca: value,
              lamina_modelo: "",
            })
          }
          options={(autocompleteOptions as SetupAutocompleteOptions).bladeBrands}
          minCharsLabel={t("autocomplete.typeMinChars")}
          noResultsLabel={t("autocomplete.noResults")}
        />
        <AppAutocompleteField
          label={t("fields.bladeModel")}
          value={profile.material_atual.lamina_modelo}
          onChangeText={(value) => updateMaterialField("lamina_modelo", value)}
          options={bladeModelOptions}
          minCharsLabel={t("autocomplete.typeMinChars")}
          noResultsLabel={t("autocomplete.noResults")}
        />

        <AppAutocompleteField
          label={t("fields.forehandRubberBrand")}
          value={profile.material_atual.borracha_fh_marca}
          onChangeText={(value) => updateMaterialField("borracha_fh_marca", value)}
          onSelectSuggestion={(value) =>
            selectMaterialFields({
              borracha_fh_marca: value,
              borracha_fh_modelo: "",
            })
          }
          options={(autocompleteOptions as SetupAutocompleteOptions).rubberBrands}
          minCharsLabel={t("autocomplete.typeMinChars")}
          noResultsLabel={t("autocomplete.noResults")}
        />
        <AppAutocompleteField
          label={t("fields.forehandRubberModel")}
          value={profile.material_atual.borracha_fh_modelo}
          onChangeText={(value) => updateMaterialField("borracha_fh_modelo", value)}
          options={forehandModelOptions}
          minCharsLabel={t("autocomplete.typeMinChars")}
          noResultsLabel={t("autocomplete.noResults")}
        />
        <Text style={styles.fieldLabel}>{t("fields.forehandRubberThickness")}</Text>
        <TextInput style={styles.input} value={profile.material_atual.borracha_fh_espessura} onChangeText={(value) => updateMaterialField("borracha_fh_espessura", value)} />

        {profile.empunhadura !== "penhold-classico" ? (
          <AppChipRow
            label={t("fields.backhandRubberType")}
            options={options.backhandTypes}
            value={profile.material_atual.borracha_bh_tipo}
            onChange={(value) => updateBackhandType(value as "convencional" | "dorso-liso")}
          />
        ) : null}

        {profile.empunhadura === "penhold-classico" || profile.material_atual.borracha_bh_tipo === "dorso-liso" ? (
          <Text style={styles.infoText}>
            {profile.empunhadura === "penhold-classico"
              ? t("profile.backhandClassicPenhold")
              : t("profile.backhandDorsoLisoHint")}
          </Text>
        ) : (
          <>
            <AppAutocompleteField
              label={t("fields.backhandRubberBrand")}
              value={profile.material_atual.borracha_bh_marca ?? ""}
              onChangeText={(value) => updateMaterialField("borracha_bh_marca", value)}
              onSelectSuggestion={(value) =>
                selectMaterialFields({
                  borracha_bh_marca: value,
                  borracha_bh_modelo: "",
                })
              }
              options={(autocompleteOptions as SetupAutocompleteOptions).rubberBrands}
              minCharsLabel={t("autocomplete.typeMinChars")}
              noResultsLabel={t("autocomplete.noResults")}
            />
            <AppAutocompleteField
              label={t("fields.backhandRubberModel")}
              value={profile.material_atual.borracha_bh_modelo ?? ""}
              onChangeText={(value) => updateMaterialField("borracha_bh_modelo", value)}
              options={backhandModelOptions}
              minCharsLabel={t("autocomplete.typeMinChars")}
              noResultsLabel={t("autocomplete.noResults")}
            />
            <Text style={styles.fieldLabel}>{t("fields.backhandRubberThickness")}</Text>
            <TextInput style={styles.input} value={profile.material_atual.borracha_bh_espessura ?? ""} onChangeText={(value) => updateMaterialField("borracha_bh_espessura", value)} />
          </>
        )}

        <Text style={styles.fieldLabel}>{t("fields.setupDuration")}</Text>
        <TextInput style={styles.input} value={profile.material_atual.tempo_setup_atual} onChangeText={(value) => updateMaterialField("tempo_setup_atual", value)} />
      </AppCard>

      <AppCard title={t("sections.history")}>
        <AppChipRow
          label={t("fields.issues")}
          options={options.issues}
          value={profile.problemas_percebidos}
          onChange={(value) => setProfile((current) => ({ ...current, problemas_percebidos: value as string[] }))}
          multiple
        />
        <AppChipRow
          label={t("fields.goal")}
          options={options.goals}
          value={profile.objetivo}
          onChange={(value) => setProfile((current) => ({ ...current, objetivo: value as AthleteProfileInput["objetivo"] }))}
        />
        <Text style={styles.fieldLabel}>{t("fields.previousMaterials")}</Text>
        <TextInput
          style={styles.input}
          value={profile.materiais_anteriores}
          onChangeText={(value) => setProfile((current) => ({ ...current, materiais_anteriores: value }))}
        />
        <Text style={styles.fieldLabel}>{t("fields.notes")}</Text>
        <TextInput
          style={[styles.input, styles.textArea]}
          multiline
          value={profile.observacoes}
          onChangeText={(value) => setProfile((current) => ({ ...current, observacoes: value }))}
        />
      </AppCard>

      {error ? <Text style={styles.errorText}>{error}</Text> : null}

      <AppPrimaryButton
        label={isLoading ? t("actions.generating") : t("actions.generate")}
        onPress={() => {
          void handleAnalyze();
        }}
        disabled={isLoading}
      />
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
  infoText: {
    color: "#6a5b49",
    fontSize: 13,
    lineHeight: 20,
    backgroundColor: "#f7ecd7",
    borderColor: "#ddc6a0",
    borderWidth: 1,
    borderRadius: 14,
    marginTop: 6,
    padding: 12,
  },
  errorText: { color: "#a52a2a", fontSize: 14, fontWeight: "700" },
});
