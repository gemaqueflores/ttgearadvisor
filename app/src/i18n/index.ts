import i18n from "i18next";
import { initReactI18next } from "react-i18next";

import enUS from "@/src/i18n/en-US/common.json";
import ptBR from "@/src/i18n/pt-BR/common.json";

export const defaultLocale = "pt-BR";

if (!i18n.isInitialized) {
  i18n.use(initReactI18next).init({
    compatibilityJSON: "v4",
    lng: defaultLocale,
    fallbackLng: defaultLocale,
    interpolation: { escapeValue: false },
    resources: {
      "pt-BR": { common: ptBR },
      "en-US": { common: enUS },
    },
    defaultNS: "common",
  });
}

export { i18n };
