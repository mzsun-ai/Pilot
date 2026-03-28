(function () {
  function markActive() {
    var page = document.body.getAttribute("data-pilot-nav") || "";
    document.querySelectorAll("[data-pilot-nav-link]").forEach(function (a) {
      var v = a.getAttribute("data-pilot-nav-link");
      var on = v === page;
      a.classList.toggle("is-active", on);
      if (on) a.setAttribute("aria-current", "page");
      else a.removeAttribute("aria-current");
    });
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", markActive);
  } else {
    markActive();
  }
})();
