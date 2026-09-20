// Local-only browser proof. Run only with explicit browser-test authorization. PUPPETEER_MODULE may name an existing installation.
import assert from 'node:assert/strict';
const { default: puppeteer } = await import(process.env.PUPPETEER_MODULE || 'puppeteer');
const origin = new URL(process.argv[2] || 'http://127.0.0.1:3012');
assert.equal(origin.hostname, '127.0.0.1');
const browser = await puppeteer.launch({ headless: true });
try {
  const page = await browser.newPage();
  // Center controls after viewport changes so the sticky mobile header cannot
  // intercept clicks; allow smooth scrolling and React updates to settle.
  const click = async (target) => {
    const element = typeof target === 'string' ? await page.$(target) : target;
    assert.ok(element, `Missing control: ${target}`);
    await element.evaluate(e => e.scrollIntoView({ block: 'center', inline: 'nearest', behavior: 'instant' }));
    await new Promise(resolve => setTimeout(resolve, 400));
    await element.click();
    await new Promise(resolve => setTimeout(resolve, 100));
  };
  const errors = [];
  const attemptedURLs = [];
  const popups = [];
  page.on('request', request => attemptedURLs.push(request.url()));
  page.on('popup', popup => { popups.push(popup.url()); void popup.close(); });
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
      await click('.selection-option');
      assert.equal(await page.$eval('.selection-option', e => e.getAttribute('aria-pressed')), 'true');
      await new Promise(r => setTimeout(r, 250));
      const style = await page.$eval('.selection-option', e => ({ fill: getComputedStyle(e).backgroundColor, opacity: getComputedStyle(e).opacity, border: getComputedStyle(e).borderWidth, overflow: e.scrollWidth > e.clientWidth }));
      assert.equal(style.fill, dark ? 'rgb(29, 55, 89)' : 'rgb(214, 230, 255)');
      assert.equal(style.opacity, '1');
      assert.equal(style.border, '0px');
      assert.equal(style.overflow, false);
      await click('.selection-actions button:first-child');
      assert.equal(await page.$eval('.selection-actions button:last-child', e => e.disabled), true);
      // Reverse click order must still yield source-option order.
      await click('.selection-option:nth-child(2)');
      await click('.selection-option:nth-child(1)');
      await click('.selection-actions button:last-child');
      await page.waitForSelector('.selection-reply text', { timeout: 3000 });
      assert.equal(await page.$eval('.selection-reply text', e => e.textContent), 'Research, Design');
      assert.equal(await page.$('.selection-option'), null);
      await click('.selection-reset');
      console.log(`PASS selection ${width}px ${dark ? 'dark' : 'light'}`);
    }
  }
  await page.goto(new URL('/interactive-components/buttons', origin).href, { waitUntil: 'networkidle0' });
  await page.waitForSelector('.buttons-preview-tap text');
  assert.equal(await page.$eval('.buttons-preview-tap text', e => e.textContent), 'Jupiter');
  console.log('PASS shared buttons bubble');
  const fixtures = [
    { index: 0, labels: ['Jupiter', 'Saturn', 'Neptune', 'Mars'], plain: 'Jupiter' },
    { index: 1, labels: ['Continue'], plain: 'Continue' },
    { index: 3, labels: ['Connect Google'], url: 'https://accounts.example.com/oauth/authorize' },
    { index: 4, labels: ['Approve', 'Open report'], plain: 'Approve', url: 'https://reports.example.com/q3' },
  ];
  const assertLabels = async (card, labels) => {
    assert.deepEqual(await card.$$eval('.buttons-preview-action', buttons => buttons.map(button =>
      button.querySelector('span')?.textContent.trim() ?? button.textContent.trim())), labels);
    assert.ok(await card.$$eval('.buttons-preview-action', buttons => buttons.every(button =>
      button.tagName === 'BUTTON' && button.type === 'button')));
  };
  for (const width of [1280, 390, 320]) {
    await page.setViewport({ width, height: 1000 });
    for (const dark of [false, true]) {
      await page.evaluate(value => document.documentElement.classList.toggle('dark', value), dark);
      const cards = await page.$$('.buttons-preview');
      assert.equal(cards.length, 5, 'Keep four action examples and the static receive preview');
      for (const fixture of fixtures) {
        const card = cards[fixture.index];
        assert.equal(await card.evaluate(e => e.getAttribute('role')), 'group');
        await assertLabels(card, fixture.labels);
        if (fixture.url) {
          const actions = await card.$$('.buttons-preview-action');
          const before = page.url();
          await click(actions.at(-1));
          await assertLabels(card, fixture.labels); // URL tap consumes nothing.
          const local = await card.$('.buttons-url-preview');
          assert.ok(local);
          assert.equal(await local.evaluate(e => e.getAttribute('role')), 'group');
          assert.equal(await local.evaluate(e => e.getAttribute('aria-label')), 'URL action preview');
          assert.ok((await local.evaluate(e => e.textContent)).includes(fixture.url));
          assert.equal(await local.$('a[href]'), null);
          assert.equal(await card.$('.buttons-reply'), null);
          assert.equal(page.url(), before);
          assert.ok(!attemptedURLs.some(url => url.startsWith(fixture.url)));
          assert.deepEqual(popups, []);
          await click(await card.$('.buttons-url-close'));
          assert.equal(await card.$('.buttons-url-preview'), null);
          await assertLabels(card, fixture.labels);
          if (fixture.plain) await click((await card.$$('.buttons-preview-action')).at(-1));
        }
        if (fixture.plain) {
          const plain = (await card.$$('.buttons-preview-action'))[0];
          await click(plain);
          assert.equal(await card.$('.buttons-preview-action'), null, 'Plain tap hides the entire group, including URL actions');
          assert.equal(await card.$('.buttons-url-preview'), null);
          const reply = await card.$('.buttons-reply');
          assert.ok(reply);
          assert.equal(await reply.evaluate(e => e.getAttribute('role')), 'status');
          assert.equal(await reply.evaluate(e => e.getAttribute('aria-label')), `Reply: ${fixture.plain}`);
          assert.equal(await reply.$eval('svg text', e => e.textContent), fixture.plain);
          await click(await card.$('.buttons-reset'));
          assert.equal(await card.$('.buttons-reply'), null);
          await assertLabels(card, fixture.labels);
        }
      }
      console.log(`PASS buttons plain/URL/mixed/reset ${width}px ${dark ? 'dark' : 'light'}`);
    }
  }
  const native = await page.$('.buttons-preview-action');
  await native.evaluate(e => e.scrollIntoView({ block: 'center', behavior: 'instant' }));
  await new Promise(resolve => setTimeout(resolve, 400));
  const normalBox = await native.boundingBox();
  await page.mouse.move(normalBox.x + normalBox.width / 2, normalBox.y + normalBox.height / 2);
  await page.mouse.down();
  await new Promise(resolve => setTimeout(resolve, 200));
  const pressed = await native.evaluate(e => ({ transform: getComputedStyle(e).transform, opacity: getComputedStyle(e).opacity }));
  assert.notEqual(pressed.transform, 'none');
  assert.equal(pressed.opacity, '1', 'Press changes scale, never opacity');
  await page.mouse.up();
  await page.waitForSelector('.buttons-reset');
  await click('.buttons-reset');
  const keyboardAction = await page.$('.buttons-preview-action');
  await keyboardAction.focus();
  await page.keyboard.press('Enter');
  await page.waitForSelector('.buttons-reply[aria-label="Reply: Jupiter"]');
  await click('.buttons-reset');
  // Reduced motion changes only presentation; the same controls remain usable.
  await page.emulateMediaFeatures([{ name: 'prefers-reduced-motion', value: 'reduce' }]);
  const action = await page.$('.buttons-preview-action');
  await action.evaluate(e => e.scrollIntoView({ block: 'center', behavior: 'instant' }));
  await new Promise(resolve => setTimeout(resolve, 400));
  const box = await action.boundingBox();
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
  await page.mouse.down();
  const reduced = await action.evaluate(e => ({ transform: getComputedStyle(e).transform,
    opacity: getComputedStyle(e).opacity, transition: getComputedStyle(e).transitionDuration }));
  assert.equal(reduced.transform, 'none');
  assert.equal(reduced.opacity, '1');
  assert.equal(reduced.transition, '0s');
  await page.mouse.up();
  assert.deepEqual(errors, []);
} finally { await browser.close(); }
