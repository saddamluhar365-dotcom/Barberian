import { getChats, getActiveId, setActiveId, clearChats, createChat } from "./state.js";

export function renderHistory(container, query = "", onSelect) {
  const needle = query.trim().toLowerCase();
  const chats = getChats().slice().sort((a,b) => b.updatedAt - a.updatedAt).filter((chat) => !needle || chat.title.toLowerCase().includes(needle) || chat.messages.some((m) => m.content.toLowerCase().includes(needle)));
  container.innerHTML = "<div class=\"history-title\">Recent</div>";
  if (!chats.length) { container.insertAdjacentHTML("beforeend", `<div class="empty">No chats found.</div>`); return; }
  for (const chat of chats) {
    const button = document.createElement("button"); button.type = "button"; button.className = `history-item${chat.id === getActiveId() ? " active" : ""}`;
    button.dataset.chatId = chat.id; button.setAttribute("aria-label", `Open chat ${chat.title}`); button.innerHTML = `<span class="history-dot"></span><span class="history-label"></span>`;
    button.querySelector(".history-label").textContent = chat.title;
    button.addEventListener("click", () => { setActiveId(chat.id); onSelect(chat); renderHistory(container, query, onSelect); });
    container.appendChild(button);
  }
}

export function newChat(onSelect, container) {
  const chat = createChat(); renderHistory(container, "", onSelect); onSelect(chat); return chat;
}

export function clearHistory(onSelect, container) {
  clearChats(); const chat = createChat(); renderHistory(container, "", onSelect); onSelect(chat);
}
