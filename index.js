const puppeteer = require('puppeteer');
const fs = require('fs');
const recipeBaseUrl = 'https://www.allrecipes.com/recipe/'

const dirName = new Date().toISOString();

const startId = 8000;
const endId = 8010;

if (!fs.existsSync(dirName)){
  fs.mkdirSync(dirName);
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function download_recipe(page, recipeId) {
  await page.goto(recipeBaseUrl + recipeId.toString(), {waitUntil: 'networkidle2'});
  const html = await page.content();
  fs.writeFile(dirName + '/' + recipeId + '.html', html, () => {
    console.log(recipeId + ' Saved!');
  });
}

(async () => {

  const browser = await puppeteer.launch({headless: false});
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
