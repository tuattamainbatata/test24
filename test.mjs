import OpenAI from "openai";

const apiKey = process.env.OPENROUTER_API_KEY;
if (!apiKey) {
  console.error("Set OPENROUTER_API_KEY first (get one at https://openrouter.ai/keys).");
  process.exit(1);
}

const client = new OpenAI({
  apiKey,
  baseURL: "https://openrouter.ai/api/v1",
});

const model = process.env.OPENROUTER_MODEL || "openai/gpt-4o-mini";

const response = await client.chat.completions.create({
  model,
  messages: [{ role: "user", content: "Say hello in one short sentence." }],
});

console.log(`Model: ${model}`);
console.log(response.choices[0].message.content);
