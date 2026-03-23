import {
  createContext,
  PropsWithChildren,
  useContext,
  useState,
} from "react";

import { analyzeProfile } from "@/src/lib/api";
import type { AnalyzeResponse, AthleteProfileInput } from "@/src/types/api";

type AdvisorContextValue = {
  isLoading: boolean;
  error: string | null;
  result: AnalyzeResponse | null;
  profile: AthleteProfileInput | null;
  analyze: (profile: AthleteProfileInput) => Promise<AnalyzeResponse>;
  setResult: (result: AnalyzeResponse | null) => void;
};

const AdvisorContext = createContext<AdvisorContextValue | null>(null);

export function AdvisorProvider({ children }: PropsWithChildren) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [profile, setProfile] = useState<AthleteProfileInput | null>(null);

  async function analyze(nextProfile: AthleteProfileInput) {
    setIsLoading(true);
    setError(null);
    setProfile(nextProfile);

    try {
      const nextResult = await analyzeProfile(nextProfile);
      setResult(nextResult);
      return nextResult;
    } catch (caughtError) {
      const message =
        caughtError instanceof Error ? caughtError.message : "Falha inesperada ao gerar a analise.";
      setError(message);
      throw caughtError;
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <AdvisorContext.Provider
      value={{ isLoading, error, result, profile, analyze, setResult }}
    >
      {children}
    </AdvisorContext.Provider>
  );
}

export function useAdvisor() {
  const context = useContext(AdvisorContext);
  if (!context) {
    throw new Error("useAdvisor precisa ser usado dentro de AdvisorProvider.");
  }
  return context;
}
