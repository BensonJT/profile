/* ============================================================
   Leland-only outside-link helper. build_single.py adds this script
   to the single-file bundle; the multi-file site never loads it.

   Why: Leland shows the page in <iframe sandbox="allow-scripts">, with
   no allow-popups or allow-top-navigation, so every link to another
   site (the demo video, GitHub, LinkedIn) does nothing when clicked.
   This script catches those clicks and opens a small dialog with the
   address selected and a Copy button, so a reviewer can paste it into
   a new tab. Links inside the page (#anchors, decks) are untouched.

   Colors use the system Canvas/CanvasText pair, so the dialog reads in
   light and dark without depending on the site's tokens.
   ============================================================ */
(function () {
    "use strict";

    var box = document.createElement("dialog");
    if (typeof box.showModal !== "function") return;
    box.setAttribute("aria-label", "Link address");
    // margin:auto re-centers the modal; the site's reset sets dialog margins to 0
    box.style.cssText = "margin:auto;max-width:min(36rem,calc(100vw - 2rem));padding:1.25rem;border:1px solid;" +
        "border-radius:12px;background:Canvas;color:CanvasText;font:inherit;";
    box.innerHTML =
        '<p style="margin:0 0 .75rem">This viewer blocks links to other sites. ' +
        'Copy the address and open it in a new tab:</p>' +
        '<input type="text" readonly style="width:100%;box-sizing:border-box;padding:.5rem;' +
        'font:inherit;border:1px solid;border-radius:6px;background:Canvas;color:CanvasText">' +
        '<div style="display:flex;gap:.5rem;justify-content:flex-end;margin-top:.75rem">' +
        '<span data-msg style="margin-right:auto;align-self:center" aria-live="polite"></span>' +
        '<button type="button" data-copy>Copy</button>' +
        '<button type="button" data-close>Close</button></div>';
    document.body.appendChild(box);

    var field = box.querySelector("input");
    var msg = box.querySelector("[data-msg]");

    box.querySelector("[data-close]").addEventListener("click", function () { box.close(); });
    box.addEventListener("click", function (e) { if (e.target === box) box.close(); });
    box.querySelector("[data-copy]").addEventListener("click", function () {
        field.focus();
        field.select();
        var done = false;
        try { done = document.execCommand("copy"); } catch (err) { done = false; }
        msg.textContent = done ? "Copied." : "Press Ctrl+C (Cmd+C on a Mac) to copy.";
    });

    document.addEventListener("click", function (e) {
        var a = e.target.closest && e.target.closest('a[href^="http://"], a[href^="https://"]');
        if (!a) return;
        e.preventDefault();
        field.value = a.href;
        msg.textContent = "";
        box.showModal();
        field.focus();
        field.select();
    }, true);
})();
