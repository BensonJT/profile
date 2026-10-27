// Click-test every Presentation link, on the site (iframe window from builder.js) and in the Leland
// single-file bundle (deck_inline.js, shadow roots). Serves the profile repo itself; needs Chrome.
// Run after tools/leland/build_single.py, from the profile repo:
//   npm test  (or: node tools/tests/test_decks.js [path/to/ai-builder-single.html])
// The bundle defaults to the vault upload copy, else dist/ai-builder-single.html here.
const http = require("http");
const fs = require("fs");
const path = require("path");
const { chromium } = require("@playwright/test");

const ROOT = path.resolve(__dirname, "..", "..");
const VAULT = "/mnt/c/Users/Jeffrey Benson/Documents/keystone/ai-builder/dist/ai-builder-single.html";
const BUNDLE = process.argv[2] || (fs.existsSync(VAULT) ? VAULT : path.join(ROOT, "dist", "ai-builder-single.html"));
const TYPES = {
    ".html": "text/html",
    ".css": "text/css",
    ".js": "text/javascript",
    ".woff2": "font/woff2",
    ".webp": "image/webp",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".pdf": "application/pdf",
};
// [selector, deck title, site page that holds it]
const DECKS = [
    { sel: "#latest [data-deck]", title: "AI value reporting at financial institutions", page: "/ai-builder.html" },
    { sel: "#builds [data-deck]", title: "Where my experience fits", page: "/ai-builder-level1.html" },
];

function serve() {
    return new Promise((resolve) => {
        const server = http.createServer((req, res) => {
            const url = decodeURIComponent(req.url.split("?")[0]);
            const file = url === "/bundle.html" ? BUNDLE : path.join(ROOT, url);
            if (
                (url !== "/bundle.html" && !file.startsWith(ROOT)) ||
                !fs.existsSync(file) ||
                fs.statSync(file).isDirectory()
            ) {
                res.writeHead(404);
                return res.end();
            }
            res.writeHead(200, { "Content-Type": TYPES[path.extname(file)] || "application/octet-stream" });
            fs.createReadStream(file).pipe(res);
        });
        server.listen(0, () => resolve(server));
    });
}

function state(page) {
    return page.evaluate(() => {
        const win = document.querySelector("[data-deck-sheet]");
        const shown = [...document.querySelectorAll(".deck__frame")].filter(
            (f) => getComputedStyle(f).display !== "none",
        );
        const f = shown[0];
        return {
            open: win.open,
            title: win.querySelector(".sheet__title").textContent.trim(),
            shown: shown.length,
            src: f && f.getAttribute("src"),
            slide: f && f.shadowRoot ? (f.shadowRoot.querySelector(".slide.on") || {}).id : null,
        };
    });
}

(async () => {
    const server = await serve();
    const base = `http://localhost:${server.address().port}`;
    const browser = await chromium.launch({ executablePath: "/usr/bin/google-chrome", args: ["--no-sandbox"] });
    const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
    const errors = [];
    page.on("pageerror", (e) => errors.push(e.message));
    let failed = 0;
    const check = (label, ok, got) => {
        console.log(`${ok ? "PASS" : "FAIL"} ${label}${ok ? "" : " " + JSON.stringify(got)}`);
        if (!ok) failed++;
    };

    for (const bundle of [false, true]) {
        const where = bundle ? "bundle" : "site";
        await page.goto(base + (bundle ? "/bundle.html" : "/ai-builder.html"));
        // The PDF download is site-only: present (and a real PDF) on the site, absent in the Leland bundle
        const pdfLinks = await page.locator('#latest a[href$=".pdf"]').count();
        if (bundle) {
            check("bundle has no PDF download link", pdfLinks === 0, pdfLinks);
        } else {
            const [dl] = await Promise.all([
                page.waitForEvent("download"),
                page.locator('#latest a[href$=".pdf"]').click(),
            ]);
            const head = fs
                .readFileSync(await dl.path())
                .subarray(0, 5)
                .toString();
            check(`site PDF download (${dl.suggestedFilename()})`, pdfLinks === 1 && head === "%PDF-", {
                pdfLinks,
                head,
            });
        }
        for (let round = 0; round < 2; round++) {
            for (const d of DECKS) {
                if (!bundle) await page.goto(base + d.page);
                await page.locator(d.sel).first().click();
                await page.waitForTimeout(bundle ? 400 : 1200);
                if (bundle && round === 0) await page.keyboard.press("ArrowRight");
                const s = await state(page);
                check(
                    `${where} round ${round + 1}: ${d.title}`,
                    s.open && s.title === d.title && s.shown === 1 && (!bundle || s.slide === "s2"),
                    s,
                );
                await page.click("[data-deck-close]");
            }
        }
    }
    check("no page errors", errors.length === 0, errors);
    await browser.close();
    server.close();
    process.exit(failed ? 1 : 0);
})();
