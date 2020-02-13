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

async function download_recipe(browser, recipeId) {
  const page = await browser.newPage();
  await page.goto(recipeBaseUrl + recipeId.toString(), {waitUntil: 'networkidle2'});
  const html = await page.content();
  fs.writeFile(dirName + '/' + recipeId + '.html', html, () => {
    console.log(recipeId + ' Saved!');
  });
  return page.close();
}

(async () => {

  const browser = await puppeteer.launch({headless: false});

    try {
      for (let i = startId; i < endId; i++) {
        await download_recipe(browser, i);

      }

      await Promise.all(downloads);
    } catch (err) {
      console.log(err);
    } finally {
      await browser.close();
    }
})();
