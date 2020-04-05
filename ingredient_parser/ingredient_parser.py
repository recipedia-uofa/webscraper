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
import functools
from load_ingredients import load_ingredients

nlp = spacy.load("en_core_web_sm")
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


class IngredientParser:

    MATCHING_THRESHOLD = 20

    # Used to convert between single and plural forms
    engine = inflect.engine()

    def __init__(self, benchmark=False):
        self.ingredients, self.alias_map = load_ingredients()

        self.benchmark = False

        if benchmark:
            self.benchmark = True
            self.num_ingredients_parsed = 0
            self.matching_parse_errors = collections.Counter()
            self.scores = list()

    def get_score(self, expression, fixed_ingredient):
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
                    matched += 1
                expression_copy.pop(local_highest_idx)

        matching_modifier = float(matched) / float(fixed_ingredient_len)
        return score * matching_modifier

    @functools.lru_cache(maxsize=None)
    def find_closest_match(self, expression):
        '''Find the closest ingredient in the dictionary of ingredients
        that matches the given expression
        '''
        highest_score = float('-inf')
        closest_match = None

        for fixed_ingredient in self.ingredients.keys():

            score = self.get_score(expression, fixed_ingredient)

            if score > highest_score:
                highest_score = score
                closest_match = fixed_ingredient

            if score == highest_score:
                if len(fixed_ingredient) > len(closest_match):
                    closest_match = fixed_ingredient

        if self.benchmark:
            self.scores.append(highest_score)

        if highest_score < IngredientParser.MATCHING_THRESHOLD:
            if self.benchmark:
                self.matching_parse_errors[(expression, closest_match, highest_score)] += 1
            closest_match = None
        else:
            # Convert alias
            closest_match = self.alias_map[closest_match]
            # print(expression, "----", closest_match, highest_score)

        return closest_match

    def parse(self, s):
        """
        Given an input string, attempt to parse and return the ingredient part
        """

        if self.benchmark:
            self.num_ingredients_parsed += 1

        s = _remove_parenthesis(s).strip()
        s = remove_adopositions(s, nlp)
        s = _get_singular(s)
        return self.find_closest_match(s)


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
