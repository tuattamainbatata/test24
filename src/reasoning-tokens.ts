import { OpenRouter } from '@openrouter/sdk';
import { getOpenRouterConfig } from './config.js';

export interface ReasoningTokensUsage {
  completionTokens: number;
  reasoningTokens: number;
  promptTokens: number;
  totalTokens: number;
}

export interface ReasoningTokensResponse {
  content: string;
  usage: ReasoningTokensUsage;
}

export async function streamWithReasoningTokens(
  userMessage: string,
  model: string = 'openrouter/free'
): Promise<ReasoningTokensResponse> {
  const config = getOpenRouterConfig();
  const openrouter = new OpenRouter({ apiKey: config.apiKey });

  const stream = await openrouter.chat.send({
    chatRequest: {
      model,
      messages: [
        {
          role: 'user',
          content: userMessage,
        },
      ],
      stream: true,
    },
  });

  let content = '';
  let usage: ReasoningTokensUsage | null = null;

  for await (const chunk of stream) {
    const chunkContent = chunk.choices[0]?.delta?.content;
    if (chunkContent) {
      content += chunkContent;
      process.stdout.write(chunkContent);
    }

    // Usage information comes in the final chunk
    if (chunk.usage) {
      usage = {
        completionTokens: chunk.usage.completionTokens || 0,
        reasoningTokens: chunk.usage.completionTokensDetails?.reasoningTokens || 0,
        promptTokens: chunk.usage.promptTokens || 0,
        totalTokens: chunk.usage.totalTokens || 0,
      };
    }
  }

  if (!usage) {
    throw new Error('No usage information received from API');
  }

  return { content, usage };
}

export async function nonStreamWithReasoningTokens(
  userMessage: string,
  model: string = 'openrouter/free'
): Promise<ReasoningTokensResponse> {
  const config = getOpenRouterConfig();
  const openrouter = new OpenRouter({ apiKey: config.apiKey });

  const response = await openrouter.chat.completions.create({
    model,
    messages: [
      {
        role: 'user',
        content: userMessage,
      },
    ],
  });

  const content = response.choices[0]?.message?.content || '';
  const usage: ReasoningTokensUsage = {
    completionTokens: response.usage?.completion_tokens || 0,
    reasoningTokens: (response.usage as any)?.completion_tokens_details?.reasoning_tokens || 0,
    promptTokens: response.usage?.prompt_tokens || 0,
    totalTokens: response.usage?.total_tokens || 0,
  };

  return { content, usage };
}
