// [Br]om – Website. Kein Inline-Code (CSP), alles hier.
(function () {
  "use strict";
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  // Jahr im Footer
  $$("[data-year]").forEach(function (el) { el.textContent = String(new Date().getFullYear()); });

  // ---------- Tester ----------
  var tester = $(".tester");
  if (tester) {
    var text = $(".tester__text", tester);
    var texts = {};
    try { texts = JSON.parse(tester.getAttribute("data-texts")); } catch (e) { texts = {}; }
    var ctl = function (n) { return $('[data-ctl="' + n + '"]', tester); };
    var out = function (n, v) { var o = $('[data-out="' + n + '"]', tester); if (o) o.textContent = v; };
    var apply = function () {
      var w = ctl("wght").value, s = ctl("size").value, t = ctl("track").value, lh = ctl("lh").value;
      text.style.fontWeight = w;
      text.style.fontSize = s + "px";
      text.style.letterSpacing = (t / 100) + "em";
      text.style.lineHeight = (lh / 100).toFixed(2);
      text.style.fontStyle = ctl("italic").checked ? "italic" : "normal";
      var feats = $$("[data-feature]", tester).filter(function (c) { return c.checked; })
        .map(function (c) { return '"' + c.getAttribute("data-feature") + '"'; });
      text.style.fontFeatureSettings = feats.length ? feats.join(", ") : "normal";
      out("wght", w); out("size", s); out("track", t); out("lh", (lh / 100).toFixed(2).replace(".", ","));
    };
    // Kleine Bildschirme: kleiner starten, damit Wörter nicht umbrechen müssen.
    if (window.matchMedia && window.matchMedia("(max-width: 640px)").matches) ctl("size").value = "36";
    $$("input", tester).forEach(function (i) { i.addEventListener("input", apply); });
    ctl("text").addEventListener("change", function () {
      if (texts[this.value]) text.textContent = texts[this.value];
    });
    // Einfügen nur als Text
    text.addEventListener("paste", function (e) {
      e.preventDefault();
      var t = (e.clipboardData || window.clipboardData).getData("text");
      document.execCommand("insertText", false, t);
    });
    apply();
  }

  // ---------- Gewichte ----------
  var wfi = $("[data-wf-italic]");
  if (wfi) wfi.addEventListener("change", function () { $(".wf").classList.toggle("is-italic", wfi.checked); });

  // ---------- Zeichen ----------
  var info = { ch: $("[data-ginfo-ch]"), cp: $("[data-ginfo-cp]"), n: $("[data-ginfo-n]") };
  var sel = null;
  var show = function (b) {
    var cp = b.getAttribute("data-cp");
    info.ch.textContent = String.fromCodePoint(parseInt(cp, 16));
    info.cp.textContent = "U+" + cp;
    info.n.textContent = (b.getAttribute("data-n") || "").toLowerCase() || "ohne Namen";
  };
  var copy = function (txt, done) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(txt).then(done, function () {});
    }
  };
  var blocks = $(".gblocks");
  if (blocks) {
    blocks.addEventListener("mouseover", function (e) {
      var b = e.target.closest(".g"); if (b) show(b);
    });
    blocks.addEventListener("focusin", function (e) {
      var b = e.target.closest(".g"); if (b) show(b);
    });
    blocks.addEventListener("click", function (e) {
      var b = e.target.closest(".g"); if (!b) return;
      if (sel) sel.classList.remove("is-sel");
      sel = b; b.classList.add("is-sel"); show(b);
      copy(String.fromCodePoint(parseInt(b.getAttribute("data-cp"), 16)), function () {
        b.classList.add("is-copied");
        info.n.textContent = "kopiert";
        setTimeout(function () { b.classList.remove("is-copied"); }, 700);
      });
    });
    $$(".seg__b").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var f = btn.getAttribute("data-filter");
        $$(".seg__b").forEach(function (x) { x.classList.toggle("is-on", x === btn); x.setAttribute("aria-pressed", x === btn ? "true" : "false"); });
        $$(".gblock").forEach(function (s) { s.hidden = !(f === "alle" || s.getAttribute("data-group") === f); });
      });
    });
    var gw = $("[data-g-wght]");
    if (gw) gw.addEventListener("input", function () {
      blocks.style.setProperty("--gw", gw.value);
      info.ch.style.fontWeight = gw.value;
      var o = $('[data-out="gwght"]'); if (o) o.textContent = gw.value;
    });
  }

  // ---------- Code kopieren ----------
  $$("[data-copy]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var src = $(btn.getAttribute("data-copy"));
      if (!src) return;
      copy(src.textContent, function () {
        var old = btn.textContent; btn.textContent = "Kopiert";
        setTimeout(function () { btn.textContent = old; }, 1200);
      });
    });
  });
})();
