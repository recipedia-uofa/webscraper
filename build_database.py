import sys
sys.path.append('ingredient_parser/')

import argparse
import csv
from ingredient_parser import IngredientParser
from ingredient_parser import load_ingredients, INGREDIENTS_DIR
import os

CSV_INDEX_TO_RELATIONSHIP = [
    'id',
    'url',
    'title',
    'img_url',
    'servings',
    'prep_time',
    'rating',
    'reviews',
    'made_it_count',
    'calories',
    'total_fat',
    'saturated_fat',
    'cholesterol',
    'sodium',
    'potassium',
    'total_carbohydrates',
    'dietary_fiber',
    'protein',
    'sugars',
    'vitamin_a',
    'vitamin_c',
    'calcium',
    'iron',
    'thiamin',
    'niacin',
    'vitamin_b6',
    'magnesium',
    'folate',
    # Everything above this index is a <contains> relationship
]

def build_database_ingredients(f, ingredients):
    '''Given a File Object and a dictionary of ingredients (ingredient -> category),
    write ingredient nodes, category nodes, and the relationships between
    ingredients and categories.
    '''
    ingredients = load_ingredients(INGREDIENTS_DIR)
    categories = os.listdir(INGREDIENTS_DIR)

    # Write category nodes
    for category in categories:
        f.write('_:{} <dgraph.type> \"Category\" .\n'.format(category))
        f.write('_:{} <cname> \"{}\" .\n'.format(category, category.replace('_', ' ')))

    # Write ingredients nodes and the relationship between ingredient and category
    for ingredient, category in ingredients.items():
        f.write('_:{} <iname> \"{}\" .\n'.format(ingredient.replace(' ', '_'), ingredient))
        f.write('_:{} <dgraph.type> \"Ingredient\" .\n'.format(ingredient.replace(' ', '_')))
        f.write('_:{} <categorized_as> _:{} .\n'.format(ingredient.replace(' ', '_'), category))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
    description='Script that builds the .rdf file from a csv file of recipes')
    parser.add_argument(
        '-i',
        '--input',
        dest='input',
        help='path to the input csv file',
        default='htmls.csv',
        type=str,
    )
    parser.add_argument(
        '-o',
        '--output',
        dest='output',
        help='path to the output file',
        default='recipedia.rdf',
        type=str,
    )
    args = parser.parse_args()

    ingredients = load_ingredients(INGREDIENTS_DIR)
    ingredient_parser = IngredientParser()

    with open(args.input, 'r') as f_input:
        reader = csv.reader(f_input,  delimiter=',', quoting=csv.QUOTE_ALL)
        with open(args.output, 'w') as f_output:

            build_database_ingredients(f_output, ingredients)

            for row in reader:

                id = row[0]
                for i in range(1, len(row)):
                    if (i < len(CSV_INDEX_TO_RELATIONSHIP)):

                        f_output.write('_:{} <{}> \"{}\" .\n'.format(id, CSV_INDEX_TO_RELATIONSHIP[i], row[i]))

                    else:

                        try:
                            raw_ingredient = row[i]
                            ingredient = ingredient_parser.parse(raw_ingredient)
                            f_output.write('_:{} <contains> _:{} .\n'.format(id, ingredient.replace(' ', '_')))
                        except Exception as e:
                            print(e)
