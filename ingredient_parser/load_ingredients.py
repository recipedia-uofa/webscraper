import os

INGREDIENTS_DIR = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), 'ingredients')


def load_ingredients(ing_dir=INGREDIENTS_DIR):
    """
    Given a directory, load all ingredients under that directory and return
    an ingredient dictionary that maps ingredients to its category.
    """

    ingredients_dict = dict()
    alias_dict = dict()

    for file in os.listdir(ing_dir):
        if file not in ['.pytest_cache']:
            with open(os.path.join(ing_dir, file), 'r') as f:
                for ingredient_line in f:
                    ingredients = ingredient_line.split(':')
                    main_ingredient = ingredients[0].strip()
                    ingredients_dict[main_ingredient] = file
                    alias_dict[main_ingredient] = main_ingredient

                    # Process aliases
                    for ing in ingredients[1:]:
                        stripped_ing = ing.strip()
                        ingredients_dict[stripped_ing] = file
                        alias_dict[stripped_ing] = main_ingredient

    return ingredients_dict, alias_dict
