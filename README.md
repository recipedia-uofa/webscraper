# Webscraper

## Scraper

The scraper is responsible for downloading raw html files for recipes from allrecipes.com. The html files will be stored at a timestamped folder in the download folder: `./download/<timestamp>`

Following is the synopsis of command line arguments that are accepted by the script. Note that both `startId` and `endId` are inclusive.

`$ node scraper.js -h`

```
usage: scraper.js [-h] [-s startId] [-e endId]

Script to download raw recipe htmls from allrecipes.com

Optional arguments:
  -h, --help            Show this help message and exit.
  -s startId, --startId startId
                        The ID of the first recipe to download
  -e endId, --endId endId
                        The ID of the last recipe to download
```

For example, to download recipes 20000 to 70000, run

`$ node scraper.js -s 20000 -e 70000`

##### Caveats
- The default values for startId is 6663 and the default value for endId is 269344 now.
- The script prints `skip: recipe <id> don't have a nutrition button` when there is no nutrition button in the html page.
- The script retries each recipe at most 3 (maxRetry) times.
- After failing to connect for 3 (maxConsecutiveFailures) times, the script will terminate.

## HtmlParser

## IngredientParser

## DatabaseBuilder
