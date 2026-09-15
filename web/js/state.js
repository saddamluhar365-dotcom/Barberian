const CHAT_KEY = "barberian_chats_v3";
const SETTINGS_KEY = "barberian_settings_v3";
const DEFAULT_SETTINGS = { focusMode: false, enterSend: true, localHistory: true, blackMode: true };

let chats = read(CHAT_KEY, []);
let settings = { ...DEFAULT_SETTINGS, ...read(SETTINGS_KEY, {}) };
let activeId = null;

function read(key, fallback) {
  try { return JSON.parse(localStorage.getItem(key) || "null") ?? fallback; } catch { return fallback; }
}
function write(key, value) {
  try { localStorage.setItem(key, JSON.stringify(value)); return true; } catch { return false; }
}
export function uid() { return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2,9)}`; }
export function getChats() { return chats; }
export function getActiveId() { return activeId; }
export function getActiveChat() { return chats.find((chat) => chat.id === activeId) || null; }
export function setActiveId(id) { activeId = id; }
export function getSettings() { return settings; }
export function updateSettings(patch) { settings = { ...settings, ...patch }; write(SETTINGS_KEY, settings); return settings; }
export function persistChats() { if (settings.localHistory) write(CHAT_KEY, chats.slice(-60)); }
export function createChat(title = "New chat") {
  const now = Date.now();
  const chat = { id: uid(), title: title.slice(0, 70) || "New chat", messages: [], createdAt: now, updatedAt: now };
  chats.push(chat); activeId = chat.id; persistChats(); return chat;
}
export function ensureActiveChat() { return getActiveChat() || createChat(); }
export function addMessage(role, content) {
  const chat = ensureActiveChat();
  chat.messages.push({ id: uid(), role, content: String(content ?? ""), createdAt: Date.now() });
  chat.updatedAt = Date.now();
  if (role === "user" && chat.messages.length === 1) chat.title = String(content).trim().slice(0, 70) || "New chat";
  persistChats(); return chat;
}
export function replaceMessages(messages) { const chat = ensureActiveChat(); chat.messages = messages; chat.updatedAt = Date.now(); persistChats(); }
export function clearChats() { chats = []; activeId = null; try { localStorage.removeItem(CHAT_KEY); } catch {} }
export function clearSettingsHistory() { clearChats(); try { localStorage.removeItem(SETTINGS_KEY); } catch {} settings = { ...DEFAULT_SETTINGS }; }
