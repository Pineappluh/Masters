const utils = require("./utils");
const playwright = require('playwright');
const fs = require("fs");
const fsPromises = fs.promises;
const batch = JSON.parse(fs.readFileSync('classification-batch.json', 'utf8'));

const classifyElements = async (page, info) => {
    await page.goto(info['webpage'], {waitUntil: 'networkidle'});

    await utils.autoScroll(page);

    for (let config of info['configs']) {
        await page.setViewportSize({width: config['width'], height: config['height']});

        await page.screenshot({path: 'test.png', fullPage: true});

        const input = config['input'];

        const values = await page.evaluate((input) => {
            function getVotingPoints(boundingBox) {
                const points = [];
                let threshold = 2;
                if (boundingBox.width < 30 || boundingBox.height < 30) {
                    threshold = 1;
                }
                points.push([boundingBox.x + threshold, boundingBox.y + threshold]);
                points.push([boundingBox.x + threshold, boundingBox.y + boundingBox.height - threshold]);
                points.push([boundingBox.x + boundingBox.width - threshold, boundingBox.y + threshold]);
                points.push([boundingBox.x + boundingBox.width - threshold, boundingBox.y + boundingBox.height - threshold]);
                points.push([boundingBox.x + Math.round(boundingBox.width / 2), boundingBox.y + Math.round(boundingBox.height / 2)]);
                return points
            }

            function findHighestOccurrenceKey(counter) {
                return Object.keys(counter).reduce((a, b) => counter[a] > counter[b] ? a : b, 0)
            }

            const values = [];
            for (let boundingBox of input) {
                const points = getVotingPoints(boundingBox);

                const classCounts = {}
                const tagCounts = {}
                for (let point of points) {
                    const elem = document.elementFromPoint(point[0], point[1]);
                    if (elem !== null) {
                        classCounts[elem.className] = (classCounts[elem.className] || 0) + 1;
                        tagCounts[elem.tagName] = (tagCounts[elem.tagName] || 0) + 1;
                    }
                }

                values.push({
                    type: findHighestOccurrenceKey(tagCounts),
                    className: findHighestOccurrenceKey(classCounts),
                    elements: document.elementsFromPoint(points[0][0], points[0][1]).length
                });
            }

            return values;
        }, input);

        const json = JSON.stringify(values, null, "\t");
        await fsPromises.writeFile(config['json'], json, 'utf8');
    }
};

(async () => {
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

        const browser = await browserType.launch({
            logger: {
                isEnabled: () => true, log: (name, severity, message, args) => console.log(name, message)
            }
        });
        await utils.createPagePool(groupedBatch, browser, classifyElements).then(() => {});
        await browser.close();
    }
})();


