import { Pressable, StyleSheet, Text } from "react-native";

type AppPrimaryButtonProps = {
  label: string;
};

export function AppPrimaryButton({ label }: AppPrimaryButtonProps) {
  return (
    <Pressable style={styles.button}>
      <Text style={styles.label}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    alignItems: "center",
    backgroundColor: "#9d4a06",
    borderRadius: 18,
    paddingHorizontal: 18,
    paddingVertical: 16,
  },
  label: { color: "#fff7ee", fontSize: 15, fontWeight: "800" },
});
