(function () {
  const listEl = document.getElementById("surrogate-list");
  const modal = document.getElementById("sur-detail-modal");
  const modalInner = document.getElementById("sur-modal-inner");

  function T(key) {
    if (window.PilotI18n) return window.PilotI18n.t(window.PilotI18n.get(), key);
    return key;
  }
  function escapeHtml(s) {
    const d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
  }
  function formatDesc(text) {
    if (!text) return "";
    var parts = String(text)
      .split(/\n\n+/)
      .map(function (p) {
        return p.trim();
      })
      .filter(Boolean);
    if (!parts.length) return "";
    return parts
      .map(function (p) {
        return "<p class=\"sur-desc-p\">" + escapeHtml(p) + "</p>";
      })
      .join("");
  }
  function excerptDesc(text, max) {
    var s = String(text || "").split(/\n\n+/)[0] || "";
    s = s.replace(/\s+/g, " ").trim();
    if (s.length <= max) return s;
    return s.slice(0, max).trim() + "…";
  }
  function authorsDisplay(it) {
    if (!it || !it.authors) return "";
    if (Array.isArray(it.authors)) return it.authors.join(", ");
    return String(it.authors);
  }
  function encodePayload(it) {
    var payload = {
      title_en: it.title_en || "",
      title_zh: it.title_zh || "",
      desc_en: it.desc_en || "",
      desc_zh: it.desc_zh || "",
      authors: authorsDisplay(it),
      tags: it.tags || [],
      scenarios: it.scenarios || [],
      paper_url: it.paper_url || "",
      code_url: it.code_url || "",
      graphic_abstract: it.graphic_abstract || "",
      arxiv_id: it.arxiv_id || "",
    };
    return encodeURIComponent(JSON.stringify(payload));
  }
  function openSurDetailModal(payload) {
    if (!modal || !modalInner) return;
    var zh = window.PilotI18n && window.PilotI18n.get() === "zh";
    var title = zh && payload.title_zh ? payload.title_zh : payload.title_en || "";
    var desc = zh && payload.desc_zh ? payload.desc_zh : payload.desc_en || "";
    var pdfUrl = payload.arxiv_id ? "https://arxiv.org/pdf/" + payload.arxiv_id + ".pdf" : "";
    var tags = (payload.tags || []).join(" · ");

    var html = "";
    html += '<header class="sur-modal-header">';
    html += "<h2 id=\"sur-modal-title\" class=\"sur-modal-title\">" + escapeHtml(title) + "</h2>";
    var authLine = payload.authors || "";
    if (authLine) {
      html +=
        '<p class="sur-modal-authors"><span class="sur-authors-label">' +
        escapeHtml(T("surAuthorsLabel")) +
        "</span> " +
        escapeHtml(authLine) +
        "</p>";
    }
    if (tags) {
      html += '<p class="sur-modal-tags">' + escapeHtml(tags) + "</p>";
    }
    html += "</header>";

    if (payload.graphic_abstract) {
      html += '<figure class="sur-modal-figure">';
      html +=
        '<a href="' +
        escapeHtml(payload.graphic_abstract) +
        '" target="_blank" rel="noopener noreferrer" class="sur-modal-figure-link">';
      html +=
        '<img src="' +
        escapeHtml(payload.graphic_abstract) +
        '" alt="' +
        escapeHtml(T("surGraphicAbstractAlt")) +
        '" class="sur-modal-figure-img" />';
      html += "</a>";
      html += '<figcaption class="sur-graphic-caption">' + escapeHtml(T("surGraphicAbstractCaption")) + "</figcaption>";
      html += "</figure>";
    }

    html += '<div class="sur-modal-body">' + formatDesc(desc) + "</div>";

    var dlParts = [];
    if (pdfUrl) {
      dlParts.push(
        '<li><a href="' +
          escapeHtml(pdfUrl) +
          '" target="_blank" rel="noopener noreferrer" class="sur-modal-dl-link">' +
          escapeHtml(T("surPdfLink")) +
          "</a></li>"
      );
    }
    if (payload.paper_url) {
      dlParts.push(
        '<li><a href="' +
          escapeHtml(payload.paper_url) +
          '" target="_blank" rel="noopener noreferrer" class="sur-modal-dl-link">' +
          escapeHtml(T("surAbsLink")) +
          "</a></li>"
      );
    }
    if (payload.code_url) {
      dlParts.push(
        '<li><a href="' +
          escapeHtml(payload.code_url) +
          '" target="_blank" rel="noopener noreferrer" class="sur-modal-dl-link">' +
          escapeHtml(T("surLinkCode")) +
          "</a></li>"
      );
    }
    if (dlParts.length) {
      html += '<section class="sur-modal-downloads">';
      html += "<h3 class=\"sur-modal-dl-title\">" + escapeHtml(T("surDownloadsHeading")) + "</h3>";
      html += '<ul class="sur-modal-dl-list">' + dlParts.join("") + "</ul></section>";
    }

    modalInner.innerHTML = html;
    modal.hidden = false;
    modal.setAttribute("aria-hidden", "false");
    document.body.classList.add("sur-modal-open");
    var closeBtn = modal.querySelector(".sur-modal-close");
    if (closeBtn) closeBtn.focus();
  }
  function closeSurDetailModal() {
    if (!modal) return;
    modal.hidden = true;
    modal.setAttribute("aria-hidden", "true");
    document.body.classList.remove("sur-modal-open");
    if (modalInner) modalInner.innerHTML = "";
  }

  document.addEventListener("click", function (e) {
    var hit = e.target.closest("[data-sur-detail]");
    if (hit && hit.getAttribute("data-sur-detail")) {
      try {
        var raw = decodeURIComponent(hit.getAttribute("data-sur-detail"));
        openSurDetailModal(JSON.parse(raw));
      } catch (err) {
        console.warn(err);
      }
      return;
    }
    if (e.target.closest("[data-sur-modal-close]")) {
      closeSurDetailModal();
    }
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && modal && !modal.hidden) {
      closeSurDetailModal();
    }
  });

  async function loadList() {
    if (!listEl) return;
    try {
      const r = await fetch("/api/v1/surrogates/list");
      const data = await r.json();
      let items = data.items || [];
      const zh = window.PilotI18n && window.PilotI18n.get() === "zh";
      items = items.slice().sort(function (a, b) {
        return (b.featured ? 1 : 0) - (a.featured ? 1 : 0);
      });
      if (!items.length) {
        listEl.innerHTML = "<div class=\"sur-empty-state\"><p>" + escapeHtml(T("surEmpty")) + "</p></div>";
        return;
      }
      listEl.innerHTML = items
        .map(function (it) {
          var title = zh && it.title_zh ? it.title_zh : it.title_en || it.id;
          var desc = zh && it.desc_zh ? it.desc_zh : it.desc_en || "";
          var tags = (it.tags || []).join(" · ");
          var featured = !!it.featured;
          var cardClass = "surrogate-card" + (featured ? " surrogate-card--featured" : "");
          var enc = encodePayload(it);

          var badge = "";
          if (featured) {
            badge =
              '<div class="sur-featured-bar"><span class="sur-featured-badge">' +
              escapeHtml(T("surFeaturedBadge")) +
              "</span>";
            if (it.arxiv_id) {
              badge +=
                '<a class="sur-arxiv-pill" href="' +
                escapeHtml(it.paper_url || "https://arxiv.org/abs/" + it.arxiv_id) +
                '" target="_blank" rel="noopener noreferrer">arXiv:' +
                escapeHtml(it.arxiv_id) +
                "</a>";
            }
            badge += "</div>";
          }

          var idLine = !featured && it.id ? "<div class=\"sur-card-id\">" + escapeHtml(it.id) + "</div>" : "";
          if (featured && it.id) {
            idLine = '<div class="sur-card-id sur-card-id--sub">' + escapeHtml(it.id) + "</div>";
          }

          var authStr = authorsDisplay(it);
          var authors = "";
          if (authStr) {
            authors =
              '<p class="sur-authors"><span class="sur-authors-label">' +
              escapeHtml(T("surAuthorsLabel")) +
              "</span> " +
              escapeHtml(authStr) +
              "</p>";
          }

          var paper = it.paper_url
            ? "<a href=\"" + escapeHtml(it.paper_url) + "\" target=\"_blank\" rel=\"noopener noreferrer\">" + T("surLinkPaper") + "</a>"
            : "";
          var code = it.code_url
            ? "<a href=\"" + escapeHtml(it.code_url) + "\" target=\"_blank\" rel=\"noopener noreferrer\">" + T("surLinkCode") + "</a>"
            : "";

          if (featured && it.graphic_abstract) {
            var gsrc = escapeHtml(it.graphic_abstract);
            var excerpt = excerptDesc(desc, 280);
            return (
              "<article class=\"" +
              cardClass +
              "\">" +
              badge +
              idLine +
              '<div class="sur-featured-row">' +
              '<div class="sur-featured-media">' +
              '<button type="button" class="sur-thumb-hit" data-sur-detail="' +
              enc +
              '" title="' +
              escapeHtml(T("surEnlargeHint")) +
              '">' +
              '<span class="sur-thumb-frame">' +
              '<img src="' +
              gsrc +
              '" alt="" loading="lazy" decoding="async" />' +
              "</span>" +
              '<span class="sur-thumb-label">' +
              escapeHtml(T("surEnlargeHint")) +
              "</span>" +
              "</button>" +
              "</div>" +
              '<div class="sur-featured-body">' +
              "<h3>" +
              escapeHtml(title) +
              "</h3>" +
              authors +
              (tags ? "<div class=\"tags\">" + escapeHtml(tags) + "</div>" : "") +
              '<p class="sur-featured-excerpt">' +
              escapeHtml(excerpt) +
              "</p>" +
              '<div class="sur-featured-actions">' +
              '<button type="button" class="sur-detail-btn" data-sur-detail="' +
              enc +
              '">' +
              escapeHtml(T("surViewDetails")) +
              "</button>" +
              "</div>" +
              "</div>" +
              "</div>" +
              "</article>"
            );
          }

          var descHtml = featured ? formatDesc(desc) : "<p class=\"sur-card-desc\">" + escapeHtml(desc) + "</p>";
          return (
            "<article class=\"" +
            cardClass +
            "\">" +
            badge +
            idLine +
            "<h3>" +
            escapeHtml(title) +
            "</h3>" +
            authors +
            (tags ? "<div class=\"tags\">" + escapeHtml(tags) + "</div>" : "") +
            '<div class="sur-desc-block">' +
            descHtml +
            "</div>" +
            '<div class="links">' +
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
  function splitFieldList(raw) {
    return String(raw || "")
      .split(/[,;，；]/)
      .map(function (x) {
        return x.trim();
      })
      .filter(Boolean);
  }
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
        authors: splitFieldList(f.authors && f.authors.value),
        tags: splitFieldList(f.tags && f.tags.value),
        scenarios: splitFieldList(f.scenarios && f.scenarios.value),
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
  window.addEventListener("pilot-lang-change", function () {
    closeSurDetailModal();
    loadList();
  });
})();
