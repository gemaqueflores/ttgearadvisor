import { PropsWithChildren } from "react";
import { StyleSheet, Text, View } from "react-native";

type AppCardProps = PropsWithChildren<{
  title: string;
}>;

export function AppCard({ title, children }: AppCardProps) {
  return (
    <View style={styles.card}>
      <Text style={styles.title}>{title}</Text>
      <View style={styles.body}>{children}</View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: "rgba(255, 248, 237, 0.96)",
    borderColor: "#ddceb7",
    borderRadius: 24,
    borderWidth: 1,
    padding: 18,
    shadowColor: "#2d3941",
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.08,
    shadowRadius: 24,
  },
  title: { color: "#18242d", fontSize: 18, fontWeight: "800", marginBottom: 14 },
  body: { gap: 12 },
});
