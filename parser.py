# REQ 9-2: HTML parser

import argparse
from bs4 import BeautifulSoup
import codecs
import re
import os
import sys
import traceback
import csv


class NoNutritionFactsException(Exception):
    '''Thrown when nutrition facts are not present in the html file
    '''
    pass


class Recipe:
    separator = '|'  # used to separate ingredients

    def __init__(self):
        self.id = 0
        self.url = ''
        self.name = ''
        self.rating = 0
        self.reviews = 0
        self.made_it_count = 0
        self.ingredients = list()
        self.img_url = ''
        self.servings = 0
        self.prep_time = 0
        self.nutrition_facts = {}
        self.calories = 0  # calories/serving

    def __str__(self):
        return self.url

def parse_recipe_html(path):
    '''Given a path to the html file, return a parsed recipe object
    '''

    recipe = Recipe()

    recipe.id = int(path.split('/')[-1].replace('.html', ''))
    with codecs.open(path, 'r', 'utf-8') as f:
        soup = BeautifulSoup(f.read(), features='html5lib')

        # Name
        recipe.name = soup.find(id='recipe-main-content').text

        # Ingredients
        for tag in soup.find_all(itemprop='recipeIngredient'):
            recipe.ingredients.append(tag.contents[0])

        # Rating
        rating_div = soup.findAll('div', {'class': 'recipe-summary__stars'})[0]
        rating_string = rating_div.find('img')['alt']
        result = re.search(
            r'Rated as (\d+(?:\.\d{1,2})?) out of 5 Stars', rating_string)
        recipe.rating = float(result.groups(1)[0])

        # Reviews
        reviews_str = soup.find(
            'span', {'class': 'review-count'}).text
        match = re.search(r'(\d+) review(?:s)?', reviews_str)
        if match:
            recipe.made_it_count = int(match.groups(1)[0])
            recipe.reviews = int(match.groups(1)[0])
        else:
            match = re.search(r'(\d)k review(?:s)?', reviews_str)
            recipe.reviews = int(match.groups(1)[0]) * 1000

        # Made it count
        made_it_count_span = soup.find(
            'span', {'class': 'made-it-count'})
        # The count is located in the next sibling of the span with class 'made-it-count'
        made_it_count_str = made_it_count_span.find_next_sibling().text
        match = re.search(r'(\d+).made it', made_it_count_str)
        if match:
            recipe.made_it_count = int(match.groups(1)[0])
        else:
            match = re.search(r'(\d)k.made it', made_it_count_str)
            recipe.made_it_count = int(match.groups(1)[0]) * 1000

        # Image URL
        recipe.img_url = soup.find('img', {'class': 'rec-photo'})['src']

        # Recipe URL
        recipe.url = soup.find(id='canonicalUrl')['href']

        # Servings
        recipe.servings = (int)(soup.find(id='metaRecipeServings')['content'])

        # Prep Time
        # The prep time string can be one of the following forms:
        # prep_time_string = '1 h 10 m'
        # prep_time_string = '45 m'
        try:
            prep_time_string = soup.find(
                'span', {'class': 'ready-in-time'}).text
            result = re.search(
                r'(?:(\d{1,2}) h )?(\d{1,2}) m', prep_time_string)
            if (result.groups()[0]):
                h = (int)(result.groups()[0])
            else:
                h = 0
            m = (int)(result.groups()[1])
            recipe.prep_time = h * 60 + m
        except AttributeError:
            recipe.prep_time = 0

        try:
            recipe.calories = int(
                re.search(
                    r'(\d+) calories',
                    soup.find('span', {'itemprop': 'calories'}).text
                ).group(1)
            )
            for row in soup.find_all('div', {'class': 'nutrition-row'}):
                row = row.find('span', {'class': 'nutrient-name'})
                name, quantity = row.text.split(':')
                name = name.lower().replace(' ', '_')
                quantity.strip()
                quantity = re.search(u'(?P<quantity>[\d.]+).*', quantity).group('quantity')
                recipe.nutrition_facts[name] = float(quantity)
        except:
            raise(NoNutritionFactsException)

        return recipe


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description='Script to parse raw recipe htmls')
    parser.add_argument(
        'path',
        help='path to the folder of the htmls',
        action='store',
        type=str
    )
    parser.add_argument(
        '-o',
        '--output',
        dest='output',
        help='path to the output file',
        default='htmls.csv',
        type=str,
    )
    args = parser.parse_args()

    total = 0
    success = 0
    with open(args.output, 'a') as f:
        writer = csv.writer(f, delimiter=',', quoting=csv.QUOTE_ALL)
        for (root, dirs, files) in os.walk(args.path, topdown=True):
            for file in files:
                if file.endswith('.html'):
                    try:
                        total = total + 1
                        f_html = os.path.join(root, file)
                        recipe = parse_recipe_html(f_html)
                        row = [
                            recipe.id,
                            recipe.url,
                            recipe.name,
                            recipe.img_url,
                            recipe.servings,
                            recipe.prep_time,
                            recipe.rating,
                            recipe.reviews,
                            recipe.made_it_count,
                            recipe.calories,
                            recipe.nutrition_facts['total_fat'],
                            recipe.nutrition_facts['saturated_fat'],
                            recipe.nutrition_facts['cholesterol'],
                            recipe.nutrition_facts['sodium'],
                            recipe.nutrition_facts['potassium'],
                            recipe.nutrition_facts['total_carbohydrates'],
                            recipe.nutrition_facts['dietary_fiber'],
                            recipe.nutrition_facts['protein'],
                            recipe.nutrition_facts['sugars'],
                            recipe.nutrition_facts['vitamin_a'],
                            recipe.nutrition_facts['vitamin_c'],
                            recipe.nutrition_facts['calcium'],
                            recipe.nutrition_facts['iron'],
                            recipe.nutrition_facts['thiamin'],
                            recipe.nutrition_facts['niacin'],
                            recipe.nutrition_facts['vitamin_b6'],
                            recipe.nutrition_facts['magnesium'],
                            recipe.nutrition_facts['folate'],
                        ]
                        row += recipe.ingredients
                        writer.writerow(row)
                        success = success + 1
                    except KeyboardInterrupt:
                        sys.exit()
                    except NoNutritionFactsException:
                        print('No nutrition facts for {}'.format(file))
                    except Exception as e:
                        print('Failed', file)
                        # print(traceback.format_exc())
    print('{}/{} succeeded!'.format(success, total))
