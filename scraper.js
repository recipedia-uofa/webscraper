// REQ 9-1: Recipe downloader

const puppeteer = require('puppeteer');
var ArgumentParser = require('argparse').ArgumentParser;
const fs = require('fs');
const recipeBaseUrl = 'https://www.allrecipes.com/recipe/'

const downloadBasePath = './download'
const downloadPath = downloadBasePath + '/' + new Date().toISOString();

// command line arguments
var parser = new ArgumentParser({
  addHelp:true,
  description: 'Script to download raw recipe htmls from allrecipes.com'
});
parser.addArgument(
  [ '-s', '--startId' ],
  {
    action: 'store',
    type: 'int',
    defaultValue: 6663,
    metavar: 'startId',
    help: 'The ID of the first recipe to download'
  }
);
parser.addArgument(
  [ '-e', '--endId' ],
  {
    action: 'store',
    type: 'int',
    defaultValue: 269344,
    metavar: 'endId',
    help: 'The ID of the last recipe to download'
  }
);
var args = parser.parseArgs();

const maxRetry = 3;
const maxConsecutiveFailures = 3;
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
  const element = await page.$('a[class="see-full-nutrition"]')
  if (element == null) {
    console.log(`skip: recipe ${recipeId} don't have a nutrition button`)
    return
  }
  await element.click()
  await page.waitForSelector(".nutrient-value");
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

  let consecutiveFailrues = 0;

  for (let recipeId = args.startId; recipeId <= args.endId; recipeId++) {
    for (let attempt = 0; attempt < maxRetry; attempt++) {
      try {
        await sleep(Math.floor(sleepTime + Math.random() * 1000));
        await download_recipe(page, recipeId);
        consecutiveFailrues = 0;
        break; // succeeds, go to the next recipeId
      } catch(err) {
        console.log(`Failed for recipeId=${recipeId} for attempt=${attempt}`);
        console.log(err);
        if (attempt == maxRetry - 1) {
          consecutiveFailrues++;
          if (consecutiveFailrues >= maxConsecutiveFailures) {
            // Failed for a recipe on the last attempt, and the number of
            // consecutive failures have reached the maximum. Abort.
            console.log(`Failed ${consecutiveFailrues} recipes consecutively. Abort.`);
            await browser.close();
            return;
          }
          else {
            // Failed for a recipe on the last attempt, go to the next recipe
            break;
          }
        }
        else {
            // Failed for a recipe, try that recipe again
            continue;
        }
      }
    }
  }
  await browser.close();
})();
