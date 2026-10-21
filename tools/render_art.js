// Render the SVG art sources to PNGs for the table and backglass.
//   node tools/render_art.js      (needs Playwright + the Comfortaa font installed)
// Writes art/render/*.png: concept playfield, table playfield (aligned to the layout), backglass.
const fs = require("fs");
const path = require("path");
const { chromium } = require(process.env.PLAYWRIGHT_PATH || "playwright");

const root = path.resolve(__dirname, "..");
const jobs = [
  { src: "art/playfield.svg", out: "art/render/playfield.png", w: 2048, h: 4300, hide: ["guides"] },
  { src: "art/playfield_table.svg", out: "art/render/playfield_table.png", w: 2048, h: 4652, hide: [] },
  { src: "art/backglass.svg", out: "art/render/backglass.png", w: 1280, h: 1024, hide: [] },
];

(async () => {
  const browser = await chromium.launch();
  for (const j of jobs) {
    let svg = fs.readFileSync(path.join(root, j.src), "utf8");
    for (const id of j.hide) svg = svg.replace(`<g id="${id}"`, `<g id="${id}" display="none"`);
    svg = svg.replace(/width="[\d.]+" height="[\d.]+"/, `width="${j.w}" height="${j.h}"`);
    const page = await browser.newPage({ viewport: { width: j.w, height: j.h } });
    await page.setContent(`<html><body style="margin:0">${svg}</body></html>`);
    await page.evaluate(() => document.fonts.ready);
    await page.screenshot({ path: path.join(root, j.out), clip: { x: 0, y: 0, width: j.w, height: j.h } });
    console.log("wrote", j.out);
  }
  await browser.close();
})();
