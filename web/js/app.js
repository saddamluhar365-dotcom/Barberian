import { health } from "./api.js";
import { ensureActiveChat, createChat, getActiveChat, clearChats } from "./state.js";
import { renderConversation } from "./chat.js";
import { renderHistory } from "./history.js";
import { initUI } from "./ui.js";

const $ = (id) => document.getElementById(id);
const elements = {
  app: $("app"), sidebar: $("sidebar"), overlay: $("overlay"), panel: $("panel"), chat: $("chat"), messages: $("messages"), history: $("history"), title: $("title"),
  searchInput: $("searchInput"), composer: $("composer"), input: $("input"), send: document.querySelector('[data-action="send"]'), stop: document.querySelector('[data-action="stop"]'),
  fileInput: $("fileInput"), attachment: $("attachment"), attachmentName: $("attachmentName"), blackMode: $("blackMode"), focusMode: $("focusMode"), enterSend: $("enterSend"), localHistory: $("localHistory"),
};

function notify(message) {
  const toast = $("toast"); toast.textContent = message; toast.classList.add("show"); clearTimeout(notify.timer); notify.timer = setTimeout(() => toast.classList.remove("show"), 1800);
}

function render() {
  const chat = getActiveChat();
  elements.title.textContent = chat?.title || "New chat";
  renderConversation(elements.messages, chat);
}

function refreshHistory() {
  renderHistory(elements.history, elements.searchInput.value, (chat) => { render(); elements.title.textContent = chat.title; });
}

function handleHistory(action) {
  if (action === "new") createChat();
  else if (action === "clear") { clearChats(); createChat(); }
  render(); refreshHistory();
}

async function checkHealth() {
  const status = $("status");
  try { const result = await health(); status.classList.add("online"); status.innerHTML = '<span class="status-dot"></span><span>Online</span>'; status.title = result.status || "healthy"; }
  catch { status.classList.remove("online"); status.innerHTML = '<span class="status-dot"></span><span>Offline</span>'; }
}

ensureActiveChat();
initUI({ elements, onRender: render, onHistoryChange: handleHistory, notify });
render();
checkHealth();
setInterval(checkHealth, 30000);
