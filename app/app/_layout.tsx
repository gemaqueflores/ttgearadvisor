import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { SafeAreaProvider } from "react-native-safe-area-context";

import { AppI18nProvider } from "@/src/i18n/provider";

export default function RootLayout() {
  return (
    <SafeAreaProvider>
      <AppI18nProvider>
        <StatusBar style="dark" />
        <Stack
          screenOptions={{
            headerShown: false,
            contentStyle: { backgroundColor: "#f3ecdf" },
          }}
        />
      </AppI18nProvider>
    </SafeAreaProvider>
  );
}
