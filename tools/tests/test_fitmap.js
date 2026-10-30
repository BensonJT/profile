// Browser test for the process map (fit-analyzer-map.html): no horizontal scroll at phone or desktop width, no
// console errors, the keys open the right drill-down (1-5, arrows, Esc), deep links work, and with JS off every
// drill-down is visible. Serves the profile repo itself; needs Chrome.
//   npm test  (or: node tools/tests/test_fitmap.js)
const http = require("http");
const fs = require("fs");
const path = require("path");
const { chromium } = require("@playwright/test");

const ROOT = path.resolve(__dirname, "..", "..");
const TYPES = { ".html": "text/html", ".css": "text/css", ".js": "text/javascript", ".woff2": "font/woff2" };
TYPES[".svg"] = "image/svg+xml";

function serve() {
    return new Promise((resolve) => {
        const server = http.createServer((req, res) => {
            const file = path.join(ROOT, decodeURIComponent(req.url.split("?")[0]));
            if (!file.startsWith(ROOT) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) {
                res.writeHead(404);
                res.end();
                return;
            }
            res.writeHead(200, { "Content-Type": TYPES[path.extname(file)] || "application/octet-stream" });
            fs.createReadStream(file).pipe(res);
        });
        server.listen(0, () => resolve(server));
    });
}

(async () => {
    const server = await serve();
    const url = `http://localhost:${server.address().port}/fit-analyzer-map.html`;
    const browser = await chromium.launch();
    const fails = [];
    const check = (ok, what) => {
        console.log(`${ok ? "ok  " : "FAIL"} ${what}`);
        if (!ok) fails.push(what);
    };
    const state = (p) => p.evaluate(() => [document.querySelector(".fm-panel.is-open")?.id, location.hash]);

    for (const width of [375, 1280]) {
        const page = await browser.newPage({ viewport: { width, height: 900 } });
        const errors = [];
        page.on("pageerror", (e) => errors.push(String(e)));
        page.on("console", (m) => m.type() === "error" && errors.push(m.text()));
        await page.goto(url, { waitUntil: "networkidle" });
        const sw = await page.evaluate(() => document.documentElement.scrollWidth);
        check(sw <= width, `${width}px: no horizontal scroll (scrollWidth ${sw})`);
        const shown = await page.$$eval(".fm-fig", (els) => els.filter((e) => e.offsetHeight > 0).length);
        check(shown >= 2, `${width}px: one variant of each figure shows (${shown} visible on load)`);
        check(errors.length === 0, `${width}px: no console errors ${errors.join(" | ")}`);
        await page.close();
    }

    const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    await page.goto(url, { waitUntil: "networkidle" });
    const ids = ["nightly", "validate", "decide", "build", "learn"];
    for (let i = 0; i < ids.length; i++) {
        await page.keyboard.press(String(i + 1));
        await page.waitForTimeout(100);
        check((await state(page))[0] === ids[i], `key ${i + 1} opens #${ids[i]}`);
    }
    await page.keyboard.press("ArrowLeft");
    await page.waitForTimeout(100);
    check((await state(page))[0] === "build", "left arrow moves back one");
    await page.keyboard.press("Escape");
    await page.waitForTimeout(100);
    check((await state(page))[1] === "#map", "Esc returns to the map");
    await page.click('#map .fm-fig--wide a[href="#decide"]');
    await page.waitForTimeout(100);
    check((await state(page))[0] === "decide", "a phase on the map opens its detail");
    await page.goto(url + "#learn", { waitUntil: "networkidle" });
    check((await state(page))[0] === "learn", "a deep link opens its detail");

    const ctx = await browser.newContext({ javaScriptEnabled: false });
    const plain = await ctx.newPage();
    await plain.goto(url);
    const visible = await plain.$$eval(".fm-panel", (els) => els.filter((e) => e.offsetHeight > 0).length);
    check(visible === 5, `JS off: all 5 drill-downs visible (${visible})`);

    await browser.close();
    server.close();
    if (fails.length) {
        console.log(`${fails.length} FAIL`);
        process.exit(1);
    }
})();
