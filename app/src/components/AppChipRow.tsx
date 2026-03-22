import { ScrollView, StyleSheet, Text, View } from "react-native";

type AppChipRowProps = {
  label: string;
  options: string[];
};

export function AppChipRow({ label, options }: AppChipRowProps) {
  return (
    <View style={styles.wrapper}>
      <Text style={styles.label}>{label}</Text>
      <ScrollView horizontal showsHorizontalScrollIndicator={false}>
        <View style={styles.row}>
          {options.map((option) => (
            <View key={option} style={styles.chip}>
              <Text style={styles.chipText}>{option}</Text>
            </View>
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
    borderRadius: 999,
    paddingHorizontal: 14,
    paddingVertical: 9,
  },
  chipText: { color: "#8c4307", fontSize: 13, fontWeight: "700" },
});
