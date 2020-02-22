import inflect
import ply.lex as lex
import ply.yacc as yacc
from ply.lex import TOKEN
import re


import spacy
nlp = spacy.load("en_core_web_sm")


def remove_parenthesis(s):
    return re.sub(r" ?\([^)]+\)", "", s)

def get_singular(s):
    singular = engine.singular_noun(s)
    if (singular):
        return singular
    else:
        return s

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
]

# Global variable that holds the parsed ingredient
ingredient = None

units = [
    'teaspoon',
    'tablespoon',
    'cup',
    'package',
    'pound',
    'dash'
]

# Build the regex for matching all units
engine = inflect.engine()
for i in range(0, len(units)):
    units.append(engine.plural(units[i]))
# Must be sorted so the plural forms are matched against first
units = sorted(units, key=len, reverse=1)

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
def t_UNIT(t):
    return t


def t_FRACTION(t):
    r'(?:[0-9]+\s)?[1-9]\/[1-9]'
    return t


def t_NUMBER(t):
    r'[1-9][0-9]*'
    return t


def t_WHITESPACE(t):
    r'\s+'
    return t


def t_WORD(t):
    r'[a-zA-Z\-\s\']+'
    return t


t_PREPNOTE = r'[a-zA-Z\-\s,]+'


def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)


def p_ingredient(p):
    '''ingredient : FRACTION WHITESPACE UNIT WHITESPACE WORD
                  | FRACTION WHITESPACE WORD
                  | NUMBER WHITESPACE UNIT WHITESPACE WORD
                  | NUMBER WHITESPACE WORD
                  | ingredient PREPNOTE
    '''
    global ingredient
    if (len(p) == 6):
        p[0] = p[5]
        ingredient = p[5]
    elif (len(p) == 4):
        p[0] = p[3]
        ingredient = p[3]
    elif (len(p) == 3):
        p[0] = p[1]
        ingredient = p[1]


def p_error(p):
    global ingredient
    ingredient = None
    if p:
        print("Syntax error at '%s'" % p.value)
    else:
        print('Unexpected end of input')


if __name__ == '__main__':
    lex.lex()
    yacc.yacc()
    for ingredient in test_ingredients:
        ingredient = remove_parenthesis(ingredient).strip()
        yacc.parse(ingredient)
        if ingredient:

            doc = nlp(ingredient)
            for chunk in doc.noun_chunks:
                if (chunk.root.dep_ == 'ROOT' or chunk.root.dep_== 'dobj'):
                    ingredient = chunk.root.text
                    ingredient = get_singular(ingredient)
            print('Got ingredient:', ingredient)
        else:
            print('Parse error')
