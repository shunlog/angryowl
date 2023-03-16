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

    def is_deterministic(self):
       return all([len(l) == 1 for l in self.d.values()])

    def verify(self, w) -> bool:
        '''Verifies whether this DFA (assuming it's a DFA) accepts the string.

        :returns: True if it is accepted, otherwise false.
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
    def from_grammar(g: Grammar):
        '''Convert a *strictly* regular grammar to an NFA.

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
        return FA(S = g.VN | F, A = A, s0 = g.S, d = d, F = F)

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

    def to_DFA(self):
        '''For an explanation of the algo, check out the dragon book.

        This algorithm is described in the Dragon book.

        Basically, the states in the NFA become sets of states in the DFA.

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
        '''Visualize the FA diagram using `graphviz https://graphviz.org/`_.

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
