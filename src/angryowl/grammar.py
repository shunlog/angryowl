from enum import IntEnum
from collections.abc import Hashable

class GrammarType(IntEnum):
    '''Grammar classes according to the `Chomsky hierarchy <https://en.wikipedia.org/wiki/Chomsky_hierarchy>`_.'''
    UNRESTRICTED_GRAMMAR = 0
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

    For example, the formal grammar::

        A -> aA
        A -> aB
        A -> ε
        B -> b

    Is represented by the following variables::

        VN = {"A", "B"}
        VT = {"a", "b"}
        P = {
            ("A",): {("a", "B"), ("a", "A"), ()},
            ("B",): {("b",)}
        }
        S = "A"
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

    def type(self) -> GrammarType:
        '''Returns the type of the grammar object according to the
        `Chomsky hierarchy <https://en.wikipedia.org/wiki/Chomsky_hierarchy>`_.

        If we determine the type of each production rule in the grammar,
        then the type of the grammar will be the least restrictive type among them
        (i.e. with the lowest type number).
        '''

        def rule_type(head, tail):
            if len(head) == 1 and (len(tail) == 0 or
                                   len(tail) == 1 and tail[0] in self.VT or
                                   len(tail) == 2 and tail[0] in self.VT and tail[1] in self.VN):
                return GrammarType.REGULAR

            if len(head) == 1:
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

            return GrammarType.UNRESTRICTED_GRAMMAR

        return min([rule_type(h, t) for h in self.P.keys() for t in self.P[h]])

    def constr_word(self) -> list:
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
