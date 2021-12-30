# pylint: disable=missing-module-docstring, w0404, r0912
from evaluate import Token
from parse import Token, parse


def formula_to_str(formula):
    """Returns a string representation of a formula.

    Parameters:
        formula (Token): A formula

    Returns:
        formula_str (str): String representation of the input formula
    """

    if formula.ident == Token.ID_TRUE:
        formula_string = "true"
    elif formula.ident == Token.ID_FALSE:
        formula_string = "false"
    elif formula.ident == Token.ID_OR:
        formula_string = (
            "("
            + formula_to_str(formula.first)
            + " or "
            + formula_to_str(formula.second)
            + ")"
        )
    elif formula.ident == Token.ID_AND:
        formula_string = (
            "("
            + formula_to_str(formula.first)
            + " and "
            + formula_to_str(formula.second)
            + ")"
        )
    elif formula.ident == Token.ID_POSSIBLE:
        formula_string = "<" + formula.first + ">" + formula_to_str(formula.second)
    elif formula.ident == Token.ID_NECESSARY:
        formula_string = "[" + formula.first + "]" + formula_to_str(formula.second)
    return formula_string


def minimize_formula(formula):
    """
    Removes trivial true/false in combination with and/or or possible/necessary.

    Parameters:
        formula (Token): A formula

    Returns:
        new_formula (Token): Minimized version of input formula
    """

    if formula.ident in [Token.ID_TRUE, Token.ID_FALSE]:
        new_formula = formula
    elif formula.ident in [Token.ID_NECESSARY, Token.ID_POSSIBLE]:
        result = minimize_formula(formula.second)
        if result.ident == Token.ID_TRUE and formula.ident == Token.ID_NECESSARY:
            new_formula = Token(Token.ID_TRUE)
        elif result.ident == Token.ID_FALSE and formula.ident == Token.ID_POSSIBLE:
            new_formula = Token(Token.ID_FALSE)
        else:
            new_formula = Token(formula.ident)
            new_formula.first = formula.first
            new_formula.second = result
    elif formula.ident == Token.ID_OR:
        formula.first = minimize_formula(formula.first)
        formula.second = minimize_formula(formula.second)
        if Token.ID_TRUE in [formula.first.ident, formula.second.ident]:
            new_formula = Token(Token.ID_TRUE)
        elif formula.first.ident == Token.ID_FALSE:
            new_formula = formula.second
        elif formula.second.ident == Token.ID_FALSE:
            new_formula = formula.first
        else:
            new_formula = formula
    elif formula.ident == Token.ID_AND:
        formula.first = minimize_formula(formula.first)
        formula.second = minimize_formula(formula.second)
        if formula.first.ident == Token.ID_FALSE:
            new_formula = Token(Token.ID_FALSE)
        elif formula.first.ident == Token.ID_TRUE:
            new_formula = formula.second
        elif formula.second.ident == Token.ID_TRUE:
            new_formula = formula.first
        else:
            new_formula = formula

    return new_formula


def depth_formula(formula):
    """Returns the depth of a formula.

    Parameters:
        formula (Token): A formula

    Returns:
        depth (int): Depth of the input formula
    """

    if formula.ident in (Token.ID_TRUE, Token.ID_FALSE):
        return 0
    if formula.ident in (Token.ID_OR, Token.ID_AND):
        return 0 + max(depth_formula(formula.first), depth_formula(formula.second))
    return 1 + depth_formula(formula.second)


def negate_formula(formula):
    """Returns a negated version of the input formula.

    Parameters:
        formula (Token): A formula

    Returns:
        negated_formula (Token): Negated version of the input formula
    """

    if formula.ident == Token.ID_TRUE:
        return parse("false")

    if formula.ident == Token.ID_FALSE:
        return parse("true")

    if formula.ident == Token.ID_OR:
        negated_formula = Token(Token.ID_AND)
        negated_formula.first = negate_formula(formula.first)
        negated_formula.second = negate_formula(formula.second)

    elif formula.ident == Token.ID_AND:
        negated_formula = Token(Token.ID_OR)
        negated_formula.first = negate_formula(formula.first)
        negated_formula.second = negate_formula(formula.second)

    elif formula.ident == Token.ID_NECESSARY:
        negated_formula = Token(Token.ID_POSSIBLE)
        negated_formula.first = formula.first
        negated_formula.second = negate_formula(formula.second)

    elif formula.ident == Token.ID_POSSIBLE:
        negated_formula = Token(Token.ID_NECESSARY)
        negated_formula.first = formula.first
        negated_formula.second = negate_formula(formula.second)

    return negated_formula
