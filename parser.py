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
        # _:25708 <xid> "https://www.allrecipes.com/recipe/25708" .
        # _:25708 <dgraph.type> "Recipe" .
        # _:25708 <name> "Potato Leek Soup III" .
        # _:25708 <rating> "4.5" .
        # _:25708 <contains> _:butter .
        # _:25708 <contains> _:leek .
        # _:25708 <contains> _:chicken_broth .
        # _:25708 <contains> _:cornstarch .
        # _:25708 <contains> _:potato .
        # _:25708 <contains> _:cream .

        lines = []
        lines.append('_:{} <xid> \"{}\" .'.format(self.id, self.url))
        for ingredient in self.ingredients:
            lines.append('_:{} <contains> _:{} .'.format(self.id, ingredient.replace(' ', '_')))
        return '\n'.join(lines)

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
