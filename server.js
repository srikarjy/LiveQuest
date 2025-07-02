require('dotenv').config();
require('dotenv').config();
console.log('🔑 Loaded ANTHROPIC_API_KEY:', process.env.ANTHROPIC_API_KEY?.slice(0,8) + '…');

// Catch any uncaught exceptions
process.on('uncaughtException', (err, origin) => {
  console.error('❌ Uncaught Exception:', err, '\nOrigin:', origin);
});

// Catch unhandled promise rejections
process.on('unhandledRejection', (reason, promise) => {
  console.error('❌ Unhandled Rejection at:', promise, '\nReason:', reason);
});

const express = require('express');
const cors = require('cors');
const { Anthropic } = require('@anthropic-ai/sdk');

const app = express();
app.use(cors());
app.use(express.json());
app.get('/health', (req, res) => res.json({ status: 'ok' }));

const anthropic = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY
});

app.post('/api/generate', async (req, res) => {
  try {
    console.log('Request body:', req.body); // Debug the incoming request
    const { title, selection } = req.body;
    const systemMessage = `You are a helpful assistant.`;
    const messages = [
      { role: 'user', content: `Title: ${title}, Selection: ${selection}` }
    ];
    console.log('Messages being sent:', messages); // Debug the messages
    console.log('System message:', systemMessage); // Debug system message
    const response = await anthropic.messages.create({
      model: 'claude-sonnet-4-20250514', // Try this model name
      max_tokens: 150,
      temperature: 0.7,
      system: systemMessage,
      messages: messages
    });
    console.log('Anthropic response:', response); // Debug the response
    const generatedText = response.content[0].text.trim();
    res.json({ prompt: generatedText });
  } catch (error) {
    console.error('Detailed error:', error); // More detailed error logging
    console.error('Error message:', error.message);
    console.error('Error stack:', error.stack);
    res.status(500).json({ 
      error: 'Claude generation failed',
      details: error.message // Include error details in development
    });
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`)); 