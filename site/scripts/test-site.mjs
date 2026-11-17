// Brom – Browsertest der Website (Chromium und Firefox).
//   BASE=https://brom.trfx.de node site/scripts/test-site.mjs [Screenshot-Ordner]
// Ohne BASE: http://localhost:$PORT (Standard 8080) mit Header X-Forwarded-Proto: https (Container lokal).
import { createRequire } from "node:module";
// Playwright aus node_modules neben dem Projekt (npm install) oder aus PLAYWRIGHT_DIR.
const require = createRequire(process.env.PLAYWRIGHT_DIR ? process.env.PLAYWRIGHT_DIR.replace(/\/?$/, "/") : import.meta.url);
const { chromium, firefox } = require("playwright");

// PORT=… prüft einen lokal laufenden Container, BASE=https://… die öffentliche Seite.
const BASE = process.env.BASE || `http://localhost:${process.env.PORT || 8080}`;
const SHOTS = process.argv[2] || "";
const local = !process.env.BASE;
let fails = 0, passes = 0;
const ok = (c, m) => { if (c) passes++; else { fails++; console.log("FEHLER:", m); } };

async function run(type, name) {
  const browser = await type.launch();
  for (const [w, h, mobile] of [[1280, 900, false], [390, 844, true], [320, 640, true]]) {
    const ctx = await browser.newContext({
      viewport: { width: w, height: h }, hasTouch: mobile && name === "chromium", isMobile: mobile && name === "chromium",
      extraHTTPHeaders: local ? { "X-Forwarded-Proto": "https" } : {},
    });
    const page = await ctx.newPage();
    const msgs = [];
    page.on("console", (m) => { if (["error", "warning"].includes(m.type())) msgs.push(m.text()); });
    page.on("pageerror", (e) => msgs.push("pageerror: " + e.message));
    const res = await page.goto(BASE + "/", { waitUntil: "networkidle" });
    const tag = `${name} ${w}px`;
    ok(res.status() === 200, `${tag}: Startseite ${res.status()}`);
    await page.evaluate(() => document.fonts.ready);
    const fontsOk = await page.evaluate(() => document.fonts.check('400 16px "Brom"'));
    ok(fontsOk, `${tag}: Webfont nicht geladen`);
    const loaded = await page.evaluate(() => [...document.fonts].filter((f) => f.family.includes("Brom") && f.status === "loaded").length);
    ok(loaded >= 1, `${tag}: keine Brom-Fontdatei geladen (${loaded})`);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    ok(overflow <= 0, `${tag}: horizontaler Überlauf ${overflow}px`);
    // dlig im Titel: [Br] wird zu einem Glyph (Breite kleiner als vier Zeichen)
    const dligW = await page.evaluate(() => { const s = document.querySelector(".hero__title .dlig"); return s.getBoundingClientRect().width / parseFloat(getComputedStyle(s).fontSize); });
    ok(dligW < 1.6, `${tag}: [Br]-Ligatur greift nicht (Breite ${dligW.toFixed(2)} em)`);
    // Codeblöcke in Brom (Browser setzen für pre sonst monospace)
    const preFonts = await page.$$eval("pre, code", (es) => es.map((e) => getComputedStyle(e).fontFamily));
    ok(preFonts.length > 0 && preFonts.every((f) => f.includes("Brom")), `${tag}: pre/code nicht in Brom (${[...new Set(preFonts)]})`);
    // Tester
    await page.locator('[data-ctl="wght"]').fill("900");
    const tw = await page.evaluate(() => getComputedStyle(document.querySelector(".tester__text")).fontWeight);
    ok(tw === "900", `${tag}: Tester-Gewicht ${tw}`);
    await page.locator('[data-ctl="italic"]').check();
    ok(await page.evaluate(() => getComputedStyle(document.querySelector(".tester__text")).fontStyle) === "italic", `${tag}: Kursiv im Tester`);
    await page.evaluate(() => document.fonts.ready);
    const itl = await page.evaluate(() => [...document.fonts].some((f) => f.family.includes("Brom") && f.style === "italic" && f.status === "loaded"));
    ok(itl, `${tag}: kursive Schriftdatei nicht geladen`);
    await page.locator('.chip:has([data-feature="ss02"])').click();
    const ff = await page.evaluate(() => getComputedStyle(document.querySelector(".tester__text")).fontFeatureSettings);
    ok(ff.includes("ss02"), `${tag}: Feature ss02 nicht gesetzt (${ff})`);
    await page.selectOption('[data-ctl="text"]', "ru");
    ok((await page.locator(".tester__text").textContent()).startsWith("Бром"), `${tag}: Textvorlage`);
    // Zeichen: Filter und Auswahl
    await page.locator('.seg__b[data-filter="griechisch"]').click();
    const vis = await page.evaluate(() => [...document.querySelectorAll(".gblock")].filter((b) => !b.hidden).map((b) => b.dataset.group));
    ok(vis.length > 0 && vis.every((g) => g === "griechisch"), `${tag}: Filter Griechisch (${vis})`);
    await page.locator('.seg__b[data-filter="alle"]').click();
    await page.locator('.g[data-cp="00DF"]').click();
    ok((await page.locator("[data-ginfo-cp]").textContent()) === "U+00DF", `${tag}: Zeicheninfo`);
    // Footer
    const links = await page.$$eval(".foot__links a", (as) => as.map((a) => [a.target, a.rel]));
    ok(links.length === 12 && links.every(([t, r]) => t === "_blank" && r.includes("noopener")), `${tag}: Footer-Links ${links.length}`);
    // GitHub-Verlinkungen (Open Source): Navbar, Hero, Download-Block, Lizenz, Footer, jeweils mit Logo außer Lizenz
    const GH = "https://github.com/Treaffox/Brom";
    const ghs = await page.$$eval("a[href^='https://github.com/Treaffox/Brom']", (as) => as.map((a) => [a.className, a.target, a.rel, !!a.querySelector("svg.gh")]));
    ok(ghs.length >= 8 && ghs.every(([, t, r]) => t === "_blank" && r.includes("noopener")), `${tag}: GitHub-Links ${ghs.length}`);
    for (const c of ["nav__gh", "btn btn--gh", "foot__gh"]) ok(ghs.some(([k, , , svg]) => k === c && svg), `${tag}: GitHub-Link ${c} mit Logo`);
    ok(await page.locator(".nav__gh").isVisible(), `${tag}: GitHub in Navbar sichtbar`);
    ok(await page.locator(".hero__cta .btn--gh").isVisible(), `${tag}: GitHub-Button im Hero sichtbar`);
    ok((await page.locator(".hero__cta .btn").allTextContents()).findIndex((t) => t.includes("GitHub")) === (await page.locator(".hero__cta .btn").allTextContents()).findIndex((t) => t.includes("Ausprobieren")) + 1, `${tag}: GitHub-Button neben Ausprobieren`);
    // Downloads erreichbar
    const hrefs = await page.$$eval('a[download]', (as) => [...new Set(as.map((a) => a.href))]);
    for (const h of hrefs) {
      const r = await ctx.request.get(h);
      ok(r.status() === 200 && Number(r.headers()["content-length"] || (await r.body()).length) > 1000, `${tag}: Download ${h} ${r.status()}`);
    }
    // Feste URLs für Apps (/latest/): erreichbar, CORS offen, no-cache, Versionsnummer passt zur Seite
    const lver = await (await ctx.request.get(BASE + "/latest/version.json")).json();
    const rver = await (await ctx.request.get(BASE + "/version.json")).json();
    ok(lver.version === rver.version, `${tag}: latest/version.json ${lver.version} != version.json ${rver.version}`);
    for (const u of [lver.css, lver.files.upright, lver.files.italic, lver.files.package, "https://brom.trfx.de/latest/version.json"]) {
      const r = await ctx.request.get(BASE + new URL(u).pathname);
      const h = r.headers();
      ok(r.status() === 200 && h["access-control-allow-origin"] === "*" && /no-cache/.test(h["cache-control"] || ""),
        `${tag}: feste URL ${u} ${r.status()} cors=${h["access-control-allow-origin"]} cache=${h["cache-control"]}`);
    }
    const lcss = await (await ctx.request.get(BASE + "/latest/brom.css")).text();
    ok(lcss.includes("Brom-VF.woff2") && lcss.includes("Brom-Italic-VF.woff2"), `${tag}: /latest/brom.css ohne Schriftdateien`);
    ok((await page.locator("#festerlink").textContent()).includes("https://brom.trfx.de/latest/brom.css"), `${tag}: Abschnitt Einbinden nennt den festen Link nicht`);
    ok(msgs.length === 0, `${tag}: Konsole: ${msgs.join(" | ")}`);
    if (SHOTS) {
      await page.evaluate(() => window.scrollTo(0, 0));
      await page.screenshot({ path: `${SHOTS}/${name}-${w}.png`, fullPage: w !== 1280 ? false : false });
      for (const id of ["tester", "gewichte", "prinzip", "zeichen", "festerlink", "download"]) {
        await page.locator("#" + id).scrollIntoViewIfNeeded();
        await page.evaluate((i) => document.getElementById(i).scrollIntoView(), id);
        await page.waitForTimeout(150);
        if (w === 1280 || id === "tester") await page.screenshot({ path: `${SHOTS}/${name}-${w}-${id}.png` });
      }
    }
    await ctx.close();
  }
  // 404
  const ctx = await browser.newContext({ extraHTTPHeaders: local ? { "X-Forwarded-Proto": "https" } : {} });
  const p = await ctx.newPage();
  const r = await p.goto(BASE + "/gibt/es/nicht", { waitUntil: "networkidle" });
  ok(r.status() === 404, `${name}: 404-Seite liefert ${r.status()}`);
  ok(await p.evaluate(() => getComputedStyle(document.body).fontFamily.includes("Brom")), `${name}: 404 ohne CSS`);
  await browser.close();
}

await run(chromium, "chromium");
await run(firefox, "firefox");
console.log(`${passes} bestanden, ${fails} fehlgeschlagen`);
process.exit(fails ? 1 : 0);
