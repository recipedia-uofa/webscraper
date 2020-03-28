import sys
sys.path.append('ingredient_parser/')
import os
from ingredient_parser import load_ingredients, INGREDIENTS_DIR
from ingredient_parser import IngredientParser
import csv
import argparse


class DatabaseBuilder():

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

    def __init__(self, f_input, f_output):
        self.f_input = f_input
        self.f_output = f_output

        self.ingredients = load_ingredients(INGREDIENTS_DIR)
        self.ingredient_parser = IngredientParser()

    def build_database_ingredients(self, f, ingredients):
        '''Given a File Object and a dictionary of ingredients (ingredient -> category),
        write ingredient nodes, category nodes, and the relationships between
        ingredients and categories.
        '''
        ingredients = load_ingredients(INGREDIENTS_DIR)
        categories = os.listdir(INGREDIENTS_DIR)

        # Write category nodes
        for category in categories:
            f.write('_:{} <dgraph.type> \"Category\" .\n'.format(category))
            f.write('_:{} <cname> \"{}\" .\n'.format(
                category, category.replace('_', ' ')))

        # Write ingredients nodes and the relationship between ingredient and category
        for ingredient, category in ingredients.items():
            f.write('_:{} <iname> \"{}\" .\n'.format(
                ingredient.replace(' ', '_'), ingredient))
            f.write('_:{} <dgraph.type> \"Ingredient\" .\n'.format(
                ingredient.replace(' ', '_')))
            f.write('_:{} <categorized_as> _:{} .\n'.format(
                ingredient.replace(' ', '_'), category))

    def parse_csv_row(self, row):
        '''Given a row as a list and a File Object, dump the database for that row
        to the File Object.
        '''
        id = row[0]
        url_id = row[1].split(r'/')[-3]

        # if the id from the filename does not match the id of the url, redirection
        # has happened, and the row should be skipped to prevent duplicate entries.
        if id != url_id:
            return

        raw_ingredients = row[len(DatabaseBuilder.CSV_INDEX_TO_RELATIONSHIP):]
        parsed_ingredients = [self.ingredient_parser.parse(raw_ingredient) for raw_ingredient in raw_ingredients]
        if None in parsed_ingredients:
            print('Failed for recipe', id)
            return
        else:
            for parsed_ingredient in parsed_ingredients:

                self.f_output.write('_:{} <contains> _:{} .\n'.format(
                    id, parsed_ingredient.replace(' ', '_')))

        for i in range(1, len(DatabaseBuilder.CSV_INDEX_TO_RELATIONSHIP) - 1):
            self.f_output.write('_:{} <{}> \"{}\" .\n'.format(
                id, DatabaseBuilder.CSV_INDEX_TO_RELATIONSHIP[i], row[i]))

    def build(self, build_ingredients = True):

        reader = csv.reader(self.f_input,  delimiter=',',
                            quoting=csv.QUOTE_ALL)

        if build_ingredients:
            self.build_database_ingredients(self.f_output, self.ingredients)

        for row in reader:
            row = [col.replace(r'"', r'\"') for col in row]
            self.parse_csv_row(row)


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

    with open(args.input, 'r') as f_input:
        with open(args.output, 'w') as f_output:

            builder = DatabaseBuilder(f_input, f_output)
            builder.build()
