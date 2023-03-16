from .grammar import Grammar
from collections import defaultdict

class FA:
    '''
    A finite automaton is represented by 5 variables.

    :param S: set of states
    :param A: alphabet, which is a set of symbols
    :param s0: starting state
    :param d: the state-transition function
    :param F: set of final states
    '''

    def __init__(self, S: set[str], A: set[str], s0: str, d: dict[tuple[set[str], str], set[str]], F: set[str]):
        self.S = S
        self.A = A
        self.s0 = s0
        self.d = d
        self.F = F

    def __repr__(self):
        return ', '.join([str(x) for x in [self.S, self.A, self.s0, self.d, self.F]])

    def draw(self, dirname, fn):
        import graphviz
        dot = graphviz.Digraph(fn, format='svg')
        dot.attr(rankdir='LR')

        for s in self._get_final_states():
            dot.attr('node', shape='doublecircle')
            dot.node(s)

        for s in self._get_nonfinal_states():
            dot.attr('node', shape='circle')
            dot.node(s)

        for s0, s1, label in self._get_edges():
            dot.edge(s0, s1, label=label)

        fn = dot.render(directory=dirname).replace('\\', '/')
        return fn


class DFA(FA):
    '''
    This Deterministic finite automaton is similar to the NFA,
    with the distinction that states are now represented by sets, and not strings.
    For example, in the transitions dict,
    a value is a set of states denoting a single "node" in the DFA graph,
    not multiple possible states like in the case of an NFA,
    whereas the keys are now represented by tuple[set[State], Symbol]
    The other variables, S, s0 and F also reflect this change.

    For example, the NFA::

        S = {'B', 'ε', 'A'}
        A = {'a', 'b'}
        s0 = 'A'
        d = {('A', 'a'): {'A', 'B'}, ('B', 'b'): {'ε'}}
        F = {'ε', 'A'}

    is transformed into the following DFA::

        S = {{'A'}, {'A', 'B'}, {'ε'}}
        A = {'a', 'b'}
        s0 = {'A'}
        d = {
            ({'A'}, 'a'): {'A', 'B'},
            ({'A', 'B'}, 'a'): {'A', 'B'},
            ({'A', 'B'}, 'b'): {'ε'}
        }
        F = {{'A'}, {'A', 'B'}, {'ε'}}
    '''

    def verify(self, w):
        s = self.s0
        for l in w:
            s2 = self.d.get((frozenset(s), l))
            if not s2:
                return False
            s = s2
        return s in self.F

    def _get_nonfinal_states(self):
        return [str(set(T)) for T in self.S - self.F]

    def _get_final_states(self):
        return [str(set(T)) for T in self.F]

    def _get_edges(self):
        e = []
        for k, v in self.d.items():
            e.append((str(set(k[0])), str(v), str(k[1])))
        return e


class NFA(FA):
    '''
    Each rule in the regular grammar is treated as follows:

    1) A -> aB

        - a transition is created: (A, a): B
        - "a" is added to the alphabet

    2) A -> a

        - a transition is created: (A, a): ε
        - a final state is added: ε
        - "a" is added to the alphabet

    3) B -> ε

        - a final state is added: B

    For example, the formal grammar::

        A -> aA
        A -> aB
        A -> ε
        B -> b

    is transformed into the following NFA::

        S = {'B', 'ε', 'A'}
        A = {'a', 'b'}
        s0 = 'A'
        d = {('A', 'a'): {'A', 'B'}, ('B', 'b'): {'ε'}}
        F = {'ε', 'A'}
    '''

    def from_grammar(g : Grammar):
        '''This function only recognizes *strictly* regular grammars'''
        assert g.type() == Grammar.Type.REGULAR
        d = defaultdict(set)
        F = set()
        A = set()

        for head, tails in g.P.items():
            head = head[0]  # in a regular grammar, head is a single nonterminal

            for tail in tails:
               if len(tail) == 0:
                   F |= {head}
               elif len(tail) == 1:
                   d[(head, tail[0])] |= {"ε"}
                   F |= {"ε"}
                   A |= {tail[0]}
               elif len(tail) == 2:
                   d[(head, tail[0])] |= {tail[1]}
                   A |= {tail[0]}

        d = dict(d)  # demote from defaultdict
        return NFA(S = g.VN | F, A = A, s0 = g.S, d = d, F = F)

    def to_grammar(self) -> Grammar:
        VT = {k[1] for k in self.d.keys()}

        P = defaultdict(set)
        for k, v in self.d.items():
            P[k[0],] |= {(k[1], s) if s != "ε" else (k[1],) for s in v}
        for s in self.F:
            if s == "ε":
                continue
            P[s,] |= {tuple()}
        P = dict(P)

        return Grammar(VN = self.S - {"ε"}, VT = VT, P = P, S = self.s0)

    def to_DFA(self) -> DFA:
        '''For an explanation of the algo, check out the dragon book.'''

        def move(T, a):
            '''Returns the set of states reachable from any state in T via symbol a'''
            return {s for S in T if (u := self.d.get((S, a))) for s in u}

        dstat = {frozenset({self.s0}): False} # Dstates (store marked/unmarked sets of states T)
        dtran = {} # Dtran (transition table)
        while not all(dstat.values()):
            T = next((k for k,v in dstat.items() if not v))
            dstat[T] = True
            for a in self.A:
                U = move(T, a)
                if not U:
                    continue
                if frozenset(U) not in dstat:
                    dstat[frozenset(U)] = False
                dtran[(T, a)] = U

        F = {T for T in dstat if any(s in self.F for s in T)}
        return DFA(S = set(dstat.keys()), A = self.A, s0 = {self.s0,}, d = dtran, F = F)

    def is_deterministic(self):
       return all([len(l) == 1 for l in self.d.values()])

    def _get_nonfinal_states(self):
        return self.S - self.F

    def _get_final_states(self):
        return self.F

    def _get_edges(self):
        e = []
        for k, v in self.d.items():
            for s in v:
                e.append((k[0], str(s), str(k[1])))
        return e

