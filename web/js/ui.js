import { getSettings, updateSettings, clearSettingsHistory } from "./state.js";
import { copyText, sendCurrent, stopCurrent } from "./chat.js";
import { renderHistory } from "./history.js";

export function initUI({ elements, onRender, onHistoryChange, notify }) {
  const { sidebar, overlay, panel, input, fileInput, attachment, attachmentName, messages, history, title } = elements;
  const setBusy = (busy) => {
    elements.send.disabled = busy || !input.value.trim();
    elements.send.classList.toggle("hidden", busy);
    elements.stop.classList.toggle("hidden", !busy);
  };
  const closeDrawer = () => { sidebar.classList.remove("open"); overlay.classList.add("hidden"); overlay.setAttribute("aria-hidden", "true"); };
  const openSettings = () => { panel.classList.remove("hidden"); panel.setAttribute("aria-hidden", "false"); closeDrawer(); };
  const closeSettings = () => { panel.classList.add("hidden"); panel.setAttribute("aria-hidden", "true"); };
  const syncSettings = () => {
    const s = getSettings();
    elements.blackMode.checked = s.blackMode; elements.focusMode.checked = s.focusMode; elements.enterSend.checked = s.enterSend; elements.localHistory.checked = s.localHistory;
    elements.app.classList.toggle("focus-mode", s.focusMode); document.body.classList.toggle("non-black", !s.blackMode);
  };
  const selectChat = (chat) => { title.textContent = chat.title; closeSettings(); onRender(); onHistoryChange(); };
  const refreshHistory = () => renderHistory(history, elements.searchInput.value, selectChat);
  elements.searchInput.addEventListener("input", refreshHistory);
  elements.composer.addEventListener("submit", (event) => { event.preventDefault(); sendCurrent(input, messages, setBusy, notify).then(refreshHistory); });
  input.addEventListener("input", () => { input.style.height = "auto"; input.style.height = `${Math.min(input.scrollHeight, 180)}px`; setBusy(false); });
  input.addEventListener("keydown", (event) => { if (event.key === "Enter" && !event.shiftKey && getSettings().enterSend) { event.preventDefault(); elements.composer.requestSubmit(); } });
  fileInput.addEventListener("change", () => { const file = fileInput.files?.[0]; if (!file) return; attachmentName.textContent = `${file.name} · local only`; attachment.classList.remove("hidden"); });
  elements.app.addEventListener("click", (event) => {
    const quick = event.target.closest("[data-prompt]"); if (quick) { input.value = quick.dataset.prompt || ""; input.focus(); setBusy(false); return; }
    const code = event.target.closest("[data-copy-code]"); if (code) { copyText(code.dataset.copyCode || "", notify); return; }
    const msg = event.target.closest("[data-copy-message]"); if (msg) { copyText(msg.dataset.copyMessage || "", notify); return; }
    const action = event.target.closest("[data-action]")?.dataset.action;
    if (!action) return;
    if (action === "new-chat") { onHistoryChange("new"); }
    else if (action === "search") { elements.searchInput.focus(); }
    else if (action === "settings") openSettings();
    else if (action === "close-settings") closeSettings();
    else if (action === "mobile-menu") { sidebar.classList.add("open"); overlay.classList.remove("hidden"); overlay.setAttribute("aria-hidden", "false"); }
    else if (action === "desktop-toggle") { sidebar.classList.toggle("collapsed"); }
    else if (action === "focus-toggle") { updateSettings({ focusMode: !getSettings().focusMode }); syncSettings(); }
    else if (action === "theme-toggle") { notify("AMOLED black mode is active"); }
    else if (action === "attach") fileInput.click();
    else if (action === "remove-attachment") { fileInput.value = ""; attachment.classList.add("hidden"); attachmentName.textContent = ""; }
    else if (action === "send") elements.composer.requestSubmit();
    else if (action === "stop") stopCurrent(setBusy, notify);
    else if (action === "clear-chat") onHistoryChange("clear");
    else if (action === "clear-settings-history") { clearSettingsHistory(); closeSettings(); onRender(); refreshHistory(); notify("Local history deleted"); }
  });
  overlay.addEventListener("click", closeDrawer);
  elements.blackMode.addEventListener("change", () => { updateSettings({ blackMode: elements.blackMode.checked }); syncSettings(); });
  elements.focusMode.addEventListener("change", () => { updateSettings({ focusMode: elements.focusMode.checked }); syncSettings(); });
  elements.enterSend.addEventListener("change", () => updateSettings({ enterSend: elements.enterSend.checked }));
  elements.localHistory.addEventListener("change", () => updateSettings({ localHistory: elements.localHistory.checked }));
  syncSettings(); refreshHistory();
  return { setBusy, refreshHistory, selectChat, syncSettings };
}
