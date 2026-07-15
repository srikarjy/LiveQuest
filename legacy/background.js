chrome.action.onClicked.addListener(async (tab) => {
  try {
    const response = await chrome.tabs.sendMessage(tab.id, { type: 'GET_CONTEXT' });
    await generateAndStore(response.title, response.selection);
  } catch (error) {
    console.error('Background click error:', error);
  }
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'REGENERATE') {
    handleRegenerate(sendResponse);
    return true; // Keep port alive for async
  }
});

async function handleRegenerate(sendResponse) {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const response = await chrome.tabs.sendMessage(tab.id, { type: 'GET_CONTEXT' });
    const newPrompt = await generateAndStore(response.title, response.selection);
    sendResponse({ success: true, prompt: newPrompt });
  } catch (error) {
    console.error('Regenerate error:', error);
    sendResponse({ success: false, error: error.message });
  }
}

async function generateAndStore(title, selection) {
  try {
    const apiResponse = await fetch('http://localhost:3001/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, selection })
    });
    const data = await apiResponse.json();
    const prompt = data.prompt;
    await chrome.storage.local.set({ prompt, timestamp: Date.now() });
    await navigator.clipboard.writeText(prompt);
    chrome.notifications.create({
      type: 'basic',
      iconUrl: 'icons/icon48.png',
      title: 'DeepPromptor',
      message: '✅ Prompt generated & copied!'
    });
    return prompt;
  } catch (error) {
    console.error('Generate error:', error);
    throw error;
  }
} 