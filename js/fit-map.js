/* ============================================================
   fit-map.js: the drill-downs on fit-analyzer-map.html.
   One panel shows at a time, chosen by the URL hash. Keys: 1-5
   open a panel, left/right move between them, Esc goes back to
   the map. With JS off every panel is visible, stacked.
   ============================================================ */
(function () {
    "use strict";

    var panels = Array.prototype.slice.call(document.querySelectorAll("[data-fm-panel]"));
    var tabs = Array.prototype.slice.call(document.querySelectorAll("[data-fm-tab]"));
    var map = document.getElementById("map");
    if (!panels.length || !map) {
        return;
    }
    document.documentElement.classList.add("fm-js");

    var ids = panels.map(function (p) {
        return p.id;
    });
    var current = ids[0];

    function render(id) {
        current = id;
        panels.forEach(function (p) {
            p.classList.toggle("is-open", p.id === id);
        });
        tabs.forEach(function (t) {
            if (t.getAttribute("href") === "#" + id) {
                t.setAttribute("aria-current", "true");
            } else {
                t.removeAttribute("aria-current");
            }
        });
    }

    /* The browser scrolls to a hash before the panel is shown, so scroll again once it is. */
    function route(scroll) {
        var id = location.hash.slice(1);
        if (ids.indexOf(id) > -1) {
            render(id);
            if (scroll) {
                document.getElementById(id).scrollIntoView({ block: "start" });
            }
        }
    }

    function go(id) {
        if (location.hash === "#" + id) {
            route(true);
        } else {
            location.hash = id;
        }
    }

    render(current);
    route(true);
    window.addEventListener("hashchange", function () {
        route(true);
    });

    document.addEventListener("keydown", function (ev) {
        var t = ev.target;
        if (ev.defaultPrevented || ev.altKey || ev.ctrlKey || ev.metaKey) {
            return;
        }
        if (t && (t.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName))) {
            return;
        }
        var i = ids.indexOf(current);
        var n = parseInt(ev.key, 10);
        if (n >= 1 && n <= ids.length) {
            go(ids[n - 1]);
        } else if (ev.key === "ArrowRight" && i < ids.length - 1) {
            go(ids[i + 1]);
        } else if (ev.key === "ArrowLeft" && i > 0) {
            go(ids[i - 1]);
        } else if (ev.key === "Escape") {
            location.hash = "map";
            map.scrollIntoView({ block: "start" });
        } else {
            return;
        }
        ev.preventDefault();
    });
})();
