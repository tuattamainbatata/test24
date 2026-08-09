// Stream a chat completion from OpenRouter, including reasoning token usage.
//
// Usage:
//   export OPENROUTER_API_KEY="sk-or-..."
//   node scripts/openrouter_streaming.mjs "your prompt here"
import { OpenRouter } from "@openrouter/sdk";

const apiKey = process.env.OPENROUTER_API_KEY;
if (!apiKey) {
  console.error("Set the OPENROUTER_API_KEY environment variable before running this script.");
  process.exit(1);
}

const prompt = process.argv.slice(2).join(" ") || "How many r's are in the word 'strawberry'?";

const openrouter = new OpenRouter({ apiKey });

const stream = await openrouter.chat.send({
  chatRequest: {
    model: "nvidia/nemotron-3-ultra-550b-a55b:free",
    messages: [{ role: "user", content: prompt }],
    stream: true
  }
});

let response = "";
for await (const chunk of stream) {
  const content = chunk.choices[0]?.delta?.content;
  if (content) {
    response += content;
    process.stdout.write(content);
  }

  if (chunk.usage) {
    console.log("\nReasoning tokens:", chunk.usage.completionTokensDetails?.reasoningTokens);
  }
}
