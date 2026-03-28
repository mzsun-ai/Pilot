(function () {
  const STORAGE_KEY = "pilot_ui_lang";
  const DEFAULT = "en";
  const STRINGS = {
    en: {
      pageTitle: "Pilot Agent — EM Console",
      agentPageTitle: "Pilot Agent — EM Console",
      agentHeroTitle: "Pilot Agent",
      strap:
        "Describe your antenna and substrate in plain language. We generate an FDTD script, run <strong>openEMS</strong>, and return return loss and a report.",
      designTitle: "Design request",
      designHint: "Include frequency (GHz), substrate (e.g. FR4), and goals.",
      queryLabel: "Simulation request",
      queryPlaceholder: "e.g. 2.4 GHz patch on FR4, return loss near resonance.",
      chip24: "2.4 GHz patch · FR4 · S11",
      chip35: "3.5 GHz example",
      chip58: "5.8 GHz · FR4 · sweep",
      submit: "Run simulation",
      statusReady: "Ready",
      resultsTitle: "Results",
      resultsHint: "Markdown report and S11 when available.",
      placeholderHtml: "Enter a request and click <strong>Run simulation</strong>",
      plotCaption: "Return loss (openEMS)",
      plotAlt: "S11",
      footer: "PILOT · LOCAL OPENEMS",
      langLabel: "Language",
      navHome: "Home",
      navKnowledge: "Knowledge",
      navAgent: "Agent",
      navSurrogate: "Surrogate",
      navGuide: "Guide",
      navTeam: "Team",
      navApi: "API",
      hubPageTitle: "Pilot",
      hubTitle: "Pilot",
      hubSubtitle: "Knowledge · openEMS Agent · Surrogate models.",
      hubRow1Label: "01",
      hubRow1Title: "Pilot Knowledge",
      hubRow1Desc: "RAG, uploads, arXiv; optional Ollama / OpenAI in config.",
      hubRow2Label: "02",
      hubRow2Title: "Pilot Agent",
      hubRow2Desc: "Natural language → openEMS FDTD (or mock).",
      hubRow3Label: "03",
      hubRow3Title: "Pilot Surrogate models",
      hubRow3Desc: "Catalog, registration, code bundles.",
      hubRowGo: "Open →",
      hubFooter: "UESTC · PILOT",
      knowPageTitle: "Pilot — Knowledge",
      knowTitle: "Pilot Knowledge",
      knowLead: "Upload TXT/MD/PDF, fetch arXiv, chat with retrieval. Set knowledge.llm_provider in config.yaml.",
      knowChatTitle: "Chat",
      knowCorpusTitle: "Corpus",
      knowCorpusHint: "Uploads go to outputs/knowledge_corpus/.",
      knowUploadBtn: "Upload file",
      knowArxivBtn: "Fetch arXiv",
      knowSourcesTitle: "Sources",
      knowSend: "Send",
      knowInputPh: "Ask about EM / FDTD… (Ctrl+Enter)",
      knowYou: "You",
      knowAssistant: "Pilot Knowledge",
      knowWelcome: "Welcome. Upload or fetch arXiv, then ask questions.",
      knowUploadOk: "Ingested",
      knowArxivOk: "arXiv:",
      knowNoSources: "No documents yet.",
      knowFooter: "Pilot Knowledge · local RAG",
      surPageTitle: "Pilot — Surrogates",
      surTitle: "Pilot Surrogate models",
      surLead: "Register models and upload ZIP bundles (optional admin key).",
      surCatalogTitle: "Catalog",
      surRegisterTitle: "Register",
      surRegisterHint: "X-Pilot-Register-Key if configured.",
      surSubmit: "Submit",
      surBundleTitle: "Upload bundle",
      surBundleHint: "ZIP for existing surrogate id.",
      surBundleBtn: "Upload zip",
      surLinkPaper: "Paper",
      surLinkCode: "Code",
      surEmpty: "No entries yet.",
      surOk: "Registered.",
      surFail: "Error:",
      surBundleOk: "Uploaded:",
      surFooter: "Pilot Surrogate",
      showcaseTitle: "Example scenarios",
      showcaseSubtitle: "Load a prompt or write your own.",
      ex1Title: "2.4 GHz patch",
      ex1Tag: "Wi-Fi · FR4",
      ex1Desc: "Return loss near resonance.",
      ex2Title: "3.5 GHz patch",
      ex2Tag: "Sub-6",
      ex2Desc: "S11 sweep.",
      ex3Title: "5.8 GHz patch",
      ex3Tag: "ISM",
      ex3Desc: "Narrow band focus.",
      exUsePrompt: "Load prompt",
      highlightsTitle: "Why Pilot",
      hl1Title: "Open source",
      hl1Desc: "openEMS + CSXCAD.",
      hl2Title: "Natural language",
      hl2Desc: "English or Chinese input.",
      hl3Title: "Web + REST",
      hl3Desc: "Same API as UI.",
      hl4Title: "Artifacts",
      hl4Desc: "Report, S11, CSV, script.",
      pipelineTitle: "Pipeline",
      pipelineHtml: "<strong>Parse</strong> → <strong>plan</strong> → <strong>script</strong> → <strong>run</strong> → <strong>report</strong>.",
      teamPageTitle: "Pilot — Team",
      teamHeroTitle: "Team",
      teamHeroLead: "Pilot — UESTC.",
      teamFooter: "UESTC · PILOT",
      teamBackHome: "← Home",
    },
    zh: {
      pageTitle: "Pilot Agent — 电磁控制台",
      agentPageTitle: "Pilot Agent — 电磁控制台",
      agentHeroTitle: "Pilot Agent",
      strap: "用自然语言描述天线与基板，生成 FDTD 脚本并运行 <strong>openEMS</strong>，返回回波损耗与报告。",
      designTitle: "设计需求",
      designHint: "写明频率（GHz）、基板（如 FR4）、目标指标。",
      queryLabel: "仿真需求",
      queryPlaceholder: "例如：FR4 上 2.4 GHz 贴片，谐振附近 S11。",
      chip24: "2.4 GHz 贴片 · FR4 · S11",
      chip35: "3.5 GHz 示例",
      chip58: "5.8 GHz · FR4 · 扫频",
      submit: "运行仿真",
      statusReady: "就绪",
      resultsTitle: "结果",
      resultsHint: "Markdown 与 S11（若已生成）。",
      placeholderHtml: "输入需求后点击 <strong>运行仿真</strong>",
      plotCaption: "回波损耗（openEMS）",
      plotAlt: "S11",
      footer: "PILOT · 本地 OPENEMS",
      langLabel: "语言",
      navHome: "首页",
      navKnowledge: "知识库",
      navAgent: "Agent",
      navSurrogate: "代理模型",
      navGuide: "教程",
      navTeam: "团队",
      navApi: "API",
      hubPageTitle: "Pilot",
      hubTitle: "Pilot",
      hubSubtitle: "知识库 · openEMS 智能体 · 代理模型。",
      hubRow1Label: "01",
      hubRow1Title: "Pilot Knowledge",
      hubRow1Desc: "RAG、上传、arXiv；可在 config 接大模型。",
      hubRow2Label: "02",
      hubRow2Title: "Pilot Agent",
      hubRow2Desc: "自然语言驱动 openEMS（或 mock）。",
      hubRow3Label: "03",
      hubRow3Title: "Pilot Surrogate models",
      hubRow3Desc: "目录、登记、代码包。",
      hubRowGo: "进入 →",
      hubFooter: "电子科技大学 · PILOT",
      knowPageTitle: "Pilot — 知识库",
      knowTitle: "Pilot Knowledge",
      knowLead: "上传 TXT/MD/PDF，拉取 arXiv，对话检索。config.yaml 配置 llm_provider。",
      knowChatTitle: "对话",
      knowCorpusTitle: "语料",
      knowCorpusHint: "文件进入 outputs/knowledge_corpus/。",
      knowUploadBtn: "上传文件",
      knowArxivBtn: "拉取 arXiv",
      knowSourcesTitle: "来源",
      knowSend: "发送",
      knowInputPh: "可问电磁/FDTD…（Ctrl+Enter）",
      knowYou: "你",
      knowAssistant: "Pilot Knowledge",
      knowWelcome: "你好。可上传或拉取 arXiv 后再提问。",
      knowUploadOk: "已入库",
      knowArxivOk: "arXiv：",
      knowNoSources: "暂无文档。",
      knowFooter: "Pilot Knowledge · 本地 RAG",
      surPageTitle: "Pilot — 代理模型",
      surTitle: "Pilot Surrogate models",
      surLead: "登记模型并上传 ZIP（可配置管理员密钥）。",
      surCatalogTitle: "目录",
      surRegisterTitle: "登记",
      surRegisterHint: "若配置了密钥请填写 X-Pilot-Register-Key。",
      surSubmit: "提交",
      surBundleTitle: "上传包",
      surBundleHint: "需已存在的 surrogate id。",
      surBundleBtn: "上传 ZIP",
      surLinkPaper: "论文",
      surLinkCode: "代码",
      surEmpty: "暂无条目。",
      surOk: "已登记。",
      surFail: "错误：",
      surBundleOk: "已上传：",
      surFooter: "Pilot Surrogate",
      showcaseTitle: "示例场景",
      showcaseSubtitle: "载入示例或自行输入。",
      ex1Title: "2.4 GHz 贴片",
      ex1Tag: "Wi-Fi · FR4",
      ex1Desc: "谐振附近 S11。",
      ex2Title: "3.5 GHz 贴片",
      ex2Tag: "Sub-6",
      ex2Desc: "扫频示例。",
      ex3Title: "5.8 GHz 贴片",
      ex3Tag: "ISM",
      ex3Desc: "窄带对比。",
      exUsePrompt: "载入示例",
      highlightsTitle: "Pilot 特点",
      hl1Title: "开源",
      hl1Desc: "openEMS + CSXCAD。",
      hl2Title: "自然语言",
      hl2Desc: "中英文描述。",
      hl3Title: "网页 + API",
      hl3Desc: "接口与 UI 一致。",
      hl4Title: "产物",
      hl4Desc: "报告、S11、CSV、脚本。",
      pipelineTitle: "流程",
      pipelineHtml: "<strong>解析</strong> → <strong>规划</strong> → <strong>脚本</strong> → <strong>运行</strong> → <strong>报告</strong>。",
      teamPageTitle: "Pilot — 团队",
      teamHeroTitle: "团队",
      teamHeroLead: "Pilot — 电子科技大学。",
      teamFooter: "电子科技大学 · PILOT",
      teamBackHome: "← 首页",
    },
  };

  function normalize(lang) {
    return lang === "zh" || lang === "zh-CN" ? "zh" : "en";
  }
  function get() {
    try {
      const s = localStorage.getItem(STORAGE_KEY);
      if (s === "zh" || s === "en") return s;
    } catch (_) {}
    const nav = typeof navigator !== "undefined" ? navigator.language || "" : "";
    if (nav.toLowerCase().startsWith("zh")) return "zh";
    return DEFAULT;
  }
  function set(lang) {
    const L = normalize(lang);
    try {
      localStorage.setItem(STORAGE_KEY, L);
    } catch (_) {}
    apply(L);
    window.dispatchEvent(new CustomEvent("pilot-lang-change", { detail: { lang: L } }));
  }
  function t(lang, key) {
    const L = normalize(lang);
    const pack = STRINGS[L] || STRINGS.en;
    return pack[key] !== undefined ? pack[key] : STRINGS.en[key] || key;
  }
  function apply(lang) {
    const L = normalize(lang);
    document.documentElement.lang = L === "zh" ? "zh-CN" : "en";
    const page = document.body && document.body.getAttribute("data-pilot-page");
    const titleMap = { team: "teamPageTitle", hub: "hubPageTitle", knowledge: "knowPageTitle", surrogate: "surPageTitle", console: "agentPageTitle" };
    const titleKey = (page && titleMap[page]) || "pageTitle";
    document.title = t(L, titleKey);
    document.querySelectorAll("[data-i18n]").forEach((el) => {
      const key = el.getAttribute("data-i18n");
      if (!key) return;
      if (el.hasAttribute("data-i18n-html")) el.innerHTML = t(L, key);
      else el.textContent = t(L, key);
    });
    const ta = document.getElementById("query");
    if (ta) ta.placeholder = t(L, "queryPlaceholder");
    const plotCap = document.querySelector(".plot-caption");
    if (plotCap) plotCap.textContent = t(L, "plotCaption");
    const plotImg = document.getElementById("plot-img");
    if (plotImg) plotImg.alt = t(L, "plotAlt");
    document.querySelectorAll(".lang-btn").forEach((btn) => {
      const target = btn.getAttribute("data-lang");
      btn.classList.toggle("active", target === L);
      btn.setAttribute("aria-pressed", target === L ? "true" : "false");
    });
  }
  window.PilotI18n = { get, set, t, apply, normalize, STRINGS };
  document.addEventListener("DOMContentLoaded", () => {
    apply(get());
    document.querySelectorAll(".lang-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        const lang = btn.getAttribute("data-lang");
        if (lang) set(lang);
      });
    });
  });
})();
