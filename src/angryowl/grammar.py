from enum import IntEnum
from typing import Generator
from collections import defaultdict
from collections.abc import Hashable, Iterable
from . import automata

class GrammarType(IntEnum):
    '''Grammar classes according to the `Chomsky hierarchy <https://en.wikipedia.org/wiki/Chomsky_hierarchy>`_.'''
    UNRESTRICTED = 0
    CONTEXT_SENSITIVE = 1
    CONTEXT_FREE = 2
    REGULAR = 3

class Grammar:
    '''A `formal grammar`_ is defined by 4 components:

    .. _formal grammar: https://en.wikipedia.org/wiki/Formal_grammar#Formal_definition

    :param VN: set of nonterminals
    :param VT: set of terminals
    :param P: list of productions
    :param S: starting state

    The list of productions is represented by a dictionary,
    each rule being a mapping of a string of symbols onto another string of symbols.

    For example, the following formal grammar::

        A -> aA
        A -> aB
        A -> ε
        B -> b

    Is represented in this way::

        Grammar(VN = {"A", "B"},
                VT = {"a", "b"},
                P = {
                    ("A",): {("a", "B"), ("a", "A"), ()},
                    ("B",): {("b",)}
                },
                S = "A")
    '''

    SymbolsStr = tuple[Hashable]

    def __init__(self, VN: set[Hashable], VT: set[Hashable], P: dict[SymbolsStr, set[SymbolsStr]], S: Hashable):
        self.VN = VN
        self.VT = VT
        self.P = P
        self.S = S

    def __repr__(self):
        return ', '.join([str(x) for x in [self.VN, self.VT, self.P, self.S]])

    def __eq__(self, other):

        if isinstance(other, Grammar):
            return (self.VN == other.VN and
                    self.VT == other.VT and
                    self.S == other.S and
                    self.P == other.P)

    def production_rules(self) -> Generator[tuple[SymbolsStr, SymbolsStr], None, None]:
        for left, rights in self.P.items():
            for right in rights:
                yield left, right


    def type(self) -> GrammarType:
        '''Returns the type of the grammar object according to the
        `Chomsky hierarchy <https://en.wikipedia.org/wiki/Chomsky_hierarchy>`_.

        If we determine the type of each production rule in the grammar,
        then the type of the grammar will be the least restrictive type among them
        (i.e. the minimum number).
        '''

        def rule_type(head: Iterable[Hashable], tail: Iterable[Hashable]) -> GrammarType:
            if len(head) == 1 and head[0] in self.VN \
               and (len(tail) == 0 or
                    len(tail) == 1 and tail[0] in self.VT or
                    len(tail) == 2 and tail[0] in self.VT and tail[1] in self.VN):
                return GrammarType.REGULAR

            if len(head) == 1 and head[0] in self.VN:
                return GrammarType.CONTEXT_FREE

            for i,l in enumerate(head):

                if l not in self.VN:
                    continue

                lh = head[:i]  # left context in head
                rh = head[i+1:]  # right context in head
                lt = tail[:i]  # left context in tail
                rt = tail[-len(rh):] if len(rh) != 0 else ''  # right context in tail

                if lh == lt and rh == rt and len(head) <= len(tail):
                    return GrammarType.CONTEXT_SENSITIVE

            return GrammarType.UNRESTRICTED

        return min(rule_type(h, t) for h, t in self.production_rules())

    def constr_word(self) -> list[Hashable]:
        '''Assuming a `*strictly* regular grammar <https://en.wikipedia.org/wiki/Regular_grammar#Strictly_regular_grammars>`_,
        construct a word using rules from the grammar picked at random.

        :returns: A random string that is valid according to the grammar.
        '''
        assert self.type() == GrammarType.REGULAR

        from random import choice
        s = self.S  # current state
        w = []  # word

        while True:
            tail = choice(list(self.P[s,]))
            if len(tail) == 2:
                w.append(tail[0])
                s = tail[1]
            elif len(tail) == 1:
                w.append(tail[0])
                break
            elif len(tail) == 0:
                break

        return w


    def to_NFA(self) -> automata.FA:
        '''Convert a `*strictly* regular grammar
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

            FA( S = {'B', 'ε', 'A'},
                A = {'a', 'b'},
                s0 = 'A',
                d = {('A', 'a'): {'A', 'B'}, ('B', 'b'): {'ε'}},
                F = {'ε', 'A'})

        :param g: A *strictly* regular grammar.
        :returns: An :class:`angryowl.automata.FA` instance.
        '''
        assert self.type() == GrammarType.REGULAR
        d = defaultdict(set)
        F = set()
        A = set()

        for left, right in self.production_rules():
            left = left[0]  # in a regular grammar, left is a single nonterminal
            if len(right) == 0:
                F |= {left}
            elif len(right) == 1:
                d[(left, right[0])] |= {"ε"}
                F |= {"ε"}
                A |= {right[0]}
            elif len(right) == 2:
                d[(left, right[0])] |= {right[1]}
                A |= {right[0]}

        d = dict(d)  # demote from defaultdict
        return automata.FA(S = self.VN | F, A = A, s0 = self.S, d = d, F = F)
