(function () {
  const listEl = document.getElementById("surrogate-list");
  function T(key) {
    if (window.PilotI18n) return window.PilotI18n.t(window.PilotI18n.get(), key);
    return key;
  }
  function escapeHtml(s) {
    const d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
  }
  async function loadList() {
    if (!listEl) return;
    try {
      const r = await fetch("/api/v1/surrogates/list");
      const data = await r.json();
      const items = data.items || [];
      const zh = window.PilotI18n && window.PilotI18n.get() === "zh";
      if (!items.length) {
        listEl.innerHTML = "<p class=\"hint\">" + escapeHtml(T("surEmpty")) + "</p>";
        return;
      }
      listEl.innerHTML = items
        .map(function (it) {
          var title = zh && it.title_zh ? it.title_zh : it.title_en || it.id;
          var desc = zh && it.desc_zh ? it.desc_zh : it.desc_en || "";
          var tags = (it.tags || []).join(", ");
          var paper = it.paper_url
            ? "<a href=\"" + escapeHtml(it.paper_url) + "\" target=\"_blank\" rel=\"noopener\">" + T("surLinkPaper") + "</a>"
            : "";
          var code = it.code_url
            ? "<a href=\"" + escapeHtml(it.code_url) + "\" target=\"_blank\" rel=\"noopener\">" + T("surLinkCode") + "</a>"
            : "";
          return (
            "<article class=\"surrogate-card\"><h3>" +
            escapeHtml(title) +
            "</h3>" +
            (tags ? "<div class=\"tags\">" + escapeHtml(tags) + "</div>" : "") +
            "<p style=\"font-size:0.88rem;color:#c4cad6\">" +
            escapeHtml(desc) +
            "</p><div class=\"links\">" +
            paper +
            code +
            "</div></article>"
          );
        })
        .join("");
    } catch (e) {
      listEl.textContent = String(e);
    }
  }
  var reg = document.getElementById("sur-register");
  if (reg) {
    reg.addEventListener("submit", async function (e) {
      e.preventDefault();
      var f = e.target;
      var body = {
        id: f.entry_id.value.trim(),
        title_en: f.title_en.value.trim(),
        title_zh: f.title_zh.value.trim(),
        desc_en: f.desc_en.value.trim(),
        desc_zh: f.desc_zh.value.trim(),
        paper_url: f.paper_url.value.trim(),
        code_url: f.code_url.value.trim(),
        tags: [],
      };
      var headers = { "Content-Type": "application/json" };
      var k = f.register_key.value.trim();
      if (k) headers["X-Pilot-Register-Key"] = k;
      try {
        const r = await fetch("/api/v1/surrogates/register", { method: "POST", headers: headers, body: JSON.stringify(body) });
        const data = await r.json();
        if (!r.ok) throw new Error(data.detail || JSON.stringify(data));
        alert(T("surOk"));
        f.reset();
        loadList();
      } catch (err) {
        alert(T("surFail") + " " + err);
      }
    });
  }
  var bund = document.getElementById("sur-bundle");
  if (bund) {
    bund.addEventListener("submit", async function (e) {
      e.preventDefault();
      var f = e.target;
      var fd = new FormData();
      fd.append("surrogate_id", f.surrogate_id.value.trim());
      fd.append("bundle", f.bundle.files[0]);
      var headers = {};
      var k = f.register_key.value.trim();
      if (k) headers["X-Pilot-Register-Key"] = k;
      try {
        const r = await fetch("/api/v1/surrogates/upload-bundle", { method: "POST", headers: headers, body: fd });
        const data = await r.json();
        if (!r.ok) throw new Error(data.detail || JSON.stringify(data));
        alert(T("surBundleOk") + " " + (data.url || ""));
        f.reset();
      } catch (err) {
        alert(T("surFail") + " " + err);
      }
    });
  }
  document.addEventListener("DOMContentLoaded", loadList);
  window.addEventListener("pilot-lang-change", loadList);
})();
