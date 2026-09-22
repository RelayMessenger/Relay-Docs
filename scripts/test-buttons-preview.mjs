// Start `mintlify dev --no-open`, then:
// node scripts/test-buttons-preview.mjs http://127.0.0.1:3000 /outside/docs/evidence
// PUPPETEER_EXECUTABLE_PATH can select an already installed Chrome.
import assert from "node:assert/strict";
import { mkdir, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import puppeteer from "puppeteer";

const origin = new URL(process.argv[2] ?? "http://127.0.0.1:3000");
assert.ok(["127.0.0.1", "[::1]"].includes(origin.hostname), "Use a local docs preview.");
assert.ok(process.argv[3], "Supply an evidence directory outside the published docs.");
const output = resolve(process.argv[3]);
await mkdir(output, { recursive: true });
const browser = await puppeteer.launch({ headless: true });
const results = [];
try {
  const page = await browser.newPage();
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.setRequestInterception(true);
  page.on("request", (request) => {
    // No analytics or unrelated remote resource requests during this proof.
    if (new URL(request.url()).origin === origin.origin || request.url().startsWith("data:")) {
      void request.continue();
    } else {
      void request.abort();
    }
  });
  await page.goto(new URL("/interactive-components/buttons", origin).href, {
    waitUntil: "networkidle0", timeout: 120_000,
  });
  await page.waitForSelector(".buttons-preview");
  for (const width of [1280, 390, 320]) {
    for (const theme of ["light", "dark"]) {
      await page.setViewport({ width, height: 1000 });
      // Pin the host appearance first: Mintlify's own theme script reacts to
      // prefers-color-scheme and will overwrite the class we set below, which
      // read the wrong palette on a dark host. Same fix the selection proof
      // already carries.
      await page.emulateMediaFeatures([{ name: "prefers-color-scheme", value: theme }]);
      await page.evaluate((value) => {
        document.documentElement.classList.toggle("dark", value === "dark");
        document.documentElement.style.colorScheme = value;
      }, theme);
      const previews = await page.evaluate(() => [...document.querySelectorAll(".buttons-preview")]
        .filter((element) => element.getBoundingClientRect().height > 0)
        .map((element) => {
          const column = element.querySelector(".buttons-preview-message")?.getBoundingClientRect();
          const pills = [...element.querySelectorAll(".buttons-preview-pill")].map((pill) => {
            const box = pill.getBoundingClientRect();
            const css = getComputedStyle(pill);
            return {
              width: box.width, height: box.height, x: box.x, y: box.y,
              label: pill.querySelector("span").textContent,
              paddingLeft: css.paddingLeft, paddingRight: css.paddingRight,
              radius: css.borderRadius, fill: css.backgroundColor,
              overflow: pill.scrollWidth > pill.clientWidth,
            };
          });
          return {
            text: element.querySelector(".buttons-preview-text")?.textContent ?? null,
            columnWidth: column?.width, columnX: column?.x, pills,
            tap: element.querySelector("svg text")?.textContent ?? null,
            overflow: element.scrollWidth > element.clientWidth,
          };
        }));
      assert.equal(previews.length, 5);
      assert.deepEqual(previews.map((preview) => preview.text), [
        "Which planet has the most moons?", null, null,
        "Connect your Google account to continue.", "Your Q3 report is ready.",
      ]);
      assert.deepEqual(previews.map((preview) => preview.pills.map((pill) => pill.label)), [
        ["Jupiter", "Saturn", "Neptune", "Mars"], ["Continue"], [],
        ["Connect Google"], ["Approve", "Open report"],
      ]);
      assert.equal(previews[2].tap, "Jupiter");
      for (const preview of previews) {
        assert.equal(preview.overflow, false);
        for (const [index, pill] of preview.pills.entries()) {
          assert.ok(Math.abs(pill.width - preview.columnWidth * 0.75) < 1,
            `Pill must use the native 75% cap, not full/content width: ${JSON.stringify(pill)}`);
          assert.ok(Math.abs(pill.width - preview.pills[0].width) < 0.1);
          assert.ok(Math.abs(pill.x - preview.columnX) < 0.1);
          assert.ok(pill.height >= 48);
          assert.equal(pill.paddingLeft, "20px");
          assert.equal(pill.paddingRight, "16px");
          assert.equal(pill.radius, "24px");
          assert.equal(pill.fill, theme === "dark" ? "rgb(16, 30, 51)" : "rgb(238, 245, 255)");
          assert.equal(pill.overflow, false);
          if (index) {
            const previous = preview.pills[index - 1];
            assert.ok(Math.abs(pill.y - previous.y - previous.height - 4) < 0.1);
          }
        }
      }
      const elements = await page.$$(".buttons-preview");
      await elements[0].screenshot({ path: resolve(output, `${theme}-${width}-choices.png`) });
      await elements[1].screenshot({ path: resolve(output, `${theme}-${width}-buttons-only.png`) });
      results.push({ theme, width, previews });
    }
  }
  assert.deepEqual(errors, []);
  await writeFile(resolve(output, "browser-report.json"), JSON.stringify({ status: "passed", results }, null, 2));
  console.log("Passed: native shared-width cap, geometry, colors and request content at three widths in light/dark.");
} finally {
  await browser.close();
}
