export function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>\"']/g, (char) => ({ "&":"&amp;", "<":"&lt;", ">":"&gt;", "\"":"&quot;", "'":"&#39;" }[char]));
}

function safeUrl(value) {
  try {
    const url = new URL(value, window.location.origin);
    return ["http:", "https:"].includes(url.protocol) ? url.href : null;
  } catch { return null; }
}

function inline(text) {
  let out = text;
  out = out.replace(/`([^`\n]+)`/g, "<code>$1</code>");
  out = out.replace(/\*\*([^*\n]+)\*\*/g, "<strong>$1</strong>");
  out = out.replace(/__([^_\n]+)__/g, "<strong>$1</strong>");
  out = out.replace(/(^|[^*])\*([^*\n]+)\*(?!\*)/g, "$1<em>$2</em>");
  out = out.replace(/(^|[^_])_([^_\n]+)_(?!_)/g, "$1<em>$2</em>");
  out = out.replace(/\[([^\]\n]+)\]\(([^)\s]+)\)/g, (match, label, href) => {
    const safe = safeUrl(href);
    return safe ? `<a href="${escapeHtml(safe)}" target="_blank" rel="noopener noreferrer">${label}</a>` : label;
  });
  return out;
}

export function renderMarkdown(source) {
  const escaped = escapeHtml(source);
  const blocks = escaped.split(/```/);
  let html = "";
  blocks.forEach((block, index) => {
    if (index % 2 === 1) {
      const lines = block.replace(/^\w+\n/, "");
      html += `<div class="code-wrap"><button class="code-copy" type="button" data-copy-code="${escapeHtml(lines)}">Copy</button><pre><code>${lines}</code></pre></div>`;
      return;
    }
    const lines = block.split(/\n/);
    let list = null;
    for (const line of lines) {
      if (/^\s*[-*]\s+/.test(line)) {
        if (list !== "ul") { if (list) html += `</${list}>`; html += "<ul>"; list = "ul"; }
        html += `<li>${inline(line.replace(/^\s*[-*]\s+/, ""))}</li>`;
      } else if (/^\s*\d+\.\s+/.test(line)) {
        if (list !== "ol") { if (list) html += `</${list}>`; html += "<ol>"; list = "ol"; }
        html += `<li>${inline(line.replace(/^\s*\d+\.\s+/, ""))}</li>`;
      } else {
        if (list) { html += `</${list}>`; list = null; }
        if (/^###\s+/.test(line)) html += `<h3>${inline(line.slice(4))}</h3>`;
        else if (/^##\s+/.test(line)) html += `<h2>${inline(line.slice(3))}</h2>`;
        else if (/^#\s+/.test(line)) html += `<h1>${inline(line.slice(2))}</h1>`;
        else if (/^>\s?/.test(line)) html += `<blockquote>${inline(line.replace(/^>\s?/, ""))}</blockquote>`;
        else if (line.trim()) html += `<p>${inline(line)}</p>`;
      }
    }
    if (list) html += `</${list}>`;
  });
  return html || "<p></p>";
}
