const genericPool = require("generic-pool");

async function autoScroll(page) {
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
                    window.scrollTo(0, 0);
                    resolve();
                }
            }, 100);
        });
    });
}

const pageFactory = (context) => {
    return {
        create: () => context.newPage(),
        destroy: (page) => page.close()
    };
};

async function createPagePool(batch, browser, processPage) {
    const context = await browser.newContext({storageState: 'state.json', ignoreHTTPSErrors: true});
    await context.setDefaultTimeout(60 * 1000); // 60 seconds

    const pagePool = genericPool.createPool(pageFactory(context), { max: 5 });
    const tasks = batch.map(async (info) => {
        const page = await pagePool.acquire();
        const data = await processPage(page, info);
        await pagePool.release(page);
        return data;
    });
    return Promise.all(tasks);
}

function groupBatchByBrowser(batch) {
    return batch.reduce(
        (entryMap, e) => entryMap.set(e.browser, [...entryMap.get(e.browser) || [], e]),
        new Map()
    );
}

async function processBatchByBrowser(batch) {

}

module.exports = { autoScroll, createPagePool, groupBatchByBrowser};

