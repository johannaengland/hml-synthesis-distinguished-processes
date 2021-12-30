# pylint: disable=missing-module-docstring, w0401, w0621, w0614, r0912, r1702, c0301, r0914, r0903, r1710, r0911, r0915, c0115, c0116, c0200


from copy import deepcopy

from evaluate import Token
from formula_functions import depth_formula, minimize_formula, negate_formula
from parse import parse

# Old version of the synthesis algorithm without the igraph library

# LTS representation:
# states: numbered 0 to n
# actions: array (check if actually needed in the end)
# transitions:  list x list x pairs:
#               on index i: all transitions from state i to other states, all together in a list
#               pair: (action, destination)


class LTS:
    states = 0
    actions = []
    transitions = []
    initial = 0

    def __init__(self, number_of_states, actions, transitions, initial):
        self.number_of_states = number_of_states
        self.actions = actions
        self.transitions = transitions
        self.initial = initial

    def change_initial(self, initial):
        self.initial = initial


input_lts = LTS(2, ["a", "b", "c"], [[["a", 0], ["b", 1]], [["c", 1]]], 0)

# input: lts, depth it should be unfolded to
# output: unfolded lts - partial tree representation, tree until depth n, normal lts after


def unfold(lts, depth=1):

    current_state = lts.initial
    representative = {current_state: current_state}
    depths = {current_state: 1}
    unfolded_lts = LTS(1, [], [], lts.initial)
    queue = [current_state]

    # tree needs to be of |depth| heigth
    while queue and depth > depths[current_state]:
        unfolded_lts.transitions.append([])
        for transition in lts.transitions[representative[current_state]]:
            if not transition[0] in unfolded_lts.actions:
                unfolded_lts.actions.append(transition[0])

            unfolded_lts.transitions[current_state].append(
                [transition[0], unfolded_lts.number_of_states]
            )
            queue.append(unfolded_lts.number_of_states)
            representative.update({unfolded_lts.number_of_states: transition[1]})
            depths.update({unfolded_lts.number_of_states: depths[current_state] + 1})
            unfolded_lts.number_of_states += 1

        queue.remove(current_state)
        current_state = queue[0]

    # adding the original LTS
    for i in queue:
        unfolded_lts.transitions.append([])

    for trans in lts.transitions:
        for i in trans:
            i[1] += unfolded_lts.number_of_states
        unfolded_lts.transitions.append(trans)
    unfolded_lts.number_of_states += lts.number_of_states

    # now we need to add the transitions between the unfolded part and the original LTS
    for current_state in queue:
        for transition in lts.transitions[representative[current_state]]:
            unfolded_lts.transitions[current_state].append(transition)

    return unfolded_lts


unfolded_lts = unfold(input_lts, 2)

# now onto the synthesis
def synthesis(input_lts_list, formula):
    if formula.ident == Token.ID_TRUE:
        # we don't need to change anything
        print("True")
        return input_lts_list

    if formula.ident == Token.ID_FALSE:
        # false should yield no results
        print("False")
        return [LTS(0, [], [], 0)]

    if formula.ident == Token.ID_POSSIBLE:
        # Try each e step, if none is successful, treat it as a false, include modified and non-modified version
        output_lts_list = []
        for input_lts in input_lts_list:
            success = False
            output_lts = LTS(
                input_lts.number_of_states,
                deepcopy(input_lts.actions),
                deepcopy(input_lts.transitions),
                input_lts.initial,
            )
            for trans in input_lts.transitions[input_lts.initial]:
                if trans[0] == formula.first:
                    output_lts.change_initial(trans[1])
                    result_lts_list = synthesis([output_lts], formula.second)
                    if result_lts_list[0].number_of_states > 0:
                        # the sythesis was successful, now we need to keep the unmodified version and add the modified version
                        # adding modified version:
                        #   add transition from current state to new state (number_of_states) and increase number_of_states
                        #   add transitions from new state to all reachable ones and do that recursively?
                        output_lts.change_initial(input_lts.initial)
                        output_lts_list.append(output_lts)
                        success = True
            if not success:
                return [LTS(0, [], [], 0)]
        return output_lts_list

    if formula.ident == Token.ID_NECESSARY:
        # for every action try the synthesis recursively, remove if it doesn't yield a result
        print("Necessary")
        output_lts_list = []
        for input_lts in input_lts_list:
            output_lts = LTS(
                input_lts.number_of_states,
                deepcopy(input_lts.actions),
                deepcopy(input_lts.transitions),
                input_lts.initial,
            )
            for trans in input_lts.transitions[input_lts.initial]:
                if trans[0] == formula.first:
                    output_lts.change_initial(trans[1])
                    result_lts_list = synthesis([output_lts], formula.second)
                    for result_lts in result_lts_list:
                        # recursive synthesis does not yield a result
                        if result_lts.number_of_states == 0:
                            output_lts.transitions[input_lts.initial].remove(trans)
                            output_lts.change_initial(input_lts.initial)
                            output_lts_list.append(output_lts)
                        else:
                            result_lts.change_initial(input_lts.initial)
                            output_lts_list.append(result_lts)
        return output_lts_list

    if formula.ident == Token.ID_AND:
        print("And")
        output_lts_list = synthesis(input_lts_list, formula.first)
        copy_lts_list = []
        i = False
        while True:
            # alternate both parts of the formula
            for output_lts in output_lts_list:
                copy_lts_list.append(
                    LTS(
                        output_lts.number_of_states,
                        deepcopy(output_lts.actions),
                        deepcopy(output_lts.transitions),
                        output_lts.initial,
                    )
                )
            if i:
                output_lts_list = synthesis(output_lts_list, formula.first)
            else:
                output_lts_list = synthesis(output_lts_list, formula.second)

            # until it doesn't change anymore
            for j in range(0, len(output_lts_list)):
                if not output_lts_list[j].transitions == copy_lts_list[j].transitions:
                    i = not i
                    break

            # lists are the same
            if j == len(output_lts_list) - 1:
                break

        return output_lts_list

    if formula.ident == Token.ID_OR:
        # we try both parts separately and return the result(s)
        print("Or")
        output_lts_list = synthesis(input_lts_list, formula.first)
        output_lts_list2 = synthesis(input_lts_list, formula.second)

        if output_lts_list[0].number_of_states == 0:
            return output_lts_list2
        if output_lts_list2[0].number_of_states == 0:
            return output_lts_list
        for output_lts2 in output_lts_list2:
            for output_lts in output_lts_list:
                if output_lts.transitions == output_lts2.transitions:
                    break
            # check (possible lambda function)
            output_lts_list.append(output_lts2)
        return output_lts_list


print(unfolded_lts.transitions)
# parsedFormula = parse('[a]false')
# parsedFormula = parse('[b]false')
# parsedFormula = parse('([a]false and [b]false)')
# parsedFormula = parse('([b]false and [a]false)')
# parsedFormula = parse('([a][a]false and [b]false)')
# parsedFormula = parse('([a]false and [b][c]false)')
# parsedFormula = parse('([a][a]false and [b][c]false)')

parsedFormula = parse("([a]false or [b]false)")
# parsedFormula = parse('([b]false or [a]false)')
# parsedFormula = parse('([a][a]false or [b]false)')
# parsedFormula = parse('([a]false or [b][c]false)')
# parsedFormula = parse('([a][a]false or [b][c]false)')

synthesisedLTSList = synthesis([unfolded_lts], parsedFormula)
print("Final results:")
for synthesisedLTS in synthesisedLTSList:
    print(synthesisedLTS.transitions)


# Formula functions related to earlier approaches/attempts
def increase_formula_depth(formula, alphabet, changed=False):
    """
    Returns a list of deepeer formulas.

    Parameters:
        formula (Token): A formula
        alphabet ([str]): List of the possible labels that will be added to the formula
        changed (bool): Helper to indicate if the formula has already been changed

    Returns:
        formula_list ([Token]): List of formulas that are deeper than the input formula by having each a label from the alphabet attached
    """
    if changed and formula.ident in [Token.ID_TRUE, Token.ID_FALSE]:
        formula_list = []
        for letter in alphabet:
            formula_list.extend(
                [parse("<" + letter + ">true"), parse("[" + letter + "]false")]
            )
    elif not changed and formula.ident in [Token.ID_TRUE, Token.ID_FALSE]:
        formula_list = [formula]
    elif formula.ident in [Token.ID_NECESSARY, Token.ID_POSSIBLE]:
        formula_list = []
        for result in increase_formula_depth(formula.second, alphabet, changed):
            new_formula = Token(formula.ident)
            new_formula.first = formula.first
            new_formula.second = result
            formula_list.append(new_formula)
    elif formula.ident in [Token.ID_AND, Token.ID_OR]:
        formula_list = []
        if depth_formula(formula.first) >= depth_formula(formula.second):
            for result in increase_formula_depth(formula.first, alphabet, True):
                new_formula = Token(formula.ident)
                new_formula.first = result
                new_formula.second = formula.second
                formula_list.append(new_formula)
        if depth_formula(formula.first) <= depth_formula(formula.second):
            for result in increase_formula_depth(formula.second, alphabet, True):
                new_formula = Token(formula.ident)
                new_formula.first = formula.first
                new_formula.second = result
                formula_list.append(new_formula)
    return formula_list


def reduce_formula_depth(formula, changed=False):
    """
    Returns a list of shallower formulas.

    Parameters:
        formula (Token): A formula
        changed (bool): Helper to indicate if the formula has already been changed

    Returns:
        formula_list ([Token]): List of formulas that are shallower than the input formula
    """

    formula = minimize_formula(formula)
    if depth_formula(formula) < 1:
        raise ValueError("The input formula must have at least depth 1.")
    if formula.ident in (Token.ID_NECESSARY, Token.ID_POSSIBLE):
        formula_list = []
        if formula.second.ident in (Token.ID_TRUE, Token.ID_FALSE) and not changed:
            formula_list.append(Token(Token.ID_TRUE))
            changed = True
        elif formula.second.ident in (Token.ID_TRUE, Token.ID_FALSE) and changed:
            formula_list.append(formula)
        else:
            results, changed = reduce_formula_depth(formula.second, changed)
            for result in results:
                new_formula = Token(formula.ident)
                new_formula.first = formula.first
                new_formula.second = result
                formula_list.append(new_formula)
    elif formula.ident in [Token.ID_AND, Token.ID_OR]:
        formula_list = []
        depth_first = depth_formula(formula.first)
        depth_second = depth_formula(formula.second)
        if depth_first >= depth_second:
            results, changed = reduce_formula_depth(formula.first, changed)
            for result in results:
                new_formula = Token(formula.ident)
                new_formula.first = result
                new_formula.second = formula.second
                formula_list.append(new_formula)
            if depth_first == depth_second:
                changed = False
        if depth_first <= depth_second:
            results, changed = reduce_formula_depth(formula.second, changed)
            for result in results:
                new_formula = Token(formula.ident)
                new_formula.first = formula.first
                new_formula.second = result
                formula_list.append(new_formula)

    return [minimize_formula(f) for f in formula_list], changed


def generate_formulas(formula_str):
    """
    Returns two list of formulas, where one satisfies the input formula and the other doesn't.

    Parameters:
        formula_str (str): A formula in string representation

    Returns:
        satisfying_formulas ([Token]): Shallower formulas combined with the input formula through and
        non_satisfying_formulas ([Token]): Shallower formulas combined with the negation of the input formula through and
    """

    input_formula = parse(formula_str)
    shallow_formulas, _ = reduce_formula_depth(input_formula)
    satisfying_formulas = []
    non_satisfying_formulas = []

    for shallow_formula in shallow_formulas:
        formula1 = Token(Token.ID_AND)
        formula1.first = input_formula
        formula1.second = shallow_formula
        satisfying_formulas.append(formula1)

        formula2 = Token(Token.ID_AND)
        formula2.first = negate_formula(input_formula)
        formula2.second = shallow_formula
        non_satisfying_formulas.append(formula2)

    return satisfying_formulas, non_satisfying_formulas
