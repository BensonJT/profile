/* ============================================================
   Jeffrey Benson — site.js
   ONE script governs the whole site. No framework, no CDN.
   Everything degrades: with JS off the page is fully readable.
   ============================================================ */
(function () {
    "use strict";

    /* ---- Mobile nav drawer ---- */
    var toggle = document.querySelector("[data-nav-toggle]");
    var drawer = document.querySelector("[data-nav-drawer]");
    if (toggle && drawer) {
        toggle.addEventListener("click", function () {
            var open = drawer.getAttribute("data-open") === "true";
            drawer.setAttribute("data-open", String(!open));
            toggle.setAttribute("aria-expanded", String(!open));
        });
        drawer.addEventListener("click", function (e) {
            if (e.target.tagName === "A") {
                drawer.setAttribute("data-open", "false");
                toggle.setAttribute("aria-expanded", "false");
            }
        });
    }

    /* ---- Decomposition figure ----
     Progressive disclosure of L0 -> L1 -> L2. The markup for all three
     levels is in the HTML, so with JS disabled every level is visible
     and the figure still reads correctly. */
    var decomp = document.querySelector("[data-decomp]");
    if (decomp) {
        var buttons = Array.prototype.slice.call(decomp.querySelectorAll("[data-level]"));
        var rows = Array.prototype.slice.call(decomp.querySelectorAll("[data-row]"));

        function show(level) {
            buttons.forEach(function (b) {
                b.setAttribute("aria-selected", String(b.dataset.level === level));
            });
            rows.forEach(function (r) {
                r.hidden = Number(r.dataset.row) > Number(level);
            });
        }

        buttons.forEach(function (b) {
            b.addEventListener("click", function () {
                show(b.dataset.level);
            });
        });
        show("1");
    }
})();
