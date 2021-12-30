"""This code was re-used from github.com/tobchen/TobyHML with permission from the author"""

class LTS:

    """A labeled transition system class."""

    def __init__(self):
        self.states = []

    def add_state(self, state_name):
        state_found = False
        for state in self.states:
            if state.name == state_name:
                state_found = True
                break
        if not state_found:
            self.states.append(self.State(state_name))

    def add_transition(self, state_from, transition, state_to):
        self.add_state(state_from)
        self.add_state(state_to)
        for state in self.states:
            if state.name == state_from:
                state.add_transition(transition, state_to)
                break

    def remove_state(self, state_name):
        # First remove state from list of states
        self.states = [state for state in self.states
                       if state.name != state_name]
        # Now remove state from other state's transitions
        for state in self.states:
            for transition in state.transitions:
                state.remove_transition_to(transition.name, state_name)

    def remove_transition_to(self, state_from, transition, state_to):
        for state in self.states:
            if state.name == state_from:
                state.remove_transition_to(transition, state_to)

    def remove_transition_from(self, state_from, transition):
        for state in self.states:
            if state.name == state_from:
                state.remove_transition_from(transition)

    def reset(self):
        self.states.clear()

    def __str__(self):
        result = ''
        divider = ''
        for state in self.states:
            result += (divider + str(state))
            divider = '\n'
        return result

    class State:
        def __init__(self, name):
            self.name = name
            self.transitions = []

        def add_transition(self, name, to_state):
            transition_found = False
            for transition in self.transitions:
                if transition.name == name:
                    transition.add_to_state(to_state)
                    transition_found = True
                    break
            if not transition_found:
                self.transitions.append(self.Transition(name, to_state))

        def remove_transition_to(self, name, to_state):
            # Remove state from transition
            for transition in self.transitions:
                if transition.name == name:
                    transition.to_states = [state for state in
                                            transition.to_states
                                            if state != to_state]
            # Now there could be an empty transition
            # Remove it, if neccessary
            self.transitions = [transition for transition in self.transitions
                                if len(transition.to_states) > 0]

        def remove_transition_from(self, name):
            self.transitions = [transition for transition in self.transitions
                                if transition.name != name]

        def __str__(self):
            result = self.name
            for transition in self.transitions:
                result += ('\n\t' + str(transition))
            return result

        class Transition:
            def __init__(self, name, to_state=None):
                self.name = name
                self.to_states = []
                if to_state is not None:
                    self.to_states.append(to_state)

            def add_to_state(self, to_state):
                to_found = False
                for to in self.to_states:
                    if to == to_state:
                        to_found = True
                        break
                if not to_found:
                    self.to_states.append(to_state)

            def __str__(self):
                return self.name + " -> " + str(self.to_states)