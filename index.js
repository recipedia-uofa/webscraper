const puppeteer = require('puppeteer');
const fs = require('fs');
const recipeBaseUrl = 'https://www.allrecipes.com/recipe/'

const downloadBasePath = './download'
const downloadPath = downloadBasePath + '/' + new Date().toISOString();

const startId = 8542;
const endId = 269344;

const maxRetry = 10;
const sleepTime = 1000; // 1s

if (!fs.existsSync(downloadBasePath)){
  fs.mkdirSync(downloadBasePath);
}

if (!fs.existsSync(downloadPath)){
  fs.mkdirSync(downloadPath);
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function download_recipe(page, recipeId) {
  await page.goto(recipeBaseUrl + recipeId.toString(), {waitUntil: 'networkidle2'});
  const html = await page.content();
  fs.writeFile(downloadPath + '/' + recipeId + '.html', html, () => {
    console.log(recipeId + ' saved!');
  });
}

(async () => {

  const browser = await puppeteer.launch({headless: true});
  const page = await browser.newPage();

  await page.setRequestInterception(true);
  page.on('request', request => {
    if (request.resourceType() === 'image')
      request.abort();
    else
      request.continue();
  });

  for (let recipeId = startId; recipeId < endId; recipeId++) {
    for (let attempt = 0; attempt < maxRetry; attempt++) {
      try {
        await sleep(Math.floor(sleepTime + Math.random() * 1000));
        await download_recipe(page, recipeId);
        break; // succeeds, go to the next recipeId
      } catch(err) {
        console.log(`Failed for recipeId=${recipeId} for attempt=${attempt}`);
        console.log(err);
        if (attempt == maxRetry - 1) {
          await browser.close();
          return;
        }
        else {
          continue;
        }
      }
    }
  }
  await browser.close();
})();
