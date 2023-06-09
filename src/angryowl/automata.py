from __future__ import annotations
from collections import defaultdict
from collections.abc import Hashable, Iterable
from . import grammar

class FA:
    '''
    A `formal automaton <https://en.wikipedia.org/wiki/Finite-state_machine#Mathematical_model>`_
    is represented by 5 variables.

    :param S: set of states
    :param A: alphabet (set of symbols)
    :param s0: initial state
    :param d: the state-transition function
    :param F: set of final states
    '''

    def __init__(self, S: set[Hashable], A: set[Hashable], s0: Hashable,
                 d: dict[tuple[set[Hashable], Hashable], set[Hashable]], F: set[Hashable]):
        self.S = S
        self.A = A
        self.s0 = s0
        self.d = d
        self.F = F


    def __repr__(self):
        return ', '.join([str(x) for x in [self.S, self.A, self.s0, self.d, self.F]])


    def __eq__(self, other):

        if isinstance(other, FA):
            return (self.S == other.S and
                    self.A == other.A and
                    self.s0 == other.s0 and
                    self.d == other.d and
                    self.F == other.F)


    def is_deterministic(self) -> bool:
        '''See what determinism means on `wikipedia <https://en.wikipedia.org/wiki/Nondeterministic_finite_automaton#>`_.

        :returns: True if the FA is deterministic, otherwise False.'''
        return all([len(l) == 1 for l in self.d.values()])


    def verify(self, w: Iterable[Hashable]) -> bool:
        '''Assuming the automaton is deterministic,
        verify whether it accepts the given string.

        :returns: True if string is accepted, otherwise False.
        '''

        assert self.is_deterministic()
        s = self.s0
        for l in w:
            s2 = self.d.get((s, l))
            if not s2:
                return False
            s = next(iter(s2))
        return s in self.F


    def to_grammar(self) -> grammar.Grammar:
        '''Convert the FA to a regular grammar.

        :returns: a strictly regular grammar corresponding to the current FA.
        '''

        VT = {k[1] for k in self.d.keys()}
        P = defaultdict(set)

        for k, v in self.d.items():
            P[k[0],] |= {(k[1], s) if s != "ε" else (k[1],) for s in v}

        for s in self.F:
            if s == "ε":
                continue
            P[s,] |= {tuple()}
        P = dict(P)

        return grammar.Grammar(VN = self.S - {"ε"}, VT = VT, P = P, S = self.s0)


    def to_DFA(self) -> FA:
        '''If this FA is nondeterministic, convert it to a deterministic one.

        Basically, the states in the NFA become sets of states in the DFA.
        For a better explanation of the algorithm
        see the `Dragon book <https://suif.stanford.edu/dragonbook/>`_.

        For example, the NFA::

            FA( S = {'B', 'ε', 'A'},
                A = {'a', 'b'},
                s0 = 'A',
                d = {('A', 'a'): {'A', 'B'}, ('B', 'b'): {'ε'}},
                F = {'ε', 'A'})

        is transformed into the following DFA::

            FA( S = {{'A'}, {'A', 'B'}, {'ε'}},
                A = {'a', 'b'},
                s0 = {'A'},
                d = {
                    ({'A'}, 'a'): {{'A', 'B'}},
                    ({'A', 'B'}, 'a'): {{'A', 'B'}},
                    ({'A', 'B'}, 'b'): {{'ε'}}
                },
                F = {{'A'}, {'A', 'B'}, {'ε'}})
        '''

        def move(T: set[Hashable], a: Hashable):
            '''Returns the set of states reachable from any state in T via symbol a'''
            return {s for S in T if (u := self.d.get((S, a))) for s in u}

        if self.is_deterministic():
            return self

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
                dtran[(T, a)] = set([frozenset(U)])

        F = {T for T in dstat if any(s in self.F for s in T)}
        return FA(S = set(dstat.keys()), A = self.A, s0 = frozenset({self.s0,}), d = dtran, F = F)


    def draw(self, dirname: str, name: str) -> str:
        '''Export the FA to a diagram in SVG using `graphviz <https://graphviz.org/>`_.

        :param dirname: Directory in which the file will be created.
        :param name: Name of the diagram, which will become the filename.
        :returns: Full path of the exported file.'''
        import graphviz
        dot = graphviz.Digraph(name, format='svg')
        dot.attr(rankdir='LR')

        nonfinal_states = (str(s) for s in self.S - self.F)
        final_states = (str(s) for s in self.F)
        edges = [(str(k[0]), str(s), str(k[1])) for k,v in self.d.items() for s in v]

        for s in final_states:
            dot.attr('node', shape='doublecircle')
            dot.node(s)

        for s in nonfinal_states:
            dot.attr('node', shape='circle')
            dot.node(s)

        for s0, s1, label in edges:
            dot.edge(s0, s1, label=label)

        name = dot.render(directory=dirname).replace('\\', '/')
        return name
