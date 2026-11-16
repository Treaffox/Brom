// Rendert Text groß im echten Browser (wie im Tester) und speichert Screenshots.
//   node site/scripts/shot-glyphs.mjs OUT_PREFIX [text] [gewichte]
import { createRequire } from "node:module";
// Playwright aus node_modules neben dem Projekt (npm install) oder aus PLAYWRIGHT_DIR.
const require = createRequire(process.env.PLAYWRIGHT_DIR ? process.env.PLAYWRIGHT_DIR.replace(/\/?$/, "/") : import.meta.url);
const { chromium, firefox } = require("playwright");

const out = process.argv[2];
const text = process.argv[3] || "abcdefghi";
const weights = (process.argv[4] || "400,500,700").split(",");
const BASE = process.env.BASE || `http://localhost:${process.env.PORT || 8080}`;
const local = !process.env.BASE;

for (const [type, name] of [[chromium, "chromium"], [firefox, "firefox"]]) {
  const b = await type.launch();
  const ctx = await b.newContext({ viewport: { width: 1600, height: 420 }, colorScheme: "dark", deviceScaleFactor: 1,
    extraHTTPHeaders: local ? { "X-Forwarded-Proto": "https" } : {} });
  const p = await ctx.newPage();
  await p.goto(BASE + "/", { waitUntil: "networkidle" });
  for (const w of weights) {
    await p.evaluate(([t, w]) => {
      document.body.innerHTML = "";
      const d = document.createElement("div");
      d.textContent = t;
      d.style.fontFamily = '"Brom"'; d.style.fontSize = "300px"; d.style.fontWeight = w;
      d.style.lineHeight = "1.2"; d.style.padding = "0 40px"; d.style.color = "#eceef0"; d.style.background = "#141619";
      document.body.style.margin = "0"; document.body.appendChild(d);
    }, [text, w]);
    await p.evaluate(() => document.fonts.ready);
    await p.screenshot({ path: `${out}-${name}-${w}.png` });
  }
  await b.close();
}
console.log("ok");
