"""This code was re-used from github.com/tobchen/TobyHML with permission from the author"""

# TODO Maybe use NetworkX instead of own LTS
def evaluate(start_token, lts):
    return generate_set(start_token, lts)


def generate_set(token, lts):
    result = set()
    if token.ident == Token.ID_TRUE:
        result = set_from_lts(lts)

    elif token.ident == Token.ID_FALSE:
        result = set()

    elif token.ident == Token.ID_AND:
        result = generate_set(token.first, lts) & \
            generate_set(token.second, lts)

    elif token.ident == Token.ID_OR:
        result = generate_set(token.first, lts) | \
            generate_set(token.second, lts)

    elif token.ident == Token.ID_POSSIBLE:
        work_set = generate_set(token.second, lts)
        result = set()
        for state in lts.states:
            go_in = False
            for transition in state.transitions:
                if transition.name == token.first:
                    for state2 in transition.to_states:
                        if state2 in work_set:
                            go_in = True
                            break
                    break
            if go_in:
                result.add(state.name)

    elif token.ident == Token.ID_NECESSARY:
        work_set = generate_set(token.second, lts)
        result = set()
        for state in lts.states:
            go_in = True
            for transition in state.transitions:
                if transition.name == token.first:
                    for state2 in transition.to_states:
                        if state2 not in work_set:
                            go_in = False
                            break
                    break
            if go_in:
                result.add(state.name)

    else:
        # TODO Yeah, what to do?
        pass

    return result


def set_from_lts(lts):
    result = set()
    for state in lts.states:
        result.add(state.name)
    return result


class Token:
    ID_ERROR = -1
    ID_TRUE = 0
    ID_FALSE = 1
    ID_AND = 2
    ID_OR = 3
    ID_POSSIBLE = 4
    ID_NECESSARY = 5

    def __init__(self, ident):
        self.ident = ident
        self.first = None
        self.second = None

    def change(self, ident):
        self.ident = ident

    def set_first(self, first):
        self.first = first

    def set_second(self, second):
        self.second = second