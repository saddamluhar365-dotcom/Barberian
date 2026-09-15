import { chat as sendChat, events } from "./api.js";
import { addMessage, ensureActiveChat, getActiveChat, persistChats } from "./state.js";
import { escapeHtml, renderMarkdown } from "./markdown.js";

let controller = null;
let busy = false;

const icon = (role) => role === "user" ? "YOU" : "B";

export function isBusy() { return busy; }

export function renderConversation(messagesEl, chat = getActiveChat()) {
  messagesEl.innerHTML = "";
  if (!chat || !chat.messages.length) {
    messagesEl.innerHTML = `<div class="welcome"><div class="welcome-inner"><div class="welcome-mark">B</div><h1>What can I help you build?</h1><p>Ask Barberian to research, reason, write, code, analyze or plan. Your local conversation history stays in this browser.</p><div class="quick-grid"><button class="quick" data-prompt="Research a topic and give me a concise verified summary."><span class="quick-icon">⌕</span><strong>Research</strong><small>Find and verify useful information.</small></button><button class="quick" data-prompt="Create a production-ready implementation plan for my project."><span class="quick-icon">◆</span><strong>Plan</strong><small>Turn an idea into clear executable steps.</small></button><button class="quick" data-prompt="Review this idea for risks, bugs and improvements."><span class="quick-icon">✓</span><strong>Review</strong><small>Find problems before they ship.</small></button><button class="quick" data-prompt="Write a clean professional draft for this request."><span class="quick-icon">✎</span><strong>Create</strong><small>Produce a polished first draft.</small></button></div></div></div>`;
    return;
  }
  for (const message of chat.messages) renderMessage(messagesEl, message);
  messagesEl.closest(".chat")?.scrollTo({ top: messagesEl.scrollHeight, behavior: "smooth" });
}

function renderMessage(container, message) {
  const row = document.createElement("article");
  row.className = `message ${message.role}`;
  const content = message.role === "assistant" ? renderMarkdown(message.content) : `<p>${escapeHtml(message.content).replace(/\n/g, "<br>")}</p>`;
  row.innerHTML = `<div class="avatar">${icon(message.role)}</div><div class="message-body"><div class="bubble">${content}</div><div class="meta"><span>${message.role === "user" ? "You" : "Barberian"}</span><button class="copy" type="button" data-copy-message="${escapeHtml(message.content)}">Copy</button></div></div>`;
  container.appendChild(row);
}

function resultText(result) {
  if (!result) return "";
  if (typeof result === "string") return result;
  return result.message ?? result.response ?? result.output ?? result.text ?? result.content ?? "";
}

export async function sendCurrent(input, messagesEl, setBusy, notify) {
  const text = input.value.trim();
  if (!text || busy) return;
  busy = true; controller = new AbortController(); setBusy(true);
  addMessage("user", text); input.value = ""; input.style.height = ""; renderConversation(messagesEl);
  const typing = document.createElement("article"); typing.className = "message assistant pending"; typing.innerHTML = `<div class="avatar">B</div><div class="message-body"><div class="bubble"><div class="typing"><i></i><i></i><i></i></div></div></div>`; messagesEl.appendChild(typing); messagesEl.closest(".chat")?.scrollTo({ top: messagesEl.scrollHeight, behavior: "smooth" });
  try {
    const result = await sendChat(text, controller.signal);
    typing.remove();
    const answer = resultText(result) || "I received the request but no response content was returned.";
    addMessage("assistant", answer); renderConversation(messagesEl);
    if (result?.run_id) {
      try { await events(result.run_id); } catch { /* replay is informational */ }
    }
  } catch (error) {
    typing.remove();
    if (error?.name === "AbortError") notify("Response stopped");
    else notify(error instanceof Error ? error.message : "Unable to reach Barberian");
    renderConversation(messagesEl);
  } finally {
    busy = false; controller = null; setBusy(false); persistChats();
  }
}

export function stopCurrent(setBusy, notify) {
  if (!controller) return;
  controller.abort(); controller = null; busy = false; setBusy(false); notify("Response stopped");
}

export function copyText(text, notify) {
  navigator.clipboard?.writeText(text).then(() => notify("Copied")).catch(() => notify("Copy unavailable"));
}

export function ensureChat() { return ensureActiveChat(); }
