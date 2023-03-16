from __future__ import annotations
from .grammar import Grammar, GrammarType
from collections import defaultdict

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

    def __init__(self, S: set[str], A: set[str], s0: str, d: dict[tuple[set[str], str], set[str]], F: set[str]):
        self.S = S
        self.A = A
        self.s0 = s0
        self.d = d
        self.F = F

    def __repr__(self):
        return ', '.join([str(x) for x in [self.S, self.A, self.s0, self.d, self.F]])

    def is_deterministic(self) -> bool:
        '''See what determinism means on `wikipedia <https://en.wikipedia.org/wiki/Nondeterministic_finite_automaton#>`_.

        :returns: True if the FA is deterministic, otherwise False.'''
        return all([len(l) == 1 for l in self.d.values()])


    def verify(self, w) -> bool:
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


    @staticmethod
    def from_grammar(g: Grammar) -> FA:
        '''Convert a `\*strictly\* regular grammar
        <https://en.wikipedia.org/wiki/Regular_grammar#Strictly_regular_grammars>`_
        to an NFA.

        There are 3 forms of production rules in a strictly regular grammar.
        The algorithm basically executes a list of actions for each production rule:

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

        :param g: A *strictly* regular grammar.
        :returns: An :class:`angryowl.automata.FA` instance.
        '''
        assert g.type() == GrammarType.REGULAR
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
        return FA(S = g.VN | F, A = A, s0 = g.S, d = d, F = F)

    def to_grammar(self) -> Grammar:
        '''The inverse of :func:`angryowl.automata.FA.from_grammar`.

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

        return Grammar(VN = self.S - {"ε"}, VT = VT, P = P, S = self.s0)


    def to_DFA(self):
        '''If this FA is nondeterministic, convert it to a deterministic one.

        See the `Dragon book <https://suif.stanford.edu/dragonbook/>`_
        for a better explanation of the algorithm.
        In short, the states in the NFA become sets of states in the DFA.

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
                ({'A'}, 'a'): {{'A', 'B'}},
                ({'A', 'B'}, 'a'): {{'A', 'B'}},
                ({'A', 'B'}, 'b'): {{'ε'}}
            }
            F = {{'A'}, {'A', 'B'}, {'ε'}}
        '''

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
                dtran[(T, a)] = set([frozenset(U)])

        F = {T for T in dstat if any(s in self.F for s in T)}
        return FA(S = set(dstat.keys()), A = self.A, s0 = frozenset({self.s0,}), d = dtran, F = F)


    def draw(self, dirname, fn) -> str:
        '''Visualize the FA diagram using `graphviz <https://graphviz.org/>`_.

        :param dirname: Directory to which the file will be exported.
        :param fn: Name of the diagram (filename minus extension).
        :returns: Path of the exported file.'''

        def get_nonfinal_states():
            return (str(s) for s in self.S - self.F)

        def get_final_states():
            return (str(s) for s in self.F)

        def get_edges():
            e = []
            for k, v in self.d.items():
                for s in v:
                    e.append((str(k[0]), str(s), str(k[1])))
            return e

        import graphviz
        dot = graphviz.Digraph(fn, format='svg')
        dot.attr(rankdir='LR')

        for s in get_final_states():
            dot.attr('node', shape='doublecircle')
            dot.node(s)

        for s in get_nonfinal_states():
            dot.attr('node', shape='circle')
            dot.node(s)

        for s0, s1, label in get_edges():
            dot.edge(s0, s1, label=label)

        fn = dot.render(directory=dirname).replace('\\', '/')
        return fn
