import { streamWithReasoningTokens, nonStreamWithReasoningTokens } from '../src/reasoning-tokens.js';

async function demonstrateStreamingWithReasoningTokens() {
  console.log('=== Streaming Example with Reasoning Tokens ===\n');

  try {
    const result = await streamWithReasoningTokens(
      "How many r's are in the word 'strawberry'?"
    );

    console.log('\n\n--- Token Usage ---');
    console.log(`Prompt tokens: ${result.usage.promptTokens}`);
    console.log(`Completion tokens: ${result.usage.completionTokens}`);
    console.log(`Reasoning tokens: ${result.usage.reasoningTokens}`);
    console.log(`Total tokens: ${result.usage.totalTokens}`);
  } catch (error) {
    console.error('Error in streaming example:', error);
  }
}

async function demonstrateNonStreamingWithReasoningTokens() {
  console.log('\n=== Non-Streaming Example with Reasoning Tokens ===\n');

  try {
    const result = await nonStreamWithReasoningTokens(
      'What is the capital of France?'
    );

    console.log('Response:', result.content);
    console.log('\n--- Token Usage ---');
    console.log(`Prompt tokens: ${result.usage.promptTokens}`);
    console.log(`Completion tokens: ${result.usage.completionTokens}`);
    console.log(`Reasoning tokens: ${result.usage.reasoningTokens}`);
    console.log(`Total tokens: ${result.usage.totalTokens}`);
  } catch (error) {
    console.error('Error in non-streaming example:', error);
  }
}

async function main() {
  console.log('OpenRouter Reasoning Tokens Examples\n');
  console.log('Make sure OPENROUTER_API_KEY environment variable is set.\n');

  await demonstrateStreamingWithReasoningTokens();
  await demonstrateNonStreamingWithReasoningTokens();
}

main().catch(console.error);
