import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { SafeAreaProvider } from "react-native-safe-area-context";

import { AppI18nProvider } from "@/src/i18n/provider";
import { AdvisorProvider } from "@/src/state/advisor-provider";

export default function RootLayout() {
  return (
    <SafeAreaProvider>
      <AppI18nProvider>
        <AdvisorProvider>
          <StatusBar style="dark" />
          <Stack
            screenOptions={{
              headerShown: false,
              contentStyle: { backgroundColor: "#f3ecdf" },
            }}
          />
        </AdvisorProvider>
      </AppI18nProvider>
    </SafeAreaProvider>
  );
}
