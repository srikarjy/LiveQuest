// list-models.js
require('dotenv').config();
const { Anthropic } = require('@anthropic-ai/sdk');

async function listModels() {
  const a = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });
  try {
    const res = await a.models.list();
    console.log('Full response:', JSON.stringify(res, null, 2));
  } catch (err) {
    console.error('Error listing models:', err);
  }
}

listModels(); 