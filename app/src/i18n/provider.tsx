import { PropsWithChildren, useEffect } from "react";
import { I18nextProvider, useTranslation } from "react-i18next";
import { getLocales } from "expo-localization";

import { defaultLocale, i18n } from "@/src/i18n";

export function AppI18nProvider({ children }: PropsWithChildren) {
  useEffect(() => {
    const deviceLocale = getLocales()[0]?.languageTag ?? defaultLocale;
    const nextLocale = deviceLocale.startsWith("pt") ? "pt-BR" : "en-US";

    if (i18n.language !== nextLocale) {
      void i18n.changeLanguage(nextLocale);
    }
  }, []);

  return <I18nextProvider i18n={i18n}>{children}</I18nextProvider>;
}

export function useAppTranslation() {
  return useTranslation();
}
