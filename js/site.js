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

    /* ---- Lightbox ----
     Any image inside a .fig__frame or .gallery opens in an overlay.
     Wide diagrams (BPMN is 4.4:1) open fit-to-screen, with a toggle to
     view at full size and pan. Closes on X, backdrop click, or Escape.
     Progressive: without JS the gallery links still open the file. */
    var zoomables = document.querySelectorAll(".fig__frame img, .gallery img");
    if (zoomables.length) {
        var box = document.createElement("div");
        box.className = "lb";
        box.setAttribute("role", "dialog");
        box.setAttribute("aria-modal", "true");
        box.setAttribute("aria-label", "Enlarged image");
        box.innerHTML =
            '<button class="lb__close" aria-label="Close">&times;</button>' +
            '<button class="lb__size" aria-label="Toggle full size">Actual size</button>' +
            '<div class="lb__stage"><img class="lb__img" alt=""></div>' +
            '<p class="lb__cap"></p>';
        document.body.appendChild(box);

        var img = box.querySelector(".lb__img");
        var cap = box.querySelector(".lb__cap");
        var stage = box.querySelector(".lb__stage");
        var sizeBtn = box.querySelector(".lb__size");
        var opener = null;

        function setFit(fit) {
            box.setAttribute("data-fit", fit ? "true" : "false");
            sizeBtn.textContent = fit ? "Actual size" : "Fit to screen";
        }

        function open(src, alt, caption) {
            img.src = src;
            img.alt = alt || "";
            cap.textContent = caption || "";
            cap.hidden = !caption;
            setFit(true);
            stage.scrollLeft = 0;
            box.setAttribute("data-open", "true");
            document.body.style.overflow = "hidden";
            box.querySelector(".lb__close").focus();
        }

        function close() {
            box.setAttribute("data-open", "false");
            document.body.style.overflow = "";
            img.src = "";
            if (opener && opener.focus) opener.focus();
        }

        Array.prototype.forEach.call(zoomables, function (el) {
            el.style.cursor = "zoom-in";
            el.addEventListener("click", function (e) {
                e.preventDefault();
                opener = el;
                var fig = el.closest("figure");
                var c = fig && fig.querySelector("figcaption");
                open(el.currentSrc || el.src, el.alt, c ? c.textContent.trim() : "");
            });
        });

        // Gallery images sit inside links; stop the navigation
        Array.prototype.forEach.call(document.querySelectorAll(".gallery a"), function (a) {
            a.addEventListener("click", function (e) {
                e.preventDefault();
            });
        });

        sizeBtn.addEventListener("click", function () {
            setFit(box.getAttribute("data-fit") !== "true");
        });
        box.querySelector(".lb__close").addEventListener("click", close);
        box.addEventListener("click", function (e) {
            if (e.target === box || e.target === stage) close();
        });
        document.addEventListener("keydown", function (e) {
            if (e.key === "Escape" && box.getAttribute("data-open") === "true") close();
        });
    }
})();
