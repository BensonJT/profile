/* Cornerstone page script. No framework, no CDN; the page reads fine with JS off. */
(function () {
    "use strict";

    /* ---- Config: set CAL_URL to the scheduling link when you have one. ----
       While empty, "Book a time" buttons simply scroll to the contact form. */
    var CAL_URL = "https://cal.com/jeffrey-benson-maom/intro?overlayCalendar=true";

    /* ---- Nav turns solid after the hero ---- */
    var nav = document.querySelector("[data-nav]");
    function onScroll() {
        if (nav) nav.setAttribute("data-solid", String(window.scrollY > 40));
    }
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });

    /* ---- Reveal on scroll ---- */
    var items = document.querySelectorAll(".reveal");
    if ("IntersectionObserver" in window) {
        var io = new IntersectionObserver(
            function (entries) {
                entries.forEach(function (e) {
                    if (e.isIntersecting) {
                        e.target.classList.add("is-in");
                        io.unobserve(e.target);
                    }
                });
            },
            { threshold: 0.12 },
        );
        items.forEach(function (el) {
            io.observe(el);
        });
    } else {
        items.forEach(function (el) {
            el.classList.add("is-in");
        });
    }

    /* ---- Hero video: respect reduced motion (the poster still shows) ---- */
    var hv = document.querySelector("[data-hero-video]");
    if (hv && window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
        hv.removeAttribute("autoplay");
        hv.pause();
    }

    /* ---- Recommendations strip: arrow buttons (the strip also scrolls by touch, wheel and keys) ---- */
    var strip = document.querySelector("[data-strip]");
    var sPrev = document.querySelector("[data-strip-prev]");
    var sNext = document.querySelector("[data-strip-next]");
    if (strip && sPrev && sNext) {
        var slow = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
        var stripStep = function () {
            var card = strip.querySelector(".voice");
            var gap = parseFloat(getComputedStyle(strip).columnGap) || 0;
            return card ? card.getBoundingClientRect().width + gap : strip.clientWidth * 0.8;
        };
        var stripUpdate = function () {
            sPrev.disabled = strip.scrollLeft <= 2;
            sNext.disabled = strip.scrollLeft + strip.clientWidth >= strip.scrollWidth - 2;
        };
        sPrev.addEventListener("click", function () {
            strip.scrollBy({ left: -stripStep(), behavior: slow ? "auto" : "smooth" });
        });
        sNext.addEventListener("click", function () {
            strip.scrollBy({ left: stripStep(), behavior: slow ? "auto" : "smooth" });
        });
        strip.addEventListener("scroll", stripUpdate, { passive: true });
        window.addEventListener("resize", stripUpdate);
        stripUpdate();
    }

    /* ---- Calendar button ---- */
    var cal = document.querySelector("[data-cal]");
    if (cal) {
        if (CAL_URL) {
            cal.href = CAL_URL;
            cal.target = "_blank";
            cal.rel = "noopener noreferrer";
        } else {
            cal.hidden = true; /* no link yet: the form is the only path */
        }
    }

    /* ---- Contact form -> personal email via a form-relay service ----
       The relay holds the destination address, so it never appears on the page. */
    var form = document.querySelector("[data-form]");
    var status = document.querySelector("[data-status]");
    if (form && status) {
        var key = form.querySelector('[name="access_key"]').value;
        form.addEventListener("submit", function (ev) {
            ev.preventDefault();
            if (key.indexOf("REPLACE") === 0) {
                status.textContent = "Form not connected yet (preview only).";
                return;
            }
            status.textContent = "Sending…";
            fetch(form.action, {
                method: "POST",
                headers: { Accept: "application/json" },
                body: new FormData(form),
            })
                .then(function (r) {
                    return r.json();
                })
                .then(function (j) {
                    if (j.success) {
                        status.textContent = "Thank you. I’ll be in touch soon.";
                        form.reset();
                    } else {
                        status.textContent = "That didn’t go through. Please try again.";
                    }
                })
                .catch(function () {
                    status.textContent = "That didn’t go through. Please try again.";
                });
        });
    }
})();
