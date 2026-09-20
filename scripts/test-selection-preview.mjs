// Local-only browser proof. PUPPETEER_MODULE may name an existing installation.
import assert from 'node:assert/strict';
const { default: puppeteer } = await import(process.env.PUPPETEER_MODULE || 'puppeteer');
const origin = new URL(process.argv[2] || 'http://127.0.0.1:3012');
assert.equal(origin.hostname, '127.0.0.1');
const browser = await puppeteer.launch({ headless: true });
try {
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  page.on('console', m => { if (m.type() === 'error' && m.text().includes('component')) errors.push(m.text()); });
  await page.setRequestInterception(true);
  page.on('request', r => new URL(r.url()).origin === origin.origin || r.url().startsWith('data:') ? r.continue() : r.abort());
  await page.goto(new URL('/interactive-components/selection', origin).href, { waitUntil: 'networkidle0', timeout: 120000 });
  await page.waitForSelector('.selection-option', { timeout: 20000 });
  assert.equal(await page.$eval('[aria-label="Selection reply preview"] svg text', e => e.textContent), 'Research, Design');
  for (const width of [1280, 390, 320]) {
    await page.setViewport({ width, height: 1000 });
    for (const dark of [false, true]) {
      await page.evaluate(dark => document.documentElement.classList.toggle('dark', dark), dark);
      assert.equal(await page.$eval('.selection-actions button:last-child', e => e.disabled), true);
      await page.click('.selection-option');
      assert.equal(await page.$eval('.selection-option', e => e.getAttribute('aria-pressed')), 'true');
      await new Promise(r => setTimeout(r, 250));
      const style = await page.$eval('.selection-option', e => ({ fill: getComputedStyle(e).backgroundColor, opacity: getComputedStyle(e).opacity, border: getComputedStyle(e).borderWidth, overflow: e.scrollWidth > e.clientWidth }));
      assert.equal(style.fill, dark ? 'rgb(29, 55, 89)' : 'rgb(214, 230, 255)');
      assert.equal(style.opacity, '1');
      assert.equal(style.border, '0px');
      assert.equal(style.overflow, false);
      await page.click('.selection-actions button:first-child');
      assert.equal(await page.$eval('.selection-actions button:last-child', e => e.disabled), true);
      // Reverse click order must still yield source-option order.
      await page.click('.selection-option:nth-child(2)');
      await page.click('.selection-option:nth-child(1)');
      await page.click('.selection-actions button:last-child');
      await page.waitForSelector('.selection-reply text', { timeout: 3000 });
      assert.equal(await page.$eval('.selection-reply text', e => e.textContent), 'Research, Design');
      assert.equal(await page.$('.selection-option'), null);
      await page.click('.selection-reset');
      console.log(`PASS selection ${width}px ${dark ? 'dark' : 'light'}`);
    }
  }
  await page.goto(new URL('/interactive-components/buttons', origin).href, { waitUntil: 'networkidle0' });
  await page.waitForSelector('.buttons-preview-tap text');
  assert.equal(await page.$eval('.buttons-preview-tap text', e => e.textContent), 'Jupiter');
  console.log('PASS shared buttons bubble');
  assert.deepEqual(errors, []);
} finally { await browser.close(); }
