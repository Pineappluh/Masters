const playwright = require('playwright');
const argv = require('minimist')(process.argv.slice(2));

(async () => {
    // Make sure to run headed.
    const browser = await playwright.chromium.launch({ headless: false });

    // Setup context however you like.
    const context = await browser.newContext();

    // Pause the page, and start recording manually.
    const page = await context.newPage();
    await page.setViewportSize({ width: argv['width'], height: argv['height'] });
    await page.goto(argv['webpage'], {waitUntil: 'commit'});

    await page.waitForEvent('close');
    await context.storageState({ path: 'state.json' });
    await browser.close();
})();
