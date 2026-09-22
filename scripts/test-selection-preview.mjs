// Local-only browser proof. Run only with explicit browser-test authorization. PUPPETEER_MODULE may name an existing installation.
// Drives the shipped selection flow (Relay-iOS RelaySelectionRow/RelaySelectionSheet):
// nothing is picked in the transcript, the prompt balloon opens a sheet, Send
// posts once, and the answered prompt or its reply reopens that sheet read-only.
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
    await new Promise(resolve => setTimeout(resolve, 150));
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
  // The preview follows the host appearance; pin light so the explicit .dark toggle below is the only variable.
  await page.emulateMediaFeatures([{ name: 'prefers-color-scheme', value: 'light' }]);
  await page.goto(new URL('/interactive-components/selection', origin).href, { waitUntil: 'networkidle0', timeout: 120000 });
  await page.waitForSelector('.selection-prompt', { timeout: 20000 });

  const QUESTION = 'Which topics interest you?';
  const rowsOf = (card, selector) => card.$$eval(`${selector} .selection-card text`, nodes => nodes.map(e => e.textContent));
  const sheetOf = async (card) => {
    const sheet = await card.$('.selection-sheet');
    assert.ok(sheet, 'The sheet must live inside its own preview card');
    return sheet;
  };
  // Every option row: its label, its checked state, whether it is inert, and
  // whether its checkbox really leads the label.
  const optionState = (sheet) => sheet.$$eval('.selection-sheet-option', rows => rows.map(row => {
    const box = row.querySelector('.selection-box').getBoundingClientRect();
    const label = row.querySelector('.selection-sheet-label');
    return {
      label: label.textContent,
      checked: row.getAttribute('aria-checked'),
      role: row.getAttribute('role'),
      disabled: row.disabled,
      leadingCheckbox: box.right <= label.getBoundingClientRect().left,
      icons: row.querySelectorAll('img, .selection-sheet-icon').length,
    };
  }));
  const sendStyle = (sheet) => sheet.$eval('.selection-send', e => {
    const css = getComputedStyle(e);
    const footer = getComputedStyle(e.parentElement);
    const box = e.getBoundingClientRect(), parent = e.parentElement.getBoundingClientRect();
    return {
      text: e.textContent, disabled: e.disabled,
      fill: css.backgroundColor, color: css.color, opacity: css.opacity,
      height: box.height,
      fullWidth: Math.abs(box.width - (parent.width - parseFloat(footer.paddingLeft) - parseFloat(footer.paddingRight))) < 0.5,
      pinnedLast: e.parentElement === e.closest('.selection-sheet').lastElementChild,
    };
  });

  for (const width of [1280, 390, 320]) {
    await page.setViewport({ width, height: 1000 });
    for (const dark of [false, true]) {
      await page.evaluate(value => document.documentElement.classList.toggle('dark', value), dark);
      const label = `${width}px ${dark ? 'dark' : 'light'}`;
      const cards = await page.$$('.selection-preview');
      assert.equal(cards.length, 2, 'Keep the interactive prompt preview and the received reply preview');
      const [live, receivedCard] = cards;

      // 1. The transcript carries one balloon and no pickable option.
      assert.deepEqual(await rowsOf(live, '.selection-prompt'), [QUESTION, 'Pick options']);
      assert.equal(await live.$('.selection-sheet'), null);
      assert.equal(await live.$('.selection-sheet-option'), null, 'Nothing is picked in the transcript');
      assert.equal(await live.$('.selection-answer'), null);
      const promptShape = await live.$eval('.selection-prompt .selection-card', e => {
        const svg = e.getBoundingClientRect();
        const column = e.closest('.buttons-preview-message').getBoundingClientRect();
        return {
          columnWidth: Math.abs(svg.width - column.width) < 1,
          height: e.getAttribute('height'),
          mirrored: e.querySelector('.selection-card-shape').parentElement.getAttribute('transform'),
          chevrons: e.querySelectorAll('.selection-card-chevron').length,
          icons: e.querySelectorAll('image, .selection-card-icon').length,
          marks: e.querySelectorAll('.selection-card-mark').length,
          fill: getComputedStyle(e.querySelector('.selection-card-shape')).fill,
          chevronRight: e.querySelector('.selection-card-chevron').getBoundingClientRect().right
            > e.querySelector('.selection-card-title').getBoundingClientRect().right,
        };
      });
      assert.ok(promptShape.columnWidth, 'The balloon is as wide as a text balloon may be');
      // A 20pt title over a 18pt second line inside 10pt insets is a 60pt
      // body; the extra 7 is the round tail hanging below it (radius 20 x
      // RelayBubbleGeometry's 0.33925 depth factor).
      assert.equal(promptShape.height, '67', 'The balloon keeps its tail below the body');
      assert.match(promptShape.mirrored, /scale\(-1,1\)/, 'An incoming balloon mirrors the tail');
      assert.equal(promptShape.chevrons, 1);
      assert.equal(promptShape.icons, 0, 'The prompt balloon carries no icon');
      assert.equal(promptShape.marks, 0);
      assert.ok(promptShape.chevronRight, 'The chevron sits at the trailing edge');
      assert.equal(promptShape.fill, dark ? 'rgb(36, 43, 54)' : 'rgb(241, 243, 245)');
      assert.equal(await live.$eval('.selection-prompt', e => e.getAttribute('aria-haspopup')), 'dialog');

      // 2. Tapping it opens the sheet.
      await click(await live.$('.selection-prompt'));
      const sheet = await sheetOf(live);
      assert.equal(await page.evaluate(() => document.activeElement.className), 'selection-sheet-grabber');
      assert.equal(await sheet.$eval('.selection-sheet-title', e => e.textContent), QUESTION);
      assert.equal(await sheet.evaluate(e => e.getAttribute('aria-modal')), 'true');
      assert.equal(await sheet.$eval('.selection-sheet-section', e => e.textContent), 'Options');
      const headerGeometry = await sheet.$eval('.selection-sheet-title', e => {
        const css = getComputedStyle(e);
        return { borderBottom: css.borderBottomWidth, next: e.nextElementSibling.className };
      });
      assert.equal(headerGeometry.borderBottom, '0px', 'No separator under the title');
      // The title carries no subtitle; the only thing under it is the pinned
      // "Options" heading, and that heading sits OUTSIDE the scroller so it
      // stays put while the rows move (owner, 2026-09-22).
      assert.equal(headerGeometry.next, 'selection-sheet-section',
        'Only the Options heading follows the title');
      const sectionGeometry = await sheet.$eval('.selection-sheet-section', e => ({
        next: e.nextElementSibling.className,
        insideScroller: Boolean(e.closest('.selection-sheet-list')),
      }));
      assert.equal(sectionGeometry.next, 'selection-sheet-list',
        'The list follows the Options heading');
      assert.equal(sectionGeometry.insideScroller, false,
        'The Options heading must not scroll away with the rows it labels');
      assert.deepEqual(await optionState(sheet), [
        { label: 'Research', checked: 'false', role: 'checkbox', disabled: false, leadingCheckbox: true, icons: 0 },
        { label: 'Design', checked: 'false', role: 'checkbox', disabled: false, leadingCheckbox: true, icons: 0 },
      ]);
      assert.equal(await sheet.$eval('.selection-sheet-list', e => getComputedStyle(e).overflowY), 'auto');

      // 3. Send is disabled until something is checked, and full width at the bottom.
      let send = await sendStyle(sheet);
      assert.equal(send.text, 'Send');
      assert.equal(send.disabled, true);
      assert.ok(send.fullWidth, 'Send spans the sheet');
      assert.ok(send.pinnedLast, 'Send is pinned under the list');
      assert.equal(send.fill, 'rgba(11, 117, 255, 0.32)');
      assert.equal(send.color, 'rgba(255, 255, 255, 0.55)');
      assert.equal(send.opacity, '1', 'Disabled dims the fill, never the control');
      await click(await sheet.$('.selection-sheet-option:nth-of-type(1)'));
      assert.equal((await optionState(sheet))[0].checked, 'true');
      assert.equal(await live.$('.selection-answer'), null, 'Checking sends nothing');
      await click(await sheet.$('.selection-sheet-option:nth-of-type(1)'));
      assert.equal((await optionState(sheet))[0].checked, 'false');
      send = await sendStyle(sheet);
      assert.equal(send.disabled, true);

      // Reverse click order must still yield source-option order.
      await click(await sheet.$('.selection-sheet-option:nth-of-type(2)'));
      await click(await sheet.$('.selection-sheet-option:nth-of-type(1)'));
      send = await sendStyle(sheet);
      assert.equal(send.disabled, false);
      assert.equal(send.fill, 'rgb(11, 117, 255)');
      assert.equal(send.color, 'rgb(255, 255, 255)');
      assert.equal(send.opacity, '1');

      // 4. Press feedback: scale only, never opacity.
      const sendHandle = await sheet.$('.selection-send');
      await sendHandle.evaluate(e => e.scrollIntoView({ block: 'center', behavior: 'instant' }));
      await new Promise(resolve => setTimeout(resolve, 400));
      const sendBox = await sendHandle.boundingBox();
      await page.mouse.move(sendBox.x + sendBox.width / 2, sendBox.y + sendBox.height / 2);
      await page.mouse.down();
      await new Promise(resolve => setTimeout(resolve, 220));
      const pressed = await sendHandle.evaluate(e => ({
        scale: new DOMMatrix(getComputedStyle(e).transform).a,
        opacity: getComputedStyle(e).opacity,
      }));
      assert.ok(Math.abs(pressed.scale - 0.96) < 0.001, `Send compresses on press (${pressed.scale})`);
      assert.equal(pressed.opacity, '1');
      await page.mouse.up();

      // 5. Send dismisses and leaves the reply.
      await page.waitForSelector('.selection-answer', { timeout: 3000 });
      assert.equal(await live.$('.selection-sheet'), null, 'Send dismisses the sheet');
      assert.deepEqual(await rowsOf(live, '.selection-answer'), [QUESTION, 'Research', 'Design']);
      const replyShape = await live.$eval('.selection-answer .selection-card', e => ({
        marks: e.querySelectorAll('.selection-card-mark').length,
        circles: e.querySelectorAll('circle').length,
        dots: [...e.querySelectorAll('text')].filter(t => t.textContent.includes('•')).length,
        mirrored: e.querySelector('.selection-card-shape').parentElement.getAttribute('transform'),
        fill: getComputedStyle(e.querySelector('.selection-card-shape')).fill,
        height: e.getAttribute('height'),
      }));
      assert.equal(replyShape.marks, 2, 'One bare checkmark per chosen label');
      assert.equal(replyShape.circles, 0, 'Not a circle');
      assert.equal(replyShape.dots, 0, 'Not a dot');
      assert.equal(replyShape.mirrored, null, 'An outgoing balloon keeps the trailing tail');
      assert.equal(replyShape.fill, 'rgb(11, 117, 255)');
      // Title plus two label lines is an 85pt body, and the tail hangs below.
      assert.equal(replyShape.height, '92');
      assert.equal(await live.$eval('.selection-answer', e => e.getAttribute('aria-label')),
        `${QUESTION}. Research, Design. Opens the options you chose`);

      // 6. The reply reopens the sheet read-only.
      await click(await live.$('.selection-answer'));
      const readOnly = await sheetOf(live);
      assert.deepEqual(await optionState(readOnly), [
        { label: 'Research', checked: 'true', role: 'checkbox', disabled: true, leadingCheckbox: true, icons: 0 },
        { label: 'Design', checked: 'true', role: 'checkbox', disabled: true, leadingCheckbox: true, icons: 0 },
      ]);
      assert.equal(await readOnly.$('.selection-sheet-footer'), null, 'The footer is absent, not disabled');
      assert.equal(await readOnly.$('.selection-send'), null);
      await page.keyboard.press('Escape');
      await new Promise(resolve => setTimeout(resolve, 150));
      assert.equal(await live.$('.selection-sheet'), null, 'Escape dismisses the sheet');
      assert.equal(await page.evaluate(() => document.activeElement.className), 'selection-answer');

      // 7. The answered prompt reopens the same read-only sheet.
      await click(await live.$('.selection-prompt'));
      const reopened = await sheetOf(live);
      assert.equal(await reopened.$('.selection-sheet-footer'), null);
      assert.deepEqual((await optionState(reopened)).map(row => row.disabled), [true, true]);
      await click(await reopened.$('.selection-sheet-grabber'));
      assert.equal(await live.$('.selection-sheet'), null, 'The grabber dismisses the sheet');
      assert.equal(await page.evaluate(() => document.activeElement.className), 'selection-prompt');

      // 8. The received preview is the reply alone, and it reopens read-only.
      assert.equal(await receivedCard.$('.selection-prompt'), null);
      assert.equal(await receivedCard.$('.selection-reset'), null);
      assert.deepEqual(await rowsOf(receivedCard, '.selection-answer'), [QUESTION, 'Research', 'Design']);
      await click(await receivedCard.$('.selection-answer'));
      const staticSheet = await sheetOf(receivedCard);
      assert.deepEqual((await optionState(staticSheet)).map(row => [row.checked, row.disabled]),
        [['true', true], ['true', true]]);
      assert.equal(await staticSheet.$('.selection-send'), null);
      await page.keyboard.press('Escape');
      await new Promise(resolve => setTimeout(resolve, 150));
      assert.equal(await receivedCard.$('.selection-sheet'), null);

      // 9. Reset returns the live demo to the unanswered prompt.
      await click(await live.$('.selection-reset'));
      assert.equal(await live.$('.selection-answer'), null);
      assert.equal(await live.$('.selection-sheet'), null);
      assert.deepEqual(await rowsOf(live, '.selection-prompt'), [QUESTION, 'Pick options']);
      console.log(`PASS selection ${label}`);
    }
  }

  // Keyboard only: open, check, submit, reopen, reset.
  await page.setViewport({ width: 1280, height: 1000 });
  await page.evaluate(() => document.documentElement.classList.remove('dark'));
  const live = (await page.$$('.selection-preview'))[0];
  await (await live.$('.selection-prompt')).focus();
  await page.keyboard.press('Enter');
  await page.waitForSelector('.selection-sheet');
  await (await live.$('.selection-sheet-option:nth-of-type(1)')).focus();
  await page.keyboard.press('Enter');
  assert.equal(await live.$eval('.selection-sheet-option', e => e.getAttribute('aria-checked')), 'true');
  await (await live.$('.selection-send')).focus();
  await page.keyboard.press('Enter');
  await page.waitForSelector('.selection-answer');
  assert.deepEqual(await live.$$eval('.selection-answer .selection-card text', n => n.map(e => e.textContent)),
    ['Which topics interest you?', 'Research']);
  await (await live.$('.selection-answer')).focus();
  await page.keyboard.press('Enter');
  await page.waitForSelector('.selection-sheet');
  assert.equal(await live.$('.selection-send'), null);
  await page.keyboard.press('Escape');
  await new Promise(resolve => setTimeout(resolve, 150));
  await click(await live.$('.selection-reset'));
  assert.equal(await live.$('.selection-answer'), null);
  console.log('PASS selection keyboard');

  // Reduced motion changes only presentation; the same controls remain usable.
  await page.emulateMediaFeatures([{ name: 'prefers-color-scheme', value: 'light' }, { name: 'prefers-reduced-motion', value: 'reduce' }]);
  await click(await live.$('.selection-prompt'));
  await click(await live.$('.selection-sheet-option:nth-of-type(1)'));
  const reducedSend = await live.$('.selection-send');
  await reducedSend.evaluate(e => e.scrollIntoView({ block: 'center', behavior: 'instant' }));
  await new Promise(resolve => setTimeout(resolve, 400));
  const reducedBox = await reducedSend.boundingBox();
  await page.mouse.move(reducedBox.x + reducedBox.width / 2, reducedBox.y + reducedBox.height / 2);
  await page.mouse.down();
  await new Promise(resolve => setTimeout(resolve, 200));
  assert.deepEqual(await reducedSend.evaluate(e => ({
    transform: getComputedStyle(e).transform,
    opacity: getComputedStyle(e).opacity,
    transition: getComputedStyle(e).transitionDuration,
  })), { transform: 'none', opacity: '1', transition: '0s' });
  await page.mouse.up();
  await page.waitForSelector('.selection-answer');
  await click(await live.$('.selection-reset'));
  console.log('PASS selection reduced motion');
  await page.emulateMediaFeatures([{ name: 'prefers-color-scheme', value: 'light' }]);

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
  await page.emulateMediaFeatures([{ name: 'prefers-color-scheme', value: 'light' }, { name: 'prefers-reduced-motion', value: 'reduce' }]);
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
