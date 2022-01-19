const utils = require("./utils");
const playwright = require('playwright');
const fs = require("fs");
const batch = JSON.parse(fs.readFileSync('layout-batch.json', 'utf8'));

const generateLayoutAndFetchLinks = async (page, info) => {
    await page.goto(info['webpage'], {waitUntil: 'networkidle'})

    await utils.autoScroll(page);

    await page.waitForTimeout(500); // fix scrolling bug

    for (let config of info['configs']) {
        await page.setViewportSize({ width: config['width'], height: config['height']});

        await page.screenshot({path: config['name'], fullPage: true});
    }

    const links = await page.evaluate((info) => {
        const sameHostHrefs = Array.from(document.links)
            .filter(link => link.hostname === window.location.hostname && link.pathname !== window.location.pathname)
            .map(link => ({'href': link.href, 'path': link.pathname, 'depth': info['depth'] + 1}));

        return [...new Set(sameHostHrefs)];
    }, info);

    await page.evaluate(() => {
        document.body.querySelectorAll('input').forEach(n => {
            n.placeholder = "";
        });

        document.body.querySelectorAll('*').forEach(n => {
            let backgroundImage = window.getComputedStyle(n).backgroundImage;
            if (backgroundImage !== 'none' && backgroundImage.startsWith("url")) {
                n.style.backgroundImage = "none";
                n.style.backdropFilter = "brightness(0)";
            }

            let color = window.getComputedStyle(n).color;
            if (color) {
                n.style.setProperty('color', 'rgba(0, 0, 0, 0)', 'important')
                n.style.setProperty('text-shadow', 'none', 'important')
            }
        });
    });


    await page.addStyleTag({content: 'img{filter: brightness(0) !important; background: black !important}'});
    await page.addStyleTag({content: 'svg{filter: brightness(0) !important; background: black !important}'});
    // await page.addStyleTag({content: 'iframe{filter: brightness(0) !important}'}); // visibility: hidden may be better, iframes are very tricky
    await page.addStyleTag({content: 'iframe{visibility: hidden !important}'});
    await page.addStyleTag({content: '*{color: rgba(0, 0, 0, 0) !important; text-shadow: none !important}'});
    await page.addStyleTag({content: 'ul{list-style: none !important}'});
    await page.addStyleTag({content: '*{animation: none !important;'});
    await page.addStyleTag({content: '*{-webkit-animation: none !important;}'});
    await page.addStyleTag({content: '*{-moz-animation: none !important}'});
    await page.addStyleTag({content: '*{-o-animation: none !important}'});

    await page.waitForTimeout(500); // text/images are sometimes visible without this

    for (let config of info['configs']) {
        await page.setViewportSize({ width: config['width'], height: config['height']});

        await page.screenshot({path: config['layout'], fullPage: true});
    }

    return links;
};

(async () => {
    const uniqueLinks = {};
    for (let [browserName, groupedBatch] of utils.groupBatchByBrowser(batch).entries()) {
        let browserType;
        for (let type of [playwright.chromium, playwright.firefox, playwright.webkit]) {
            if (browserName === type.name()) {
                browserType = type;
            }
        }

        if (!browserType) {
            continue;
        }

        const browser = await browserType.launch({logger: {
            isEnabled: () => true, log: (name, severity, message, args) => console.log(name, message)
        }});
        await utils.createPagePool(groupedBatch, browser, generateLayoutAndFetchLinks).then(allLinks => {
            for (let links of allLinks) {
                for (let link of links) {
                    if (!(link.path in uniqueLinks) || link.depth < uniqueLinks[link.path][1]) {
                        uniqueLinks[link.path] = [link.href, link.depth];
                    }
                }
            }
        });
        await browser.close();
    }

    const json = JSON.stringify(uniqueLinks, null, "\t");
    fs.writeFile('links.json', json, 'utf8', () => {});
})();

