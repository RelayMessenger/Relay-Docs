// Manual local Mintlify proof. Never opens a hosted site or a provider API.
import assert from "node:assert/strict";
import { mkdir, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import puppeteer from "puppeteer";

const url = new URL(process.argv[2] ?? "http://localhost:3108/integrations/index");
assert(["localhost", "127.0.0.1"].includes(url.hostname), "Use a local Mintlify preview");
assert.equal(url.protocol, "http:");
assert(!url.username && !url.password, "Credentials are not accepted");
const output = process.argv[3] && resolve(process.argv[3]);
if (output) await mkdir(output, { recursive: true });
const browser = await puppeteer.launch({
  headless: true,
  ...(process.env.PUPPETEER_EXECUTABLE_PATH
    ? { executablePath: process.env.PUPPETEER_EXECUTABLE_PATH } : {}),
  args: ["--mute-audio"],
});
const receipts = [];
try {
  const page = await browser.newPage();
  await page.setRequestInterception(true);
  page.on("request", (request) => {
    // Docs fonts and static assets may load; analytics and writes may not.
    if (request.method() !== "GET" || /posthog|ingest|analytics|telemetry/.test(request.url())) {
      return request.abort();
    }
    return request.continue();
  });
  for (const [name, width, height, dark] of [
    ["desktop", 1440, 1080, false],
    ["phone", 390, 844, false],
    ["desktop-dark", 1440, 1080, true],
  ]) {
    await page.setViewport({ width, height, deviceScaleFactor: 1 });
    await page.emulateMediaFeatures([{ name: "prefers-color-scheme", value: dark ? "dark" : "light" }]);
    await page.goto(url.href, { waitUntil: "networkidle2" });
    await page.waitForSelector('a[href="/integrations/pipecat"]');
    await page.evaluate(async () => {
      await document.fonts.ready;
      await Promise.all([...document.images].map((image) => image.decode().catch(() => {})));
    });
    const layout = await page.evaluate(() => ({
      width: innerWidth,
      scrollWidth: document.documentElement.scrollWidth,
      logos: [...document.querySelectorAll('img[src*="/images/brands/"]')].map((image) => ({
        src: image.getAttribute("src"), loaded: image.naturalWidth > 0,
        width: image.getBoundingClientRect().width,
      })),
    }));
    assert.equal(layout.logos.length, 19, "Every integration has a brand mark");
    assert(layout.logos.every((image) => image.loaded && image.width > 0), "All logos render");
    assert(layout.scrollWidth <= width, "No page overflow");
    if (output) {
      await page.screenshot({ path: `${output}/index-${name}.png`, fullPage: true });
      await writeFile(`${output}/index-${name}.html`, await page.content());
    }
    receipts.push({ name, ...layout });

    if (dark) {
      // Draw the actual SVG and its computed theme treatment in the browser.
      // Without the dark-mode treatment these black marks disappear.
      async function lightPixels(brand) {
        return page.evaluate((brand) => {
          const image = document.querySelector(`img[src*="/images/brands/${brand}.svg"]`);
          const style = getComputedStyle(image);
          const canvas = document.createElement("canvas");
          canvas.width = canvas.height = 64;
          const context = canvas.getContext("2d");
          context.fillStyle = "#09090b";
          context.fillRect(0, 0, 64, 64);
          context.fillStyle = style.backgroundColor;
          context.fillRect(0, 0, 64, 64);
          context.filter = style.filter;
          context.drawImage(image, 0, 0, 64, 64);
          const pixels = context.getImageData(0, 0, 64, 64).data;
          let light = 0;
          for (let i = 0; i < pixels.length; i += 4) {
            if (Math.min(pixels[i], pixels[i + 1], pixels[i + 2]) > 180) light++;
          }
          return light;
        }, brand);
      }
      for (const brand of ["pipecat", "elevenlabs", "livekit"]) {
        const before = await lightPixels(brand);
        assert(before > 5, `${brand}: visible on dark`);
        await page.evaluate((brand) => {
          const image = document.querySelector(`img[src*="/images/brands/${brand}.svg"]`);
          image.style.filter = "none";
          image.style.background = "transparent";
        }, brand);
        const mutated = await lightPixels(brand);
        assert(mutated <= 5, `${brand}: the visibility test must catch the missing theme treatment`);
        await page.evaluate((brand) => {
          const image = document.querySelector(`img[src*="/images/brands/${brand}.svg"]`);
          image.style.removeProperty("filter");
          image.style.removeProperty("background");
        }, brand);
        const restored = await lightPixels(brand);
        assert(restored > 5, `${brand}: restored visibility`);
        receipts.push({ mutation: `${brand}-dark-treatment`, before, mutated, restored });
      }
    }
  }
  if (output) await writeFile(`${output}/render-results.json`, JSON.stringify(receipts, null, 2) + "\n");
  console.log("PASS: 19 logos, desktop/phone/dark, no overflow; 3 dark-theme mutations caught");
} finally {
  await browser.close();
}
