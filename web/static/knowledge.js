(function () {
  const logEl = document.getElementById("knowledge-chat-log");
  const inputEl = document.getElementById("knowledge-input");
  const sendBtn = document.getElementById("knowledge-send");
  const sourcesEl = document.getElementById("knowledge-sources");
  const groundingWrap = document.getElementById("know-grounding-wrap");
  const groundingEl = document.getElementById("know-grounding");
  const fileEl = document.getElementById("knowledge-file");
  const arxivBtn = document.getElementById("arxiv-fetch");
  const arxivQ = document.getElementById("arxiv-query");
  const messages = [];
  let sendLocked = false;

  function T(key) {
    if (window.PilotI18n) return window.PilotI18n.t(window.PilotI18n.get(), key);
    return key;
  }
  function setPlaceholder() {
    if (inputEl) inputEl.placeholder = T("knowInputPh");
  }
  function escapeHtml(s) {
    const d = document.createElement("div");
    d.textContent = s == null ? "" : String(s);
    return d.innerHTML;
  }
  function safeMarkdown(raw) {
    const s = raw == null ? "" : String(raw);
    if (typeof marked === "undefined" || typeof marked.parse !== "function") {
      return escapeHtml(s).replace(/\n/g, "<br>");
    }
    try {
      var out = marked.parse.length >= 2 ? marked.parse(s, { async: false }) : marked.parse(s);
      if (out && typeof out.then === "function") return escapeHtml(s).replace(/\n/g, "<br>");
      return out;
    } catch (e) {
      return escapeHtml(s).replace(/\n/g, "<br>");
    }
  }
  function formatApiDetail(data) {
    if (data == null) return "(no body)";
    var d = data.detail;
    if (typeof d === "string") return d;
    if (Array.isArray(d))
      return d
        .map(function (x) {
          return (x && x.msg) || (x && x.message) || JSON.stringify(x);
        })
        .join("; ");
    try {
      return JSON.stringify(data);
    } catch (e) {
      return String(data);
    }
  }
  function renderGrounding(citations) {
    if (!groundingWrap || !groundingEl) return;
    var list = citations || [];
    if (!list.length) {
      groundingWrap.hidden = true;
      groundingEl.innerHTML = "";
      return;
    }
    groundingWrap.hidden = false;
    groundingEl.innerHTML = list
      .map(function (h, i) {
        var src = escapeHtml(h.source || "");
        var score = typeof h.score === "number" ? h.score.toFixed(1) : "";
        var cid = escapeHtml(h.id || "");
        var did = escapeHtml(h.doc_id || "");
        var prev = escapeHtml((h.text || "").slice(0, 320));
        if ((h.text || "").length > 320) prev += "…";
        return (
          '<article class="know-cite-card"><header class="know-cite-head"><span class="know-cite-num">#' +
          (i + 1) +
          '</span><span class="know-cite-src">' +
          src +
          '</span><span class="know-cite-score">' +
          escapeHtml(T("knowCiteScore").replace("%s", score)) +
          "</span></header>" +
          (did ? '<p class="know-cite-id"><code>' + did + "</code></p>" : "") +
          (cid ? '<p class="know-cite-chunk"><code>' + cid + "</code></p>" : "") +
          '<p class="know-cite-text">' +
          prev +
          "</p></article>"
        );
      })
      .join("");
  }

  function appendBubble(role, html) {
    if (!logEl) return;
    const div = document.createElement("div");
    div.className = "chat-msg " + role;
    const label = role === "user" ? T("knowYou") : T("knowAssistant");
    div.innerHTML = "<strong>" + label + "</strong><div class=\"md\">" + html + "</div>";
    logEl.appendChild(div);
  }
  function renderLog() {
    if (!logEl) return;
    logEl.innerHTML = "";
    try {
      messages.forEach(function (m) {
        var raw = m.content || "";
        var html = m.role === "assistant" ? safeMarkdown(raw) : escapeHtml(raw);
        appendBubble(m.role, html);
      });
      logEl.scrollTop = logEl.scrollHeight;
    } catch (e) {
      logEl.textContent = "Chat display error: " + String(e);
    }
  }
  async function sendChat() {
    if (!inputEl || !sendBtn || sendLocked) return;
    const text = (inputEl.value || "").trim();
    if (!text) return;
    sendLocked = true;
    inputEl.value = "";
    messages.push({ role: "user", content: text });
    renderLog();
    sendBtn.disabled = true;
    try {
      var sourceIds = [];
      if (sourcesEl) {
        sourcesEl.querySelectorAll(".know-source-cb:checked").forEach(function (cb) {
          var id = cb.getAttribute("data-doc-id");
          if (id) sourceIds.push(id);
        });
      }
      const r = await fetch("/api/v1/knowledge/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: messages.map((m) => ({ role: m.role, content: m.content })),
          source_doc_ids: sourceIds,
        }),
      });
      var data = null;
      try {
        data = await r.json();
      } catch (jsonErr) {
        messages.push({
          role: "assistant",
          content: "**Error:** HTTP " + r.status + " — response was not JSON.",
        });
        renderLog();
        return;
      }
      if (!r.ok) {
        messages.push({
          role: "assistant",
          content: "**Request failed (HTTP " + r.status + "):** " + formatApiDetail(data),
        });
        renderLog();
        return;
      }
      var reply =
        data.content != null && data.content !== ""
          ? data.content
          : formatApiDetail(data);
      messages.push({ role: "assistant", content: reply });
      renderLog();
      renderGrounding(data.citations || []);
    } catch (e) {
      messages.push({ role: "assistant", content: "**Error:** " + String(e) });
      renderLog();
    } finally {
      sendBtn.disabled = false;
      sendLocked = false;
    }
  }
  if (sendBtn) sendBtn.addEventListener("click", sendChat);
  if (inputEl) {
    inputEl.addEventListener("keydown", function (e) {
      if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        sendChat();
      }
    });
  }
  if (fileEl) {
    fileEl.addEventListener("change", async function () {
      const f = fileEl.files && fileEl.files[0];
      if (!f) return;
      const fd = new FormData();
      fd.append("file", f);
      try {
        const r = await fetch("/api/v1/knowledge/upload", { method: "POST", body: fd });
        const data = await r.json();
        if (!r.ok) throw new Error(formatApiDetail(data));
        messages.push({
          role: "assistant",
          content: T("knowUploadOk") + " `" + (data.doc_id || "") + "` — **" + (data.chunks || 0) + "** chunks.",
        });
        renderLog();
        refreshSources();
      } catch (e) {
        messages.push({ role: "assistant", content: "**Upload failed:** " + String(e) });
        renderLog();
      }
      fileEl.value = "";
    });
  }
  if (arxivBtn) {
    arxivBtn.addEventListener("click", async function () {
      const q = (arxivQ && arxivQ.value ? arxivQ.value : "").trim();
      if (!q) return;
      arxivBtn.disabled = true;
      try {
        const r = await fetch("/api/v1/knowledge/fetch-arxiv", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ query: q, max_results: 4 }),
        });
        const data = await r.json();
        if (!r.ok) throw new Error(formatApiDetail(data));
        messages.push({
          role: "assistant",
          content:
            T("knowArxivOk") + " **" + (data.ingested || 0) + "** / " + (data.items || 0) + " arXiv summaries.",
        });
        renderLog();
        refreshSources();
      } catch (e) {
        messages.push({ role: "assistant", content: "**arXiv:** " + String(e) });
        renderLog();
      } finally {
        arxivBtn.disabled = false;
      }
    });
  }
  async function refreshSources() {
    if (!sourcesEl) return;
    var countEl = document.getElementById("know-doc-count");
    try {
      const r = await fetch("/api/v1/knowledge/sources");
      const data = await r.json();
      const docs = data.documents || [];
      if (countEl) countEl.textContent = String(docs.length);
      if (!docs.length) {
        sourcesEl.innerHTML = "<p class=\"know-sources-empty\">" + escapeHtml(T("knowNoSources")) + "</p>";
        return;
      }
      sourcesEl.innerHTML = docs
        .map(function (d) {
          var title = escapeHtml(d.title || d.doc_id || "");
          var didRaw = d.doc_id || "";
          var didEsc = escapeHtml(didRaw);
          var n = d.chunks || 0;
          return (
            '<label class="know-source-row">' +
            '<input type="checkbox" class="know-source-cb" data-doc-id="' +
            didEsc +
            '" />' +
            '<span class="know-source-body"><span class="know-source-title">' +
            title +
            '</span><span class="know-source-meta">' +
            n +
            " " +
            escapeHtml(T("knowChunks")) +
            "</span></span></label>"
          );
        })
        .join("");
      sourcesEl.querySelectorAll(".know-source-cb").forEach(function (cb) {
        cb.addEventListener("change", function () {
          /* selection is read at send time */
        });
      });
    } catch (e) {
      if (countEl) countEl.textContent = "—";
      sourcesEl.textContent = String(e);
    }
  }
  function boot() {
    setPlaceholder();
    refreshSources();
    messages.length = 0;
    messages.push({ role: "assistant", content: T("knowWelcome") });
    renderLog();
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
  window.addEventListener("pilot-lang-change", function () {
    setPlaceholder();
    refreshSources();
  });
})();
