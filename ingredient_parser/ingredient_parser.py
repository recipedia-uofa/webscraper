import inflect
import ply.lex as lex
import ply.yacc as yacc
from ply.lex import TOKEN
import re
import os
from fuzzywuzzy import fuzz


INGREDIENTS_DIR = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), 'ingredients')


def _remove_parenthesis(s):
    return re.sub(r" ?\([^)]+\)", "", s)


def _get_singular(s):
    singular = IngredientParser.engine.singular_noun(s)
    if (singular):
        return singular
    else:
        return s


def load_ingredients(dir):
    '''Given a directory, load all ingredients under that directory and return
    an ingredient dictionary that maps ingredients to its category.
    '''

    ingredients_dict = dict()

    for (root, dirs, files) in os.walk(dir, topdown=True):
        for file in files:
            with open(os.path.join(root, file), 'r') as f:
                for ingredient in f:
                    ingredients_dict[ingredient.strip()] = file

    return ingredients_dict


def find_closest_match(ingredient, ingredients):
    '''Find the closest ingredient in a dictionary of ingredients
    that matches the given ingredient
    '''
    highest_score = float('-inf')
    closest_match = None

    for simple_ingredient in ingredients.keys():

        score = fuzz.ratio(ingredient, simple_ingredient)
        score += len(set(ingredient.split()) &
                     set(simple_ingredient.split())) * 100

        if score > highest_score:
            highest_score = score
            closest_match = simple_ingredient

    return closest_match


class IngredientParser:

    units = [
        'teaspoon',
        'tablespoon',
        'cup',
        'package',
        'pound',
        'dash',
    ]

    # Used to convert between single and plural forms
    engine = inflect.engine()

    # Build the regex for matching all units
    for i in range(0, len(units)):
        units.append(engine.plural(units[i]))
    # Must be sorted so the plural forms are matched against first
    units = sorted(units, key=len, reverse=1)

    # used for matching quantity units (e.g. cup, cups, teaspoon, and etc.)
    units_pattern = '(?:{})'.format(('|'.join(units)))

    # Tokens
    tokens = (
        'UNIT',
        'FRACTION',
        'NUMBER',
        'PREPNOTE',
        'WORD',
        'WHITESPACE'
    )

    @TOKEN(units_pattern)
    def t_UNIT(self, t):
        return t

    def t_FRACTION(self, t):
        r'(?:[0-9]+\s)?[1-9]\/[1-9]'
        return t

    def t_NUMBER(self, t):
        r'[1-9][0-9]*'
        return t

    def t_WHITESPACE(self, t):
        r'\s+'
        return t

    def t_WORD(self, t):
        r'[a-zA-Z\-\s\'®]+'
        return t

    t_PREPNOTE = r'[a-zA-Z\-\s,®0-9]+'

    def t_error(self, t):
        print("Illegal character '%s'" % t.value[0])
        t.lexer.skip(1)

    def p_ingredient(self, p):
        '''ingredient : FRACTION WHITESPACE UNIT WHITESPACE WORD
                      | FRACTION WHITESPACE WORD
                      | NUMBER WHITESPACE UNIT WHITESPACE WORD
                      | NUMBER WHITESPACE WORD
                      | ingredient PREPNOTE
        '''
        if (len(p) == 6):
            p[0] = p[5]
            self.ingredient = p[5]
        elif (len(p) == 4):
            p[0] = p[3]
            self.ingredient = p[3]
        elif (len(p) == 3):
            p[0] = p[1]
            self.ingredient = p[1]

    def p_error(self, p):
        self.ingredient = None
        if p:
            print("Syntax error at '%s'" % p.value)
        else:
            print('Unexpected end of input')

    def __init__(self):

        self.ingredient = None  # Variable to hold the parsed ingredient
        self.ingredients = load_ingredients(INGREDIENTS_DIR)

        # Build the lexer and parser
        lex.lex(module=self)
        yacc.yacc(module=self)

    def parse(self, s):
        '''Given an input string, attempt to parse and return the ingredient part
        '''
        s = _remove_parenthesis(s).strip()
        yacc.parse(s)

        if self.ingredient:
            singular_ingredient = _get_singular(self.ingredient)
            return find_closest_match(singular_ingredient, self.ingredients)
        else:
            raise ValueError('Failed to parse:', s)


if __name__ == '__main__':

    # TODO: Make them into tests

    test_ingredients = [
        r"1 1/4 cups all-purpose flour",
        r"1 egg",
        r"2 eggs",
        r"1/2 teaspoon salt",
        r"1/2 salt",
        r"1/2 tablespoon butter, melted",
        r"1/2 cup frozen blueberries, thawed",
        r"1/4 lemon, juiced (optional)",
        r"1 tablespoon confectioners' sugar, or to taste (optional)",
        r"1/2 (16 ounce) package linguine pasta",
        r"2 tablespoons chopped fresh parsley, or to taste",
        r"1/2 cup half-and-half",
        r"24 large shrimp in shell (21 to 25 per lb), peeled and deveined",
        r"1 pound large shrimp, peeled and deveined",
        r"1 1/2 teaspoons ground cinnamon",
        r"1 dash hot pepper sauce (such as Frank's RedHot®), or to taste",
        r"2 russet potatoes, scrubbed and cut into eighths",
        # r"8 bars Baby Ruth ™ candy bars, chopped",
        # r"1 broiler/fryer chicken, cut up and skin removed",
        # r"salt to taste",
        # r"salt and pepper to taste",
        # r"ground black pepper to taste",
        # r"1 (8 ounce) can water chestnuts ",
        # r"1 cup candied cherries",
        # r"2/3 cup canned pumpkin",
    ]

    parser = IngredientParser()
    for ingredient in test_ingredients:
        print(parser.parse(ingredient))
