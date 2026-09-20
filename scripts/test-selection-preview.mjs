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
  assert.deepEqual(await page.$$eval('[aria-label="Selection reply preview"] svg text', rows => rows.map(e => e.textContent)), ['• Research', '• Design']);
  const assertSend = async (dark, disabled) => {
    await new Promise(resolve => setTimeout(resolve, 250));
    const style = await page.$eval('.selection-actions button', e => {
      const pill = e.querySelector('.selection-send-pill');
      const box = e.getBoundingClientRect(), visual = pill.getBoundingClientRect();
      const parent = e.parentElement.getBoundingClientRect();
      const option = [...e.closest('.selection-stack').querySelectorAll('.selection-option')].at(-1).getBoundingClientRect();
      const hitStyle = getComputedStyle(e), visualStyle = getComputedStyle(pill);
      return {
        disabled: e.disabled, width: box.width, height: box.height,
        visualWidth: visual.width, visualHeight: visual.height,
        inset: visual.y - box.y, gap: box.y - option.bottom,
        offset: Math.abs(box.x + box.width / 2 - parent.x - parent.width / 2),
        visualOffset: Math.abs(visual.x + visual.width / 2 - box.x - box.width / 2),
        fill: visualStyle.backgroundColor, color: visualStyle.color,
        fontSize: visualStyle.fontSize, fontWeight: visualStyle.fontWeight,
        hitFill: hitStyle.backgroundColor, opacity: hitStyle.opacity,
        visualOpacity: visualStyle.opacity, transition: visualStyle.transitionProperty,
        duration: visualStyle.transitionDuration,
      };
    });
    assert.equal(style.disabled, disabled);
    assert.deepEqual([style.width, style.height, style.visualWidth, style.visualHeight], [84, 44, 84, 32]);
    assert.ok(Math.abs(style.inset - 6) < .1);
    assert.ok(Math.abs(style.gap - 4) < .1, 'Hit target starts 4px below the last option');
    assert.ok(style.offset < .1 && style.visualOffset < .1, 'Both target and visual are centered');
    assert.equal(style.hitFill, 'rgba(0, 0, 0, 0)');
    const fill = dark ? '20, 45, 77' : '232, 241, 255';
    const color = dark ? '111, 176, 255' : '11, 117, 255';
    assert.equal(style.fill, disabled ? `rgba(${fill}, 0.34)` : `rgb(${fill})`);
    assert.equal(style.color, disabled ? `rgba(${color}, 0.34)` : `rgb(${color})`);
    assert.equal(style.fontSize, '15px');
    assert.equal(style.fontWeight, '600');
    assert.equal(style.opacity, '1');
    assert.equal(style.visualOpacity, '1', 'Only colors dim, not control opacity');
    assert.equal(style.transition, 'background-color, color');
    assert.equal(style.duration, '0.2s, 0.2s');
  };
  for (const width of [1280, 390, 320]) {
    await page.setViewport({ width, height: 1000 });
    for (const dark of [false, true]) {
      await page.evaluate(dark => document.documentElement.classList.toggle('dark', dark), dark);
      assert.deepEqual(await page.$$eval('.selection-actions button', buttons => buttons.map(e => e.textContent.trim())), ['Send']);
      await assertSend(dark, true);
      await click('.selection-option');
      assert.equal(await page.$eval('.selection-option', e => e.getAttribute('aria-pressed')), 'true');
      await assertSend(dark, false);
      await new Promise(r => setTimeout(r, 250));
      const style = await page.$eval('.selection-option', e => ({ fill: getComputedStyle(e).backgroundColor, opacity: getComputedStyle(e).opacity, border: getComputedStyle(e).borderWidth, overflow: e.scrollWidth > e.clientWidth }));
      assert.equal(style.fill, dark ? 'rgb(29, 55, 89)' : 'rgb(214, 230, 255)');
      assert.equal(style.opacity, '1');
      assert.equal(style.border, '0px');
      assert.equal(style.overflow, false);
      await click('.selection-option');
      assert.equal(await page.$eval('.selection-option', e => e.getAttribute('aria-pressed')), 'false');
      assert.equal(await page.$('.selection-reply'), null);
      await assertSend(dark, true);
      // Reverse click order must still yield source-option order.
      await click('.selection-option:nth-child(2)');
      await click('.selection-option:nth-child(1)');
      await assertSend(dark, false);
      const send = await page.$('.selection-actions button');
      await send.evaluate(e => e.scrollIntoView({ block: 'center', behavior: 'instant' }));
      await new Promise(resolve => setTimeout(resolve, 400));
      const box = await send.boundingBox();
      // The transparent top inset belongs to the hit target too.
      await page.mouse.move(box.x + box.width / 2, box.y + 2);
      await page.mouse.down();
      await new Promise(resolve => setTimeout(resolve, 200));
      const pressed = await send.evaluate(e => ({
        scale: new DOMMatrix(getComputedStyle(e).transform).a,
        opacity: getComputedStyle(e).opacity,
      }));
      assert.ok(Math.abs(pressed.scale - .97) < .001);
      assert.equal(pressed.opacity, '1');
      await page.mouse.up();
      await page.waitForSelector('.selection-reply text', { timeout: 3000 });
      assert.deepEqual(await page.$$eval('.selection-reply text', rows => rows.map(e => e.textContent)), ['• Research', '• Design']);
      assert.equal(await page.$eval('.selection-reply', e => e.getAttribute('aria-label')), 'Reply: • Research\n• Design');
      assert.equal(await page.$('.selection-option'), null);
      await click('.selection-reset');
      console.log(`PASS selection ${width}px ${dark ? 'dark' : 'light'}`);
    }
  }
  await page.emulateMediaFeatures([{ name: 'prefers-reduced-motion', value: 'reduce' }]);
  await click('.selection-option');
  const reducedSend = await page.$('.selection-actions button');
  await reducedSend.evaluate(e => e.scrollIntoView({ block: 'center', behavior: 'instant' }));
  await new Promise(resolve => setTimeout(resolve, 400));
  const reducedBox = await reducedSend.boundingBox();
  await page.mouse.move(reducedBox.x + reducedBox.width / 2, reducedBox.y + 2);
  await page.mouse.down();
  assert.deepEqual(await reducedSend.evaluate(e => ({
    transform: getComputedStyle(e).transform,
    opacity: getComputedStyle(e).opacity,
    transition: getComputedStyle(e).transitionDuration,
    colorTransition: getComputedStyle(e.querySelector('.selection-send-pill')).transitionDuration,
  })), { transform: 'none', opacity: '1', transition: '0s', colorTransition: '0s' });
  await page.mouse.up();
  await page.waitForSelector('.selection-reply');
  await click('.selection-reset');
  await page.emulateMediaFeatures([]);
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
