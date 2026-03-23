import { Pressable, StyleSheet, Text } from "react-native";

type AppPrimaryButtonProps = {
  label: string;
  onPress?: () => void;
  disabled?: boolean;
};

export function AppPrimaryButton({ label, onPress, disabled = false }: AppPrimaryButtonProps) {
  return (
    <Pressable style={[styles.button, disabled && styles.buttonDisabled]} onPress={onPress} disabled={disabled}>
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
  buttonDisabled: { opacity: 0.55 },
  label: { color: "#fff7ee", fontSize: 15, fontWeight: "800" },
});
