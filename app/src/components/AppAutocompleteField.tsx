import { useMemo, useState } from "react";
import { Pressable, StyleSheet, Text, TextInput, View } from "react-native";

type AppAutocompleteFieldProps = {
  label: string;
  value: string;
  onChangeText: (value: string) => void;
  onSelectSuggestion?: (value: string) => void;
  options: string[];
  minCharsLabel: string;
  noResultsLabel: string;
  minChars?: number;
};

function normalizeForSearch(value: string) {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();
}

export function AppAutocompleteField({
  label,
  value,
  onChangeText,
  onSelectSuggestion,
  options,
  minCharsLabel,
  noResultsLabel,
  minChars = 3,
}: AppAutocompleteFieldProps) {
  const [isFocused, setIsFocused] = useState(false);
  const normalizedQuery = normalizeForSearch(value);

  const suggestions = useMemo(() => {
    if (normalizedQuery.length < minChars) {
      return [];
    }

    return options
      .filter((option) => normalizeForSearch(option).includes(normalizedQuery))
      .slice(0, 8);
  }, [minChars, normalizedQuery, options]);

  const showHint = isFocused && normalizedQuery.length > 0 && normalizedQuery.length < minChars;
  const showNoResults = isFocused && normalizedQuery.length >= minChars && suggestions.length === 0;
  const showSuggestions = isFocused && suggestions.length > 0;

  return (
    <View style={styles.wrapper}>
      <Text style={styles.label}>{label}</Text>
      <TextInput
        style={styles.input}
        value={value}
        onChangeText={onChangeText}
        onFocus={() => setIsFocused(true)}
        onBlur={() => {
          setTimeout(() => setIsFocused(false), 120);
        }}
        autoCapitalize="words"
        autoCorrect={false}
      />

      {showHint ? <Text style={styles.helper}>{minCharsLabel}</Text> : null}
      {showNoResults ? <Text style={styles.helper}>{noResultsLabel}</Text> : null}

      {showSuggestions ? (
        <View style={styles.dropdown}>
          {suggestions.map((suggestion) => (
            <Pressable
              key={`${label}-${suggestion}`}
              style={styles.option}
              onPress={() => {
                onSelectSuggestion?.(suggestion);
                onChangeText(suggestion);
                setIsFocused(false);
              }}
            >
              <Text style={styles.optionText}>{suggestion}</Text>
            </Pressable>
          ))}
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: { gap: 8 },
  label: {
    color: "#22343f",
    fontSize: 14,
    fontWeight: "700",
    marginTop: 2,
  },
  input: {
    backgroundColor: "#fffaf1",
    borderColor: "#dfd2bf",
    borderRadius: 16,
    borderWidth: 1,
    color: "#22343f",
    paddingHorizontal: 14,
    paddingVertical: 12,
  },
  helper: {
    color: "#6a5b49",
    fontSize: 12,
    lineHeight: 18,
  },
  dropdown: {
    backgroundColor: "#fffdf8",
    borderColor: "#ddceb7",
    borderRadius: 16,
    borderWidth: 1,
    overflow: "hidden",
  },
  option: {
    borderBottomColor: "#efe3d1",
    borderBottomWidth: 1,
    paddingHorizontal: 14,
    paddingVertical: 12,
  },
  optionText: {
    color: "#22343f",
    fontSize: 14,
  },
});
