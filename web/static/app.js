(function () {
  const $ = (s) => document.querySelector(s);
  const queryEl = $("#query");
  const submitBtn = $("#submit");
  const statusEl = $("#status");
  const resultsPanel = $("#results-panel");
  const reportEl = $("#report");
  const errorBanner = $("#error");
  const plotImg = $("#plot-img");
  const plotWrap = $("#plot-wrap");
  const linksEl = $("#artifact-links");

  function T(key) {
    if (window.PilotI18n) return window.PilotI18n.t(window.PilotI18n.get(), key);
    const fb = {
      statusReady: "Ready",
      statusRunning: "Running FDTD (openEMS)…",
      errRunFailed: "Run failed",
      errBadResponse: "Server returned non-JSON. Is the API running?",
      errHttp: "Request failed (HTTP %s)",
      linkCsv: "Download s11.csv",
      linkScript: "Open generated openEMS script",
    };
    return fb[key] || key;
  }

  function formatApiErrorBody(data, httpStatus) {
    if (data == null) return T("errRunFailed");
    if (typeof data.error === "string" && data.error.trim()) return data.error;
    const d = data.detail;
    if (typeof d === "string" && d.trim()) return d;
    if (Array.isArray(d) && d.length)
      return d.map((x) => (x && (x.msg || x.message)) || JSON.stringify(x)).join("; ");
    if (d && typeof d === "object") return JSON.stringify(d);
    return T("errHttp").replace("%s", String(httpStatus || "?"));
  }

  function setStatusReady() {
    statusEl.textContent = T("statusReady");
    statusEl.setAttribute("data-i18n", "statusReady");
  }

  async function runQuery(text) {
    submitBtn.disabled = true;
    statusEl.textContent = T("statusRunning");
    statusEl.removeAttribute("data-i18n");
    statusEl.classList.add("running");
    errorBanner.classList.remove("visible");
    errorBanner.textContent = "";
    reportEl.innerHTML = "";
    plotWrap.style.display = "none";
    linksEl.innerHTML = "";
    resultsPanel.classList.remove("empty");

    try {
      const payload = JSON.stringify({ query: text });
      let res = await fetch("/api/v1/simulations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: payload,
      });
      if (res.status === 404) {
        res = await fetch("/api/run", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: payload,
        });
      }
      let data;
      try {
        data = await res.json();
      } catch (_) {
        errorBanner.textContent = !res.ok ? T("errBadResponse") + " HTTP " + res.status : T("errBadResponse");
        errorBanner.classList.add("visible");
        return;
      }
      if (!res.ok) {
        errorBanner.textContent = formatApiErrorBody(data, res.status);
        errorBanner.classList.add("visible");
        return;
      }
      if (!data.ok) {
        errorBanner.textContent = formatApiErrorBody(data, res.status);
        errorBanner.classList.add("visible");
        return;
      }
      if (typeof marked !== "undefined" && data.report_markdown) {
        reportEl.innerHTML = marked.parse(data.report_markdown);
      } else {
        reportEl.textContent = data.report_markdown || "";
      }
      if (data.task_id) {
        const u = data.artifact_urls || {};
        const tid = data.task_id;
        const plotUrl = u.s11_plot || `/api/artifact/${tid}/s11.png`;
        const csvUrl = u.s11_csv || `/api/artifact/${tid}/s11.csv`;
        const scriptUrl = u.script || `/api/artifact/${tid}/run_openems_patch.py`;
        plotImg.src = plotUrl + "?t=" + Date.now();
        plotImg.onload = () => {
          plotWrap.style.display = "block";
        };
        plotImg.onerror = () => {
          plotWrap.style.display = "none";
        };
        const a1 = document.createElement("a");
        a1.href = csvUrl;
        a1.textContent = T("linkCsv");
        a1.download = "";
        const a2 = document.createElement("a");
        a2.href = scriptUrl;
        a2.textContent = T("linkScript");
        a2.target = "_blank";
        linksEl.append(a1, a2);
      }
    } catch (e) {
      errorBanner.textContent = String(e);
      errorBanner.classList.add("visible");
    } finally {
      submitBtn.disabled = false;
      statusEl.classList.remove("running");
      setStatusReady();
    }
  }

  submitBtn.addEventListener("click", () => {
    const q = queryEl.value.trim();
    if (q.length < 3) return;
    runQuery(q);
  });

  document.querySelectorAll(".chip").forEach((c) => {
    c.addEventListener("click", () => {
      queryEl.value = c.dataset.q || "";
      queryEl.focus();
    });
  });

  window.addEventListener("pilot-lang-change", () => {
    if (!statusEl.classList.contains("running")) setStatusReady();
    const links = linksEl.querySelectorAll("a");
    if (links.length >= 2 && window.PilotI18n) {
      links[0].textContent = window.PilotI18n.t(window.PilotI18n.get(), "linkCsv");
      links[1].textContent = window.PilotI18n.t(window.PilotI18n.get(), "linkScript");
    }
  });
})();
