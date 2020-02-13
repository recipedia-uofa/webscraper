const puppeteer = require('puppeteer');
const fs = require('fs');
const recipeBaseUrl = 'https://www.allrecipes.com/recipe/'

const downloadBasePath = './download'
const downloadPath = downloadBasePath + '/' + new Date().toISOString();

const startId = 6663;
const endId = 269344;


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

    try {
      for (let i = startId; i < endId; i++) {
        await download_recipe(page, i);
      }
    } catch (err) {
      console.log(err);
    } finally {
      await browser.close();
    }
})();
