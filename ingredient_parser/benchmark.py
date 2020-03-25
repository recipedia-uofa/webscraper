import sys
sys.path.append('../')
import argparse
import random
from ingredient_parser import IngredientParser
from build_database import DatabaseBuilder
import os
import csv


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description='Script that parses random recipes from an input csv file and print statistics for ingredient parsing')
    parser.add_argument(
        'path',
        help='path to the input csv file',
        default='htmls.csv',
        type=str,
    )
    parser.add_argument(
        '-n',
        '--number',
        dest='number',
        help='number of tests performed',
        default=100,
        type=int,
    )
    args = parser.parse_args()

    num_recipes = 0
    with open(args.path, 'r') as f:
        for line in f:
            num_recipes += 1

    print('{} has a total of {} recipes'.format(args.path, num_recipes))

    test_lines = set()
    while len(test_lines) != args.number:
        test_lines.add(int(random.random() * num_recipes))

    line_number = 0
    with open(args.path, 'r') as f_input:

        # stats
        total_ingredients = 0

        ingredient_parser = IngredientParser()
        reader = csv.reader(f_input,  delimiter=',',quoting=csv.QUOTE_ALL)
        for row in reader:
            if line_number in test_lines:
                raw_ingredients = row[len(DatabaseBuilder.CSV_INDEX_TO_RELATIONSHIP):]
                total_ingredients += len(raw_ingredients)
                for raw_ingredient in raw_ingredients:
                    try:
                        ingredient_parser.parse(raw_ingredient)
                    except ValueError as e:
                        # silent for now
                        pass
            line_number += 1

    print('Average number of ingredients per recipe: {}'.format(total_ingredients / args.number))
    print('Success rate for quantity parsing:', float(ingredient_parser.ingredients_parsed - ingredient_parser.quantity_parse_errors) / float(ingredient_parser.ingredients_parsed))
