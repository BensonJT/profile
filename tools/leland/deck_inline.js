/* ============================================================
   Leland-only deck runtime. build_single.py adds this script to the
   single-file bundle; the multi-file site never loads it.

   Why: Leland blocks frames, so the iframe Presentation window from
   builder.js shows nothing there. build_single.py stores every linked
   deck's CSS and slides on the dialog (data-deck-inline-b64, a JSON map
   keyed by deck file name) and gives each link a data-deck-key. This
   script draws the clicked deck in its own shadow root inside the dialog,
   so each deck's styles stay scoped, and drives it: arrows, click, swipe,
   N for notes, F to fill the window (true full screen is blocked by the
   sandbox). The dialog title comes from the link's data-deck-title.

   It listens in the capture phase and stops the click, so builder.js's
   iframe handler never runs in the bundle. builder.js still handles
   Close and the backdrop click.
   ============================================================ */
(function () {
    "use strict";

    var win = document.querySelector("[data-deck-sheet]");
    var b64 = win && win.getAttribute("data-deck-inline-b64");
    if (!b64 || typeof win.showModal !== "function" || !document.body.attachShadow) return;

    var slot = win.querySelector("[data-deck-slot]");
    var heading = win.querySelector(".sheet__title");
    var defaultTitle = heading.textContent;
    var all = null; // the decoded map, on first open
    var decks = {}; // key -> {host, body, stage, slides, notes, text, count, i}
    var cur = null;
    var maxed = false;

    function build(key) {
        if (!all) {
            var bytes = Uint8Array.from(atob(b64), function (c) {
                return c.charCodeAt(0);
            });
            all = JSON.parse(new TextDecoder("utf-8").decode(bytes));
        }
        var src = all[key];
        if (!src) return null;
        var d = { i: 0 };
        d.host = document.createElement("div");
        d.host.className = "deck__frame";
        d.host.style.position = "relative";
        d.host.style.overflow = "hidden";
        slot.appendChild(d.host);
        var root = d.host.attachShadow({ mode: "open" });
        root.innerHTML = "<style>" + src.css + '</style><div class="deck-body">' + src.html + "</div>";
        d.body = root.querySelector(".deck-body");
        d.stage = root.querySelector(".stage");
        d.slides = [].slice.call(root.querySelectorAll(".slide"));
        d.notes = root.querySelector(".notes");
        d.text = root.querySelector(".notes-text");
        d.count = root.querySelector(".notes-count");

        d.stage.addEventListener("click", function (e) {
            var r = d.stage.getBoundingClientRect();
            go(e.clientX - r.left < r.width / 3 ? d.i - 1 : d.i + 1);
        });
        var x0 = null;
        d.stage.addEventListener(
            "touchstart",
            function (e) {
                x0 = e.touches[0].clientX;
            },
            { passive: true },
        );
        d.stage.addEventListener("touchend", function (e) {
            if (x0 === null) return;
            var dx = e.changedTouches[0].clientX - x0;
            if (Math.abs(dx) > 40) go(dx < 0 ? d.i + 1 : d.i - 1);
            x0 = null;
        });
        return d;
    }

    function fit() {
        if (!cur) return;
        if (maxed) {
            var head = win.querySelector(".sheet__head");
            var hint = win.querySelector(".deck__hint");
            cur.host.style.height = window.innerHeight - 20 - head.offsetHeight - (hint ? hint.offsetHeight : 0) + "px";
        }
        var h = cur.host.clientHeight - (cur.body.classList.contains("show-notes") ? cur.notes.offsetHeight : 0);
        cur.stage.style.height = h + "px";
        cur.body.style.setProperty("--s", Math.min(cur.host.clientWidth / 1920, h / 1080));
    }

    function go(n) {
        var d = cur;
        d.i = Math.max(0, Math.min(d.slides.length - 1, n));
        d.slides.forEach(function (el, k) {
            el.classList.toggle("on", k === d.i);
        });
        var aside = d.slides[d.i].querySelector("aside");
        d.text.textContent = aside ? aside.textContent : "";
        d.count.textContent = d.i + 1 + " / " + d.slides.length;
    }

    function toggleMax() {
        maxed = !maxed;
        win.style.width = maxed ? "calc(100vw - 16px)" : "";
        win.style.maxHeight = maxed ? "calc(100vh - 16px)" : "";
        win.style.overflow = maxed ? "hidden" : "";
        Object.keys(decks).forEach(function (k) {
            decks[k].host.style.aspectRatio = maxed ? "auto" : "";
            if (!maxed) decks[k].host.style.height = "";
        });
        fit();
    }

    window.addEventListener("resize", fit);

    window.addEventListener(
        "click",
        function (e) {
            var link = e.target.closest && e.target.closest("[data-deck]");
            if (!link) return;
            e.preventDefault();
            e.stopPropagation();
            var key = link.getAttribute("data-deck-key");
            if (!decks[key]) {
                var d = build(key);
                if (!d) return;
                decks[key] = d;
            }
            Object.keys(decks).forEach(function (k) {
                decks[k].host.hidden = k !== key;
            });
            cur = decks[key];
            heading.textContent = link.getAttribute("data-deck-title") || defaultTitle;
            win.showModal();
            go(cur.i);
            requestAnimationFrame(fit);
        },
        true,
    );

    document.addEventListener("keydown", function (e) {
        if (!win.open || !cur) return;
        var k = e.key;
        if (k === "ArrowRight" || k === "PageDown" || k === " ") {
            go(cur.i + 1);
            e.preventDefault();
        } else if (k === "ArrowLeft" || k === "PageUp") {
            go(cur.i - 1);
            e.preventDefault();
        } else if (k === "Home") {
            go(0);
        } else if (k === "End") {
            go(cur.slides.length - 1);
        } else if (k === "n" || k === "N") {
            cur.body.classList.toggle("show-notes");
            fit();
        } else if (k === "f" || k === "F") {
            toggleMax();
        }
    });
})();
