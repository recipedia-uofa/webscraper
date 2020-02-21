import inflect
import ply.lex as lex
import ply.yacc as yacc
from ply.lex import TOKEN

# import spacy
# nlp = spacy.load("en_core_web_sm")

test_ingredients = [
    r'1 1/4 cups all-purpose flour',
    r'1 egg',
    r'2 eggs',
    r'1/2 teaspoon salt',
    r'1/2 tablespoon butter, melted',
    r'1/2 cup frozen blueberries, thawed',
    # r'1/4 lemon, juiced (optional)',
]

# Global variable that holds the parsed ingredient
ingredient = None

units = [
    'teaspoon',
    'tablespoon',
    'cup',
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
    'AMOUNT',
    'QUANTITY',
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
    r'[0-9]'
    return t


def t_WHITESPACE(t):
    r'\s+'
    return t


def t_WORD(t):
    r'[a-zA-Z\-\s]+'
    return t


def t_PREPNOTE(t):
    r'[a-zA-Z\-\s,]+'
    return t


def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)


precedence = (
    ('right', 'NUMBER'),
)


def p_ingredient(p):
    '''ingredient : quantity WHITESPACE WORD PREPNOTE
                  | quantity WHITESPACE WORD
    '''
    global ingredient
    ingredient = p[3]


def p_quantity(p):
    '''quantity : FRACTION WHITESPACE UNIT
                | NUMBER WHITESPACE UNIT
                | NUMBER
    '''
    p[0] = ''.join(p[1:])


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
        a = yacc.parse(ingredient)
        if ingredient:
            print('Got ingredient:', ingredient)
        else:
            print('Parse error')
