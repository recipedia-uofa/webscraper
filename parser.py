import argparse
from bs4 import BeautifulSoup
import codecs
import re
import os
import sys
import traceback
sys.path.append('ingredient_parser/')
from ingredient_parser import IngredientParser
from ingredient_parser import load_ingredients, INGREDIENTS_DIR


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

        lines = []

        lines.append('_:{} <xid> \"{}\" .'.format(self.id, self.url))
        lines.append('_:{} <dgraph.type> \"Recipe\" .'.format(self.id))
        lines.append('_:{} <name> \"{}\" .'.format(self.id, self.name))
        lines.append('_:{} <rating> \"{}\" .'.format(self.id, self.rating))
        lines.append('_:{} <calories> \"{}\" .'.format(self.id, self.calories))
        lines.append('_:{} <servings> \"{}\" .'.format(self.id, self.servings))

        for nutrient, quantity in self.nutrition_facts.items():
            lines.append('_:{} <{}> \"{}\" .'.format(self.id, nutrient, quantity))

        for ingredient in self.ingredients:
            lines.append('_:{} <contains> _:{} .'.format(self.id, ingredient.replace(' ', '_')))
        return '\n'.join(lines)

        # TODO: consider just dump out a csv file at this point
        # return ','.join([
        #     '\"{}\"'.format(self.url),
        #     '\"{}\"'.format(self.name),
        #     '\"{}\"'.format(str(self.rating)),
        #     '\"{}\"'.format(Recipe.separator.join(self.ingredients)),
        #     '\"{}\"'.format(self.img_url),
        #     '\"{}\"'.format(str(self.servings)),
        #     '\"{}\"'.format(str(self.prep_time)),
        #     '\"{}\"'.format(str(self.calories)),
        #     '\"{}\"'.format(str(self.fat)),
        #     '\"{}\"'.format(str(self.carbohydrates)),
        #     '\"{}\"'.format(str(self.protein)),
        #     '\"{}\"'.format(str(self.cholesterol)),
        #     '\"{}\"'.format(str(self.sodium)),
        # ])

def output_database_ingredients():

    ingredients = load_ingredients(INGREDIENTS_DIR)
    with open(args.output, 'w') as f:

        for ingredient in ingredients.keys():
            f.write('_:{} <xid> \"{}\" .\n'.format(ingredient.replace(' ', '_'), ingredient))
            f.write('_:{} <dgraph.type> \"Ingredient\" .\n'.format(ingredient.replace(' ', '_')))


def parse_recipe_html(path):
    '''Given a path to the html file, return a parsed recipe object
    '''
    # print('path', path.split('/')[-1].replace('.html', ''))

    recipe = Recipe()

    recipe.id = int(path.split('/')[-1].replace('.html', ''))
    with codecs.open(path, 'r', 'utf-8') as f:
        soup = BeautifulSoup(f.read(), features='html5lib')

        # Name
        recipe.name = soup.find(id='recipe-main-content').text

        # Ingredients
        for tag in soup.find_all(itemprop='recipeIngredient'):
            ingredient = tag.contents[0]
            try:
                ingredient = ingredient_parser.parse(ingredient)
                recipe.ingredients.append(ingredient)
            except Exception as e:
                print(e)

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
                recipe.nutrition_facts[name] = quantity
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
        default='data.rdf',
        type=str,
    )
    args = parser.parse_args()

    output_database_ingredients()

    ingredient_parser = IngredientParser()

    total = 0
    success = 0
    with open(args.output, 'a') as f:
        for (root, dirs, files) in os.walk(args.path, topdown=True):
            for file in files:
                if file.endswith('.html'):
                    try:
                        total = total + 1
                        f_html = os.path.join(root, file)
                        line = str(parse_recipe_html(f_html)) + '\n'
                        f.write(line)
                        success = success + 1
                    except KeyboardInterrupt:
                        sys.exit()
                    except NoNutritionFactsException:
                        print('No nutrition facts for {}'.format(file))
                    except Exception as e:
                        print('Failed', file)
                        # print(traceback.format_exc())
    print('{}/{} succeeded!'.format(success, total))
