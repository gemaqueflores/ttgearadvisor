import { ScrollView, StyleSheet, Text, View } from "react-native";
import { Pressable } from "react-native";

type AppChipRowProps = {
  label: string;
  options: Array<{ label: string; value: string }>;
  value: string | string[];
  onChange: (value: string | string[]) => void;
  multiple?: boolean;
};

export function AppChipRow({
  label,
  options,
  value,
  onChange,
  multiple = false,
}: AppChipRowProps) {
  const selectedValues = Array.isArray(value) ? value : [value];

  function toggleOption(optionValue: string) {
    if (!multiple) {
      onChange(optionValue);
      return;
    }

    const nextValues = selectedValues.includes(optionValue)
      ? selectedValues.filter((item) => item !== optionValue)
      : [...selectedValues, optionValue];

    onChange(nextValues);
  }

  return (
    <View style={styles.wrapper}>
      <Text style={styles.label}>{label}</Text>
      <ScrollView horizontal showsHorizontalScrollIndicator={false}>
        <View style={styles.row}>
          {options.map((option) => (
            <Pressable
              key={option.value}
              style={[
                styles.chip,
                selectedValues.includes(option.value) && styles.chipSelected,
              ]}
              onPress={() => toggleOption(option.value)}
            >
              <Text
                style={[
                  styles.chipText,
                  selectedValues.includes(option.value) && styles.chipTextSelected,
                ]}
              >
                {option.label}
              </Text>
            </Pressable>
          ))}
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: { gap: 8 },
  label: { color: "#22343f", fontSize: 14, fontWeight: "700" },
  row: { flexDirection: "row", gap: 10 },
  chip: {
    backgroundColor: "#f6e5d2",
    borderColor: "#dfc4a5",
    borderWidth: 1,
    borderRadius: 999,
    paddingHorizontal: 14,
    paddingVertical: 9,
  },
  chipSelected: {
    backgroundColor: "#9d4a06",
    borderColor: "#9d4a06",
  },
  chipText: { color: "#8c4307", fontSize: 13, fontWeight: "700" },
  chipTextSelected: { color: "#fff7ee" },
});
