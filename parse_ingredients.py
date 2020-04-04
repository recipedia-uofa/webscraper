import csv
import argparse

import sys
sys.path.append('ingredient_parser/')
from ingredient_parser import load_ingredients, INGREDIENTS_DIR
from ingredient_parser import IngredientParser

INGREDIENTS_TO_IGNORE = [
    'salt',
    'black pepper',
    'water',
    'skewers',
    'coloring',
]

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

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Script that builds the .rdf file from a csv file of recipes')
    parser.add_argument(
        '-i',
        '--input',
        dest='input',
        help='path to the input csv file',
        default='htmldata.csv',
        type=str,
    )
    parser.add_argument(
        '-o',
        '--output',
        dest='output',
        help='path to the output file',
        default='parseddata.csv',
        type=str,
    )
    args = parser.parse_args()

    assert(args.input.endswith('.csv'))
    assert(args.output.endswith('.csv'))

    all_ingredients = load_ingredients(INGREDIENTS_DIR)
    ingredient_parser = IngredientParser()

    # Statistics
    num_recipes_failed = 0
    successes = 0

    with open(args.input, 'r') as input_csv, open(args.output, 'w') as output_csv:
        reader = csv.reader(input_csv, delimiter=',', quoting=csv.QUOTE_ALL)
        writer = csv.writer(output_csv, delimiter=',', quoting=csv.QUOTE_ALL)

        for row in reader:
            raw_ingredients = row[len(CSV_INDEX_TO_RELATIONSHIP):]
            parsed_ingredients = []
            failed_recipe = False

            for raw_ingredient in raw_ingredients:
                if any([ignored_ingredient in raw_ingredient for ignored_ingredient in INGREDIENTS_TO_IGNORE]):
                    continue
                else:
                    parsed_ingredient = ingredient_parser.parse(raw_ingredient)
                    if parsed_ingredient is None:
                        print('Failed parsing', raw_ingredient)
                        num_recipes_failed += 1
                        failed_recipe = True
                        break
                    else:
                        parsed_ingredients.append(parsed_ingredient)

            if not failed_recipe:
                writer.writerow(row[:len(CSV_INDEX_TO_RELATIONSHIP)] + parsed_ingredients)
                successes += 1
                print('Parsed {}'.format(successes))
            
    print("Done!")
