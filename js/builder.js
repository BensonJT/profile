/* ============================================================
   Jeffrey Benson — builder.js
   AI Builder page only. Same conventions as site.js: no framework,
   no CDN, ES5-style so it can be pasted into site.js on merge.

   How the popups work:
     Each .build card, .feature block, or .tile holds two hidden blocks:
       <div class="build__panel" data-panel="how">  ...  </div>
       <div class="build__panel" data-panel="docs"> ...  </div>
     A button with data-open="how" or data-open="docs" copies that
     block into the one shared <dialog> and opens it. Content stays in
     the HTML, next to the card it belongs to, so editing a build means
     editing one place.
   ============================================================ */
(function () {
    "use strict";

    var sheet = document.querySelector("[data-sheet]");
    if (!sheet || typeof sheet.showModal !== "function") return;

    var kindEl = sheet.querySelector("[data-sheet-kind]");
    var titleEl = sheet.querySelector("[data-sheet-title]");
    var bodyEl = sheet.querySelector("[data-sheet-body]");
    var LABELS = { how: "How I built this", docs: "Documentation", auto: "What is automated", charts: "Charts" };

    document.addEventListener("click", function (e) {
        // Match only the popup buttons: the nav drawer also carries a data-open attribute.
        var btn = e.target.closest('[data-open="how"], [data-open="docs"], [data-open="auto"], [data-open="charts"]');
        if (!btn) return;
        var card = btn.closest(".build, .feature, .tile");
        if (!card) return;
        var kind = btn.getAttribute("data-open");
        var panel = card.querySelector('[data-panel="' + kind + '"]');
        var content = panel ? panel.innerHTML.trim() : "";

        kindEl.textContent = LABELS[kind] || "";
        titleEl.textContent = card.querySelector(".build__title, .feature__title, .tile__label").textContent;
        bodyEl.innerHTML = content || '<p class="sheet__empty">Write-up coming when this build ships.</p>';
        sheet.showModal();
    });

    // Close on the Close button, or a click on the dimmed backdrop
    sheet.querySelector("[data-sheet-close]").addEventListener("click", function () {
        sheet.close();
    });
    sheet.addEventListener("click", function (e) {
        if (e.target === sheet) sheet.close();
    });
})();

/* Presentation window: links marked data-deck open their deck (href) in a full-screen dialog, titled
   from data-deck-title (default: the dialog's own title, the Build 06 deck). One frame per deck, kept
   after first open. The frame element is created here, not written in the HTML, because Leland's
   publisher strips frame tags; in the single-file bundle scripts/deck_inline.js handles the links instead. */
(function () {
    "use strict";

    var win = document.querySelector("[data-deck-sheet]");
    if (!win || typeof win.showModal !== "function") return;
    var slot = win.querySelector("[data-deck-slot]");
    var heading = win.querySelector(".sheet__title");
    var defaultTitle = heading.textContent;
    var frames = {};

    function load(href, name) {
        var frame = document.createElement("iframe");
        frame.className = "deck__frame";
        frame.title = "Presentation: " + name;
        frame.addEventListener("load", function () {
            try {
                frame.contentWindow.focus();
            } catch (err) {
                /* focus is best effort */
            }
        });
        frame.src = href;
        slot.appendChild(frame);
        return frame;
    }

    document.addEventListener("click", function (e) {
        var link = e.target.closest("[data-deck]");
        if (!link) return;
        e.preventDefault();
        var href = link.getAttribute("href");
        var name = link.getAttribute("data-deck-title") || defaultTitle;
        heading.textContent = name;
        Object.keys(frames).forEach(function (k) {
            frames[k].hidden = k !== href;
        });
        if (!frames[href]) frames[href] = load(href, name);
        win.showModal();
        frames[href].focus();
    });
    win.querySelector("[data-deck-close]").addEventListener("click", function () {
        win.close();
    });
    win.addEventListener("click", function (e) {
        if (e.target === win) win.close();
    });
})();

/* Evaluation timeline (#evaluation, "How the practice grew"): the index beside one story at a time.
   Without JS the index is a table of contents over all seven stacked stories. A "How I evaluate it"
   link on a project card selects that story and scrolls to the timeline. */
(function () {
    "use strict";

    var root = document.querySelector("[data-practice]");
    if (!root) return;
    var panels = [].slice.call(root.querySelectorAll(".practice__panel"));
    var links = [].slice.call(root.querySelectorAll(".practice__item"));
    var step = root.querySelector("[data-practice-step]");
    var prev = root.querySelector("[data-practice-prev]");
    var next = root.querySelector("[data-practice-next]");
    var heading = root.previousElementSibling;
    var narrow = window.matchMedia("(max-width: 899px)");
    var current = 0;

    function find(id) {
        for (var i = 0; i < panels.length; i++) if (panels[i].id === id) return i;
        return -1;
    }
    function toTimeline() {
        (heading || root).scrollIntoView({ block: "start" });
    }
    function show(i) {
        current = i;
        panels.forEach(function (p, k) {
            p.hidden = k !== i;
        });
        links.forEach(function (a, k) {
            if (k === i) a.setAttribute("aria-current", "true");
            else a.removeAttribute("aria-current");
        });
        prev.disabled = i === 0;
        next.disabled = i === panels.length - 1;
        if (narrow.matches) {
            // Slide the chip row so the selected chip leads it, without scrolling the page
            var row = links[i].closest("ol");
            row.scrollLeft += links[i].getBoundingClientRect().left - row.getBoundingClientRect().left;
        }
    }
    function go(i) {
        show(i);
        try {
            history.replaceState(null, "", "#" + panels[i].id);
        } catch (err) {
            /* single-file hosts may refuse; the story still shows */
        }
        // A long story can leave the reader below the next one's top: bring the timeline back into view
        if (panels[i].getBoundingClientRect().top < 0) toTimeline();
    }

    root.classList.add("practice--js");
    step.hidden = false;

    // Window + capture phase: Leland injects a document-level capture listener that swallows every "#" link
    // click (stopImmediatePropagation) and scrolls instead (seen 2026-10-26). Ours must run first.
    window.addEventListener(
        "click",
        function (e) {
            var a = e.target.closest && e.target.closest('a[href^="#eval-"]');
            if (!a) return;
            var i = find(a.getAttribute("href").slice(1));
            if (i < 0) return;
            e.preventDefault();
            e.stopPropagation();
            go(i);
            if (!root.contains(a)) toTimeline();
        },
        true,
    );
    prev.addEventListener("click", function () {
        if (current > 0) go(current - 1);
    });
    next.addEventListener("click", function () {
        if (current < panels.length - 1) go(current + 1);
    });
    window.addEventListener("hashchange", function () {
        var i = find(location.hash.slice(1));
        if (i >= 0) {
            show(i);
            toTimeline();
        }
    });

    var start = find(location.hash.slice(1));
    show(start >= 0 ? start : 0);
    if (start >= 0) requestAnimationFrame(toTimeline);
})();
