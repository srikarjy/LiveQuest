// popup.js
document.addEventListener('DOMContentLoaded', async () => {
  await loadAndDisplayPrompt();
  document.getElementById('copyBtn').addEventListener('click', handleCopy);
  document.getElementById('regenBtn').addEventListener('click', handleRegenerate);
});

async function loadAndDisplayPrompt() {
  try {
    const result = await chrome.storage.local.get(['prompt']);
    const promptText = result.prompt || 'No prompt generated yet';
    document.getElementById('prompt').value = promptText;
  } catch (error) {
    console.error('Load prompt error:', error);
    document.getElementById('prompt').value = 'Error loading prompt';
  }
}

async function handleCopy() {
  try {
    const result = await chrome.storage.local.get(['prompt']);
    const prompt = result.prompt;
    if (!prompt) {
      console.error('No prompt to copy');
      return;
    }
    await navigator.clipboard.writeText(prompt);
    const btn = document.getElementById('copyBtn');
    const originalText = btn.textContent;
    btn.textContent = 'Copied!';
    setTimeout(() => btn.textContent = originalText, 1000);
  } catch (error) {
    console.error('Copy error:', error);
  }
}

async function handleRegenerate() {
  try {
    const btn = document.getElementById('regenBtn');
    btn.disabled = true;
    btn.textContent = 'Generating...';
    const response = await new Promise((resolve, reject) => {
      chrome.runtime.sendMessage({ type: 'REGENERATE' }, (response) => {
        if (chrome.runtime.lastError) {
          reject(new Error(chrome.runtime.lastError.message));
        } else {
          resolve(response);
        }
      });
    });
    if (response.success) {
      await loadAndDisplayPrompt();
    } else {
      console.error('Regenerate failed:', response.error);
    }
  } catch (error) {
    console.error('Regenerate error:', error);
  } finally {
    const btn = document.getElementById('regenBtn');
    btn.disabled = false;
    btn.textContent = 'Regenerate';
  }
} 