const playwright = require('playwright');

async function autoScroll(page){
    await page.evaluate(async () => {
        await new Promise((resolve, reject) => {
            let totalHeight = 0;
            let distance = 100;
            let timer = setInterval(() => {
                let scrollHeight = document.body.scrollHeight;
                window.scrollBy(0, distance);
                totalHeight += distance;

                if(totalHeight >= scrollHeight){
                    clearInterval(timer);
                    resolve();
                }
            }, 100);
        });
    });
}

(async () => {
    const browser = await playwright.chromium.launch({
        logger: {
            isEnabled: () => true,
            log: (name, severity, message, args) => console.log(name, message)
        }
    });
    const context = await browser.newContext({ storageState: 'state.json' });
    const page = await context.newPage();
    await page.goto('https://www.jayone.org/user/145', {waitUntil: 'networkidle'})
    await page.setViewportSize({ width: 360, height: 640});
    await page.screenshot({path: 'example-start.png', fullPage: true});

    await autoScroll(page);

    let only_text = true;

    if (only_text) {
        await page.evaluate(() => {
            document.body.querySelectorAll('input').forEach(n => {
                n.placeholder = "";
            });


            document.body.querySelectorAll('*').forEach(n => {
                let color = window.getComputedStyle(n).color;
                if (color) {
                    n.style.setProperty('color', 'rgba(255, 255, 255, 1)', 'important')
                    n.style.setProperty('text-shadow', 'none', 'important')
                }

                n.style.setProperty('background-color', 'black' , 'important')
                n.style.setProperty('border-color', 'black' , 'important')
                n.style.setProperty('background-image', 'none' , 'important')
                n.style.setProperty('background', 'none' , 'important')
                n.style.setProperty('box-shadow', 'none' , 'important')
            });
        });

        await page.addStyleTag({content: '*{background-color: black !important}'})
        await page.addStyleTag({content: 'svg{filter: brightness(0) !important; background: black !important}'});
        await page.addStyleTag({content: 'iframe{visibility: hidden !important}'});
        await page.addStyleTag({content: 'img{filter: brightness(0) !important; background: black !important}'})
        await page.addStyleTag({content: 'ul{list-style: none !important}'});
    }

    await page.waitForTimeout(1000);
    await page.screenshot({path: 'example.png', fullPage: true});

    await browser.close();
})();

