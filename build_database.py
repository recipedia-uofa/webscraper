# REQ 9-4: Database builder

import sys
sys.path.append('ingredient_parser/')
import os
from load_ingredients import load_ingredients, INGREDIENTS_DIR
from ingredient_parser import IngredientParser
import csv
import argparse
from nutriscore import load_model, predict_nutriscore
import time


class DatabaseBuilder:

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

    # parameters for beta distribution used for rating score
    ALPHA = 3
    BETA  = 2

    def __init__(self, f_input, f_output, model):
        self.f_input = f_input
        self.f_output = f_output

        self.ingredients, self.alias_map = load_ingredients()
        self.ingredient_parser = IngredientParser()
        self.nutriscore_model = load_model(model)

        self.num_recipes_processed = 0
        self.num_recipes_failed = 0
        self.duration = 0

    @staticmethod
    def build_database_ingredients(f, ingredients, aliases):
        """
        Given a File Object and a dictionary of ingredients (ingredient -> category),
        write ingredient nodes, category nodes, and the relationships between
        ingredients and categories.
        """
        categories = os.listdir(INGREDIENTS_DIR)

        # Write category nodes
        for category in categories:
            f.write('_:{} <dgraph.type> \"Category\" .\n'.format(category))
            f.write('_:{} <cname> \"{}\" .\n'.format(
                category, category.replace('_', ' ')))

        # Write ingredients nodes and the relationship between ingredient and category
        for ingredient in aliases.values():
            category = ingredients[ingredient]
            f.write('_:{} <iname> \"{}\" .\n'.format(
                ingredient.replace(' ', '_'), ingredient))
            f.write('_:{} <dgraph.type> \"Ingredient\" .\n'.format(
                ingredient.replace(' ', '_')))
            f.write('_:{} <categorized_as> _:{} .\n'.format(
                ingredient.replace(' ', '_'), category))

    @staticmethod
    def get_rating_score(average_rating, num_ratings, alpha, beta):
        normalized_rating = average_rating / 5
        return 5 * (alpha + normalized_rating * num_ratings) / (alpha + beta + num_ratings)

    def parse_csv_row(self, row):
        """
        Given a row as a list and a File Object, dump the database for that row
        to the File Object.
        """

        self.num_recipes_processed += 1

        id = row[0]
        url_id = row[1].split(r'/')[-3]

        # if the id from the filename does not match the id of the url, redirection
        # has happened, and the row should be skipped to prevent duplicate entries.
        if id != url_id:
            return

        try:
            # Calculate nutrition score
            recipe_data = row[:len(DatabaseBuilder.CSV_INDEX_TO_RELATIONSHIP) - 1]
            nutrition_score = predict_nutriscore(self.nutriscore_model, recipe_data)
            self.f_output.write('_:{} <nutrition_score> \"{:.2f}\" .\n'.format(id, nutrition_score))
            # print(nutriscore)
        except ZeroDivisionError:
            print("recipe {} failed: division by zero".format(id))
            return

        for i in range(1, len(DatabaseBuilder.CSV_INDEX_TO_RELATIONSHIP) - 1):
            self.f_output.write('_:{} <{}> \"{}\" .\n'.format(
                id, DatabaseBuilder.CSV_INDEX_TO_RELATIONSHIP[i], row[i]))

        raw_ingredients = row[len(DatabaseBuilder.CSV_INDEX_TO_RELATIONSHIP):]
        parsed_ingredients = []

        for raw_ingredient in raw_ingredients:
            if any([ignored_ingredient in raw_ingredient for ignored_ingredient in DatabaseBuilder.INGREDIENTS_TO_IGNORE]):
                continue
            else:
                parsed_ingredient = self.ingredient_parser.parse(raw_ingredient)
                if parsed_ingredient is None:
                    print('Failed parsing', raw_ingredient)
                    self.num_recipes_failed += 1
                    return
                else:
                    parsed_ingredient = self.alias_map[parsed_ingredient]
                    parsed_ingredients.append(parsed_ingredient)


        # REQ 1-1: Recipe ontology contains relationships.
        for parsed_ingredient in parsed_ingredients:
            self.f_output.write('_:{} <contains> _:{} .\n'.format(
                id, parsed_ingredient.replace(' ', '_')))

        # Calculate rating score
        average_rating = float(row[6])
        num_ratings = float(row[7])
        rating_score = DatabaseBuilder.get_rating_score(average_rating, num_ratings, DatabaseBuilder.ALPHA, DatabaseBuilder.BETA)
        self.f_output.write('_:{} <rating_score> \"{:.2f}\" .\n'.format(id, rating_score))

    # REQ 1-2: Store ontology in queryable format.
    def build(self, build_ingredients=True):
        start_time = time.time()
        reader = csv.reader(self.f_input,  delimiter=',', quoting=csv.QUOTE_ALL)

        if build_ingredients:
            self.build_database_ingredients(self.f_output, self.ingredients, self.alias_map)

        for row in reader:
            row = [col.replace(r'"', r'\"') for col in row]
            self.parse_csv_row(row)

        self.duration = time.time() - start_time

    def statistics(self):
        print('Took {}s per recipe on average'.format(self.duration / self.num_recipes_processed))
        print('Failed {}/{} recipes'.format(self.num_recipes_failed, self.num_recipes_processed))
        print(self.ingredient_parser.find_closest_match.cache_info())


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
    parser.add_argument(
        '-m',
        '--model',
        dest='model',
        help='path to a serialized nutriscore model',
        default='nutriscore.model',
        type=str
    )
    args = parser.parse_args()

    with open(args.input, 'r') as f_input, open(args.output, 'w') as f_output:
            builder = DatabaseBuilder(f_input, f_output, args.model)
            builder.build()
            builder.statistics()
