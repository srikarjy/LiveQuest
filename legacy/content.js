// Listen for messages from the background or popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'GET_CONTEXT') {
    const title = document.title;
    const selection = window.getSelection().toString();
    sendResponse({ title, selection });
  }
  // No need to return true; response is synchronous
}); 