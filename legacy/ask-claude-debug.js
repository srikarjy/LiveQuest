require('dotenv').config();
const { Anthropic } = require('@anthropic-ai/sdk');

async function askClaude() {
  const anthropic = new Anthropic({
    apiKey: process.env.ANTHROPIC_API_KEY
  });

  // Your long, detailed prompt
  const userPrompt = `
You are Claude, a world-class AI assistant and debugging expert. I'm building a Chrome extension called DeepPromptor that:

1. Uses Manifest V3, with:
   • background service worker: background.js  
   • content script: content.js (grabs document.title and any selected text)  
   • popup UI: popup.html + popup.js  

2. Talks to a local Node/Express backend on http://localhost:3001/api/generate, which calls Anthropic Claude Opus 4 via anthropic.messages.create() and returns { prompt: string }.

3. The desired workflow is:
   a. User selects text on any page.  
   b. User clicks the toolbar icon → background.js grabs context → fetches a generated prompt → writes it to chrome.storage.local.prompt → copies it to clipboard → shows a notification.  
   c. User clicks the extension icon again to open the popup, which displays the latest prompt.  
   d. Popup has "Copy" and "Regenerate" buttons.  
      – Copy should copy whatever is in the textarea.  
      – Regenerate should re-run the same fetch and update the textarea.

However, right now:
- "Copy" sometimes writes an empty string.
- "Regenerate" often returns the same stale prompt.
- Sometimes the popup just says "No prompt returned." or "Loading..."
- I'm getting errors like "The message port closed before a response was received."

Below is the relevant code:

**content.js**  
```js
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === 'GET_CONTEXT') {
    const title = document.title;
    const selection = window.getSelection().toString() || '';
    sendResponse({ title, selection });
  }
});
```

**background.js**
```js
async function generatePrompt(tab) {
  try {
    const { title, selection } = await chrome.tabs.sendMessage(tab.id, { type: 'GET_CONTEXT' });
    const resp = await fetch('http://localhost:3001/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, selection })
    });
    const { prompt } = await resp.json();
    await chrome.storage.local.set({ prompt });
    await navigator.clipboard.writeText(prompt);
    chrome.notifications.create({ /* success */ });
  } catch (err) {
    chrome.notifications.create({ /* error */ });
  }
}

chrome.action.onClicked.addListener((tab) => generatePrompt(tab));
chrome.runtime.onMessage.addListener((msg, sender) => {
  if (msg.type === 'REGENERATE') {
    chrome.tabs.query({ active: true, currentWindow: true }, ([tab]) => {
      if (tab) generatePrompt(tab);
    });
  }
});
```

**popup.html**
```html
<!DOCTYPE html>
<html>
  <body>
    <img id="spinner" src="icons/spinner.gif" />
    <textarea id="prompt"></textarea>
    <div id="controls">
      <button id="copyBtn">Copy</button>
      <button id="regenBtn">Regenerate</button>
    </div>
    <script src="popup.js"></script>
  </body>
</html>
```

**popup.js (current version)**
```js
document.addEventListener('DOMContentLoaded', () => {
  const promptEl  = document.getElementById('prompt');
  const copyBtn   = document.getElementById('copyBtn');
  const regenBtn  = document.getElementById('regenBtn');
  const spinner   = document.getElementById('spinner');
  const controls  = document.getElementById('controls');

  function setLoading(isLoading) { /* toggles spinner & disables buttons */ }

  async function loadAndMaybeGenerate() {
    setLoading(true);
    try {
      const { prompt } = await chrome.storage.local.get('prompt');
      if (prompt) {
        promptEl.value = prompt;
      } else {
        await new Promise(r => chrome.runtime.sendMessage({ type: 'REGENERATE' }, r));
        const res = await chrome.storage.local.get('prompt');
        promptEl.value = res.prompt || 'No prompt returned.';
      }
    } catch (err) {
      promptEl.value = \`Error: ${err.message}\`;
    } finally {
      setLoading(false);
    }
  }

  regenBtn.addEventListener('click', loadAndMaybeGenerate);
  copyBtn.addEventListener('click', async () => {
    await navigator.clipboard.writeText(promptEl.value);
  });

  // initial load
  promptEl.value = 'Loading...';
  loadAndMaybeGenerate();
});
```

**Manifest.json**
```jsonc
{
  "manifest_version": 3,
  "name": "DeepPromptor",
  "version": "1.0.0",
  "permissions": ["activeTab","storage","clipboardWrite","notifications"],
  "host_permissions": ["http://localhost:3001/*"],
  "background": { "service_worker": "background.js" },
  "content_scripts": [{ "matches":["<all_urls>"], "js":["content.js"] }],
  "action": { "default_popup":"popup.html" }
}
```

Questions

Why does Copy sometimes yield an empty string?

Why does Regenerate return the same stale prompt?

How should I correctly use chrome.runtime.sendMessage/sendResponse in MV3 for async flows?

Provide a unified MV3 pattern for toolbar-click vs popup-click generation & proper state management.

Supply a corrected minimal background.js + popup.js with robust error/loading states.

Please analyze each of these issues in depth and then output revised code that fixes them all.
`;

  try {
    const response = await anthropic.messages.create({
      model: 'claude-opus-4-20250514',
      system: 'You are Claude, a world-renowned debugging expert. Answer exactly as requested.',
      messages: [
        { role: 'user', content: userPrompt }
      ],
      max_tokens: 1000,
      temperature: 0.2
    });
    console.log('Claude response:\n', response.content);
  } catch (err) {
    console.error('Error asking Claude:', err);
  }
}

askClaude(); 