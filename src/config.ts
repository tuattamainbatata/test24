export interface OpenRouterConfig {
  apiKey: string;
  baseURL?: string;
}

export function getOpenRouterConfig(): OpenRouterConfig {
  const apiKey = process.env.OPENROUTER_API_KEY;

  if (!apiKey) {
    throw new Error(
      'OPENROUTER_API_KEY environment variable is not set. ' +
      'Please set it before using OpenRouter functionality.'
    );
  }

  return {
    apiKey,
    baseURL: process.env.OPENROUTER_BASE_URL || 'https://openrouter.ai/api/v1',
  };
}
