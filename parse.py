"""This code was re-used from github.com/tobchen/TobyHML with permission from the author"""

from evaluate import Token


def parse(hml):
    try:
        result, _ = parse_formula(''.join(hml.split()))
    except ParseException as e:
        raise e
    return result


def parse_formula(formula):
    # true
    if formula[:4] == 'true':
        # print('true')

        result = Token(Token.ID_TRUE)
        formula = formula[4:]

    # false
    elif formula[:5] == 'false':
        # print('false')

        result = Token(Token.ID_FALSE)
        formula = formula[5:]

    # ( FORMULA and/or FORMULA )
    elif formula[0] == '(':
        # print('binary')

        # Get rid of '('
        formula = formula[1:]

        result = Token(Token.ID_ERROR)

        try:
            result.first, formula = parse_formula(formula)
        except ParseException as e:
            raise e

        if formula[:3] == 'and':
            result.change(Token.ID_AND)
            formula = formula[3:]
        elif formula[:2] == 'or':
            result.change(Token.ID_OR)
            formula = formula[2:]
        else:
            raise ParseException('Unknown binary operation!')

        try:
            result.second, formula = parse_formula(formula)
        except ParseException as e:
            raise e

        # Get rid of ')'
        if formula[0] == ')':
            formula = formula[1:]
        else:
            raise ParseException(') missing!')

    # < LABEL > FORMULA
    elif formula[0] == '<':
        # print('possible')

        # Get rid of '<'
        formula = formula[1:]

        result = Token(Token.ID_POSSIBLE)
        try:
            label, formula = parse_label(formula)
            result.set_first(label)
        except ParseException as e:
            raise e

        # Get rid of '>'
        if formula[0] == '>':
            formula = formula[1:]
        else:
            raise ParseException('> missing!')

        rest, formula = parse_formula(formula)
        result.set_second(rest)

    # [ LABEL ] FORMULA
    elif formula[0] == '[':
        # print('necessary')

        # Get rid of '['
        formula = formula[1:]

        result = Token(Token.ID_NECESSARY)
        try:
            label, formula = parse_label(formula)
            result.set_first(label)
        except ParseException as e:
            raise e

        # Get rid of ']'
        if formula[0] == ']':
            formula = formula[1:]
        else:
            raise ParseException('] missing!')

        rest, formula = parse_formula(formula)
        result.set_second(rest)

    # ERROR
    else:
        raise ParseException('Unknown formular start!')

    return result, formula


def parse_label(formula):
    i = 0
    while formula[i].isalnum():
        i += 1
    return formula[:i], formula[i:]


class ParseException(Exception):
    def __init__(self, value):
        self.value = value

    @property
    def __str__(self):
        return repr(self.value)



# FORMULA = CONST | UNARY | '(' BINARY ')'
# CONST = 'true' | 'false'
# UNARY = '<' ([a-z]|[A-Z]|[0-9])+ '>' FORMULA |
#         '[' ([a-z]|[A-Z]|[0-9])+ ']' FORMULA
# BINARY = FORMULA 'and' FORMULA | FORMULA 'or' FORMULA