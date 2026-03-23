import Constants from "expo-constants";

import type { AnalyzeResponse, AthleteProfileInput } from "@/src/types/api";

function resolveApiBaseUrl() {
  if (process.env.EXPO_PUBLIC_API_URL) {
    return process.env.EXPO_PUBLIC_API_URL;
  }

  const hostUri =
    Constants.expoConfig?.hostUri ??
    Constants.expoGoConfig?.hostUri ??
    Constants.manifest2?.extra?.expoClient?.hostUri;

  if (hostUri) {
    const [host] = hostUri.split(":");
    return `http://${host}:8000`;
  }

  return "http://127.0.0.1:8000";
}

const apiBaseUrl = resolveApiBaseUrl();

export async function analyzeProfile(profile: AthleteProfileInput): Promise<AnalyzeResponse> {
  const response = await fetch(`${apiBaseUrl}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(profile),
  });

  if (!response.ok) {
    const rawBody = await response.text();

    try {
      const parsed = JSON.parse(rawBody) as { detail?: string; error?: string };
      const message = parsed.detail ?? parsed.error;
      throw new Error(message || `Falha na analise (${response.status})`);
    } catch {
      throw new Error(rawBody || `Falha na analise (${response.status})`);
    }
  }

  return (await response.json()) as AnalyzeResponse;
}
