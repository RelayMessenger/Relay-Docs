// Run only in an owned Daytona Linux sandbox. T3 is the first browser check;
// this repeatable viewport test also covers its unavailable resize operation.
import assert from "node:assert/strict";
import puppeteer from "puppeteer";

assert.equal(process.platform, "linux", "Run browser tests in Daytona, not on the shared Mac.");
assert.ok(process.env.DOCS_PREVIEW_URL, "Set DOCS_PREVIEW_URL to the owned preview.");
const origin = new URL(process.env.DOCS_PREVIEW_URL).origin;
const browser = await puppeteer.launch({
  executablePath: process.env.PUPPETEER_EXECUTABLE_PATH || "/usr/bin/chromium",
  headless: true, args: ["--no-sandbox"],
});
const page = await browser.newPage();
const errors = [];
page.on("pageerror", (error) => errors.push(error.message));
const receipts = [];
const clickText = async (selector, label) => {
  await page.evaluate(({ selector, label }) => {
    const control = [...document.querySelectorAll(selector)].find((node) => node.textContent.trim() === label);
    if (!control || control.disabled) throw new Error(`Missing or disabled ${label}`);
    control.click();
  }, { selector, label });
};
const theme = async (dark) => page.evaluate((dark) => document.documentElement.classList.toggle("dark", dark), dark);
const open = async (path, width, dark) => {
  await page.setViewport({ width, height: 900 });
  await page.goto(origin + path, { waitUntil: "networkidle2" });
  await theme(dark);
};
try {
  for (const width of [1280, 390, 320]) {
    for (const dark of [false, true]) {
      await open("/integrations", width, dark);
      await page.waitForSelector('img[src*="/images/brands/mcp.svg"]');
      const directory = await page.evaluate(() => {
        const logo = document.querySelector('img[src*="/images/brands/mcp.svg"]');
        const rect = logo.getBoundingClientRect();
        const noLogoTitles = ["Your own backend", "Agent prompt", "Skills"];
        return {
          mcpLoaded: logo.complete && logo.naturalWidth > 0,
          mcpWidth: rect.width, mcpHeight: rect.height,
          primary: getComputedStyle(document.documentElement).getPropertyValue("--primary").trim(),
          noLogoRows: noLogoTitles.every((title) => {
            const heading = [...document.querySelectorAll('[data-component-part="card-title"]')].find((node) => node.textContent === title);
            return heading && !heading.closest("a")?.querySelector("img");
          }),
        };
      });
      assert.ok(directory.mcpLoaded);
      assert.equal(directory.mcpWidth, 24);
      assert.equal(directory.mcpHeight, 24);
      assert.equal(directory.primary, "0 107 230");
      assert.ok(directory.noLogoRows);
      await open("/interactions/rich-cards", width, dark);
      await page.waitForSelector(".rich-preview .native-capsule");
      const metrics = await page.evaluate(() => {
        const card = document.querySelector(".rich-card");
        const button = card.querySelector(".native-capsule");
        return {
          width: card.getBoundingClientRect().width,
          column: document.querySelector(".native-transcript").getBoundingClientRect().width,
          mediaHeight: card.querySelector(".rich-media").getBoundingClientRect().height,
          buttonHeight: button.getBoundingClientRect().height,
          color: getComputedStyle(button).backgroundColor,
          imageLoaded: card.querySelector("img").naturalWidth > 0,
          pageOverflow: document.documentElement.scrollWidth > innerWidth,
        };
      });
      assert.ok(Math.abs(metrics.width - Math.min(350, metrics.column - 126)) < 1, JSON.stringify(metrics));
      assert.equal(metrics.mediaHeight, 168);
      assert.equal(metrics.buttonHeight, 40);
      assert.equal(metrics.color, dark ? "rgb(0, 126, 255)" : "rgb(11, 117, 255)");
      assert.ok(metrics.imageLoaded);
      assert.equal(metrics.pageOverflow, false);
      await page.click('.rich-preview .rich-suggestions button:nth-child(2)');
      await page.waitForSelector(".rich-preview dialog[open]");
      assert.equal(await page.$(".rich-preview .native-response"), null, "URL actions must not create replies");
      await page.keyboard.press("Escape");
      await page.waitForSelector(".rich-preview dialog[open]", { hidden: true });
      await page.click('.rich-preview .rich-suggestions button');
      await page.waitForSelector(".rich-preview .native-response pre");
      const reply = await page.$eval(".rich-preview .native-response pre", (node) => JSON.parse(node.textContent));
      assert.equal(reply.parts[1].id, "book_lagoon");
      const carousel = await page.$$(".rich-preview");
      assert.equal(carousel.length, 2);
      const shelf = await carousel[1].$eval(".rich-shelf", (node) => ({
        scrollable: node.scrollWidth > node.clientWidth,
        heights: [...node.querySelectorAll(".rich-card")].map((card) => card.getBoundingClientRect().height),
      }));
      assert.ok(shelf.scrollable);
      assert.equal(shelf.heights[0], shelf.heights[1]);

      await open("/interactions/form", width, dark);
      await page.waitForSelector(".native-form-prompt");
      await page.click(".native-form-prompt");
      await page.waitForSelector(".native-form-sheet[open]");
      await clickText(".native-form-bottom button", "Continue");
      await page.waitForSelector('input[aria-label="Name"]');
      assert.ok(await page.$eval(".native-form-bottom button", (button) => button.disabled));
      await page.focus('input[aria-label="Name"]');
      const focus = await page.$eval('input[aria-label="Name"]', (input) => ({
        field: getComputedStyle(input).outlineOffset,
        group: getComputedStyle(input.closest(".native-field-group")).outlineStyle,
      }));
      assert.equal(focus.group, "solid");
      assert.equal(focus.field, "-3px");
      await page.type('input[aria-label="Name"]', "Ada");
      await clickText(".form-choice", "Vegetarian");
      await clickText(".form-choice", "Cake");
      await clickText(".form-choice", "Tea");
      await clickText(".native-form-bottom button", "Next");
      await page.waitForSelector(".form-date");
      await page.select('select[aria-label="Region"]', "east");
      await page.click(".form-date");
      await page.waitForSelector(".form-calendar");
      assert.ok(await page.$eval(".native-form-bottom button", (button) => button.disabled));
      for (let attempt = 0; attempt < 3 && !(await page.$('[aria-label="2026-10-02"]')); attempt++) {
        await page.click('[aria-label="Previous month"]');
      }
      await page.click('[aria-label="2026-10-02"]');
      assert.equal(await page.$eval(".form-date", (node) => node.getAttribute("aria-label")), "Visit date, Oct 2, 2026");
      await page.type('textarea[aria-label="Notes"]', "Window seat, please.");
      await page.click('[role="switch"]');
      await clickText(".native-form-bottom button", "Next");
      await page.waitForSelector(".form-answer-row");
      await clickText(".native-form-bottom button", "Send");
      await page.waitForSelector(".native-form-answer");
      const response = await page.$eval(".native-response pre", (node) => JSON.parse(node.textContent));
      assert.deepEqual(response.parts[1].answers.extras, ["tea", "cake"]);
      const bubbles = await page.$$eval(".form-preview .selection-card", (items) => items.map((svg) => {
        const width = Number(svg.getAttribute("width"));
        return {
          width,
          overflow: [...svg.querySelectorAll("text")].some((text) => text.getBBox().x + text.getBBox().width > width - 30),
          subtitleFill: getComputedStyle(svg.querySelector(".selection-card-subtitle")).fill,
        };
      }));
      assert.ok(bubbles.every((bubble) => !bubble.overflow), JSON.stringify(bubbles));
      assert.equal(bubbles[1].subtitleFill, dark ? "rgba(255, 255, 255, 0.6)" : "rgba(255, 255, 255, 0.8)");
      await page.click(".native-form-answer");
      await page.waitForSelector(".native-form-sheet[open]");
      assert.equal((await page.$$(".native-form-sheet input, .native-form-sheet textarea, .native-form-sheet select")).length, 0);
      assert.equal(await page.$(".native-form-bottom"), null);
      const dialog = await page.$eval(".native-form-sheet", (node) => ({
        width: node.getBoundingClientRect().width,
        overflow: node.scrollWidth > node.clientWidth,
        focusedInside: node.contains(document.activeElement),
      }));
      assert.ok(dialog.width <= Math.min(402, width - 24));
      assert.equal(dialog.overflow, false);
      assert.ok(dialog.focusedInside);
      await page.keyboard.press("Escape");
      await page.waitForSelector(".native-form-sheet[open]", { hidden: true });
      assert.ok(await page.$eval(".native-form-answer", (node) => document.activeElement === node));
      receipts.push({ width, theme: dark ? "dark" : "light", directory, card: metrics, bubbles, dialog, checks: "MCP logo, logo separation, reply, URL isolation, carousel, full form, read-only reopen, focus return" });
    }
  }
  assert.deepEqual(errors, []);
  console.log(JSON.stringify({ origin, receipts, pageErrors: errors }, null, 2));
} finally {
  await browser.close();
}
