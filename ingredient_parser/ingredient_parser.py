import inflect
import ply.lex as lex
import ply.yacc as yacc
from ply.lex import TOKEN
import re
import os
from fuzzywuzzy import fuzz
import string
from scipy.special import softmax
import spacy
import collections

nlp = spacy.load("en_core_web_sm")
INGREDIENTS_DIR = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), 'ingredients')
THRESHOLD = 80
separators = r'[{}]'.format(string.punctuation + r'\s')


def _remove_parenthesis(s):
    return re.sub(r" ?\([^)]+\)", "", s)


def _get_singular(s):
    singular = IngredientParser.engine.singular_noun(s)
    if (singular):
        return singular
    else:
        return s


def split(s, separators):
    '''Split s with a string of separators (e.g ",.-")
    '''
    sep = r'[{}]'.format(separators)
    return re.split(sep, s)


def threshold_ratio(s1, s2, threshold):
    '''Perform fuzz.ratio on s1 and s2 but return 0 if the ratio
    is lower than threshold
    '''
    ratio = fuzz.ratio(s1, s2)
    if ratio < threshold:
        return 0
    else:
        return ratio


def get_score(expression, fixed_ingredient):
    '''Get a score between expression and fixed_ingredient by comparing how
    similar they are.
    '''

    score = 0

    expression = split(expression, string.punctuation + r'\s')
    expression.reverse()
    expression_len = len(expression)

    fixed_ingredient = split(fixed_ingredient, string.punctuation + r'\s')
    fixed_ingredient.reverse()
    fixed_ingredient_len = len(fixed_ingredient)

    matched = 0

    expression_copy = list(expression)

    # Using softmax so the weights add up to 1
    # Reversed so it is more heavily weighted towards the end of the string
    weight = list(range(fixed_ingredient_len))
    weight.reverse()
    weight = softmax(weight)

    for i in range(0, len(fixed_ingredient)):
        local_highest_score = float('-inf')
        local_highest_idx = 0
        if len(expression_copy) > 0:
            for j in range(0, len(expression_copy)):
                ratio = threshold_ratio(
                    fixed_ingredient[i], expression_copy[j], THRESHOLD)
                if ratio > local_highest_score:
                    local_highest_score = ratio
                    local_highest_idx = j
            score += weight[i] * local_highest_score
            if local_highest_score > 0:
                matched += 2
            expression_copy.pop(local_highest_idx)

    matching_modifier = float(
        matched) / float(expression_len + fixed_ingredient_len)
    return score * matching_modifier


def remove_adopositions(s, nlp):
    '''Given a string s and the spacy nlp engine, return a string without adpositions.
    For example, "shrimp in shell" -> "shrimp".
    '''
    doc = nlp(s)
    indices_to_remove = []
    for token in doc:
        if token.pos_ == 'ADP':
            for tok in token.subtree:
                indices_to_remove.append(tok.i)
    return ' '.join([token.text for token in doc if token.i not in indices_to_remove])


def load_ingredients(dir):
    '''Given a directory, load all ingredients under that directory and return
    an ingredient dictionary that maps ingredients to its category.
    '''

    ingredients_dict = dict()

    for file in os.listdir(dir):
        if file not in ['.pytest_cache']:
            with open(os.path.join(dir, file), 'r') as f:
                for ingredient in f:
                    ingredients_dict[ingredient.strip()] = file

    return ingredients_dict


def find_closest_match(expression, ingredients):
    '''Find the closest ingredient in a dictionary of ingredients
    that matches the given expression
    '''
    highest_score = float('-inf')
    closest_match = None

    for fixed_ingredient in ingredients.keys():

        score = get_score(expression, fixed_ingredient)

        if score > highest_score:
            highest_score = score
            closest_match = fixed_ingredient

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

    INGREDIENTS_TO_IGNORE = [
        'salt',
        'black pepper',
        'water',
        'skewers',
        'coloring',
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
        r'[^0-9^,]+'
        return t

    t_PREPNOTE = r'.+'

    def t_error(self, t):
        print("Illegal character '%s'" % t.value[0])
        t.lexer.skip(1)

    def p_ingredient(self, p):
        '''ingredient : FRACTION WHITESPACE UNIT WHITESPACE WORD
                      | FRACTION WHITESPACE WORD
                      | NUMBER WHITESPACE UNIT WHITESPACE WORD
                      | NUMBER WHITESPACE WORD
                      | ingredient PREPNOTE
                      | WORD
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
        elif (len(p) == 2):
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

        # stats
        self.num_ingredients_parsed = 0
        self.quantity_parse_errors = collections.Counter()

        # Build the lexer and parser
        lex.lex(module=self)
        yacc.yacc(module=self)

    def parse(self, s):
        '''Given an input string, attempt to parse and return the ingredient part
        '''
        self.ingredient = None
        self.num_ingredients_parsed += 1

        for ignored_ingredient in IngredientParser.INGREDIENTS_TO_IGNORE:
            if ignored_ingredient in s:
                return None

        s = _remove_parenthesis(s).strip()
        s = remove_adopositions(s, nlp)
        yacc.parse(s)

        if self.ingredient:
            singular_ingredient = _get_singular(self.ingredient)
            return find_closest_match(singular_ingredient, self.ingredients)
        else:
            self.quantity_parse_errors[s] += 1
            raise ValueError('Failed to parse:', s)


if __name__ == '__main__':

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
        r"Fresh raspeberries",
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
