// Render the backglass promo loop to dist/promo.mp4 (1920x1080, 30 s, loops cleanly).
//   node tools/render_promo.js            (needs Playwright + Chromium and ffmpeg)
// Frame-exact: each frame calls the page's promoRender(t) and takes a screenshot,
// so the video matches what the backglass page plays live. Use it on other booth
// screens, socials, or add it to backglass/media/playlist.js.
const fs = require("fs");
const http = require("http");
const os = require("os");
const path = require("path");
const { execFileSync } = require("child_process");
const { chromium } = require(process.env.PLAYWRIGHT_PATH || "playwright");

const root = path.resolve(__dirname, "..");
const FPS = +(process.env.FPS || 25);
const SECONDS = 30;
const W = 1920, H = 1080;
const out = path.join(root, "dist", "promo.mp4");
const TYPES = { ".html": "text/html", ".js": "text/javascript", ".png": "image/png", ".ttf": "font/ttf", ".svg": "image/svg+xml" };

// Tiny static server so the page can load the Comfortaa font from the repo
const server = http.createServer((req, res) => {
  const p = path.join(root, decodeURIComponent(req.url.split("?")[0]));
  if (!p.startsWith(root) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { "Content-Type": TYPES[path.extname(p)] || "application/octet-stream" });
  fs.createReadStream(p).pipe(res);
});

(async () => {
  await new Promise(r => server.listen(0, "127.0.0.1", r));
  const port = server.address().port;
  const frames = fs.mkdtempSync(path.join(os.tmpdir(), "tt-promo-"));
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: W, height: H } });
  await page.goto(`http://127.0.0.1:${port}/backglass/index.html?promo=1&export=1`);
  await page.waitForFunction("typeof window.promoRender === 'function'");
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(700);   // let the promo layer finish fading in
  const total = FPS * SECONDS;
  for (let n = 0; n < total; n++) {
    await page.evaluate(t => window.promoRender(t), n / FPS);
    await page.screenshot({ path: path.join(frames, `f${String(n).padStart(5, "0")}.png`) });
    if (n % (FPS * 5) === 0) console.log(`frame ${n}/${total}`);
  }
  await browser.close();
  server.close();
  fs.mkdirSync(path.dirname(out), { recursive: true });
  execFileSync("ffmpeg", ["-y", "-loglevel", "error", "-framerate", String(FPS), "-i", path.join(frames, "f%05d.png"),
    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-movflags", "+faststart", out], { stdio: "inherit" });
  fs.rmSync(frames, { recursive: true, force: true });
  console.log("wrote", path.relative(root, out));
})();
