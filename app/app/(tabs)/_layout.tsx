import { Tabs } from "expo-router";
import { Ionicons } from "@expo/vector-icons";

import { useAppTranslation } from "@/src/i18n/provider";

export default function TabsLayout() {
  const { t } = useAppTranslation();

  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: "#9d4a06",
        tabBarInactiveTintColor: "#6f7c83",
        tabBarStyle: {
          backgroundColor: "#fff8ed",
          borderTopColor: "#e1d4bd",
          height: 72,
          paddingBottom: 10,
          paddingTop: 8,
        },
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: t("navigation.profile"),
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="clipboard-outline" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="result"
        options={{
          title: t("navigation.result"),
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="sparkles-outline" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="settings"
        options={{
          title: t("navigation.settings"),
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="options-outline" size={size} color={color} />
          ),
        }}
      />
    </Tabs>
  );
}
