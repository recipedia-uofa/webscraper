import argparse
from bs4 import BeautifulSoup
import codecs
import re
import os
import sys
import traceback
sys.path.append('ingredient_parser/')
from ingredient_parser import IngredientParser


class NoNutritionFactsException(Exception):
    '''Thrown when nutrition facts are not present in the html file
    '''
    pass


class Recipe:
    separator = '|'  # used to separate ingredients

    def __init__(self):
        self.url = ''
        self.name = ''
        self.rating = 0
        self.ingredients = list()
        self.img_url = ''
        self.servings = 0
        self.prep_time = 0
        self.calories = 0  # calories/serving
        self.fat = 0  # g/serving
        self.carbohydrates = 0  # g/serving
        self.protein = 0  # g/serving
        self.cholesterol = 0  # mg/serving
        self.sodium = 0  # mg/serving

    def __str__(self):
        return ','.join([
            '\"{}\"'.format(self.url),
            '\"{}\"'.format(self.name),
            '\"{}\"'.format(str(self.rating)),
            '\"{}\"'.format(Recipe.separator.join(self.ingredients)),
            '\"{}\"'.format(self.img_url),
            '\"{}\"'.format(str(self.servings)),
            '\"{}\"'.format(str(self.prep_time)),
            '\"{}\"'.format(str(self.calories)),
            '\"{}\"'.format(str(self.fat)),
            '\"{}\"'.format(str(self.carbohydrates)),
            '\"{}\"'.format(str(self.protein)),
            '\"{}\"'.format(str(self.cholesterol)),
            '\"{}\"'.format(str(self.sodium)),
        ])


def parse_recipe_html(path):
    '''Given a path to the html file, return a parsed recipe object
    '''
    recipe = Recipe()
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
            # Nutrition Facts
            recipe.calories = int(
                re.search(
                    r'(\d+) calories',
                    soup.find('span', {'itemprop': 'calories'}).text
                ).group(1)
            )

            recipe.fat = float(
                soup.find('span', {'itemprop': 'fatContent'}).text)

            recipe.carbohydrates = float(
                soup.find('span', {'itemprop': 'carbohydrateContent'}).text)

            recipe.protein = float(
                soup.find('span', {'itemprop': 'proteinContent'}).text)

            cholesterol_str = soup.find(
                'span', {'itemprop': 'cholesterolContent'}).text
            if (cholesterol_str == '< 1 '):
                recipe.cholesterol = 0
            else:
                recipe.cholesterol = float(cholesterol_str)

            sodium_str = soup.find('span', {'itemprop': 'sodiumContent'}).text
            if (sodium_str == '< 1 '):
                recipe.sodium = 0
            else:
                recipe.sodium = float(sodium_str)
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
        default='data.csv',
        type=str,
    )
    args = parser.parse_args()

    ingredient_parser = IngredientParser()

    total = 0
    success = 0
    with open(args.output, 'w') as f:
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
