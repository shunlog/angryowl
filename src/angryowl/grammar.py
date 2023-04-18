from __future__ import annotations
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
        s = "{"
        for left, right in self.production_rules():
            s += "{} -> {}, ".format(' '.join(left), ' '.join(right))
        s = s[:-2]
        s += "}"
        return s


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


    def _new_nonterminal(self, s):
        # Find a symbol that starts with `s` that's not used as a nonterminal
        i = 0
        while True:
            ns = "{}{}".format(s, i)
            if ns not in self.VN:
                break
            i += 1
        return ns


    def _START(self):
        s = self._new_nonterminal(self.S)
        self.P[(s,)] = {(self.S,)}
        self.S = s
        self.VN |= {s}


    def _TERM(self):
        # find all non-solitary terminals
        terminals = set()
        for left, right in self.production_rules():
            if len(right) <= 1:
                continue
            for s in right:
                if s in self.VT:
                    terminals.add(s)

        # create new non-terminals for every such terminal
        mapping = dict()
        for s in terminals:
            ns = self._new_nonterminal(s)
            self.VN.add(ns)
            self.P[(ns,)] = {(s,)}
            mapping[s] = ns

        # replace all terminals with non-terminals
        P2 = self.P.copy()
        for left, right in self.production_rules():
            if len(right) <= 1:
                continue
            r2 = ()
            for s in right:
                if s in self.VT:
                    s = mapping[s]
                r2 += s,
            P2[left].remove(right)
            P2[left].add(r2)

        self.P = P2


    def _BIN(self):
        P2 = self.P.copy()
        for left, right in self.production_rules():
            # elliminate rules with more than 2 terminals on the right
            if len(right) <= 2:
                continue

            assert all(s in self.VN for s in right)

            # split the current rule
            prev_sym = left[0]
            P2[left].remove(right)
            for s in right[:-2]:
                ns = self._new_nonterminal(left[0])
                self.VN.add(ns)
                P2[(prev_sym,)].add((s, ns))
                P2[(ns,)] = set()
                prev_sym = ns
            P2[(prev_sym,)] = {(right[-2], right[-1])}

        self.P = P2


    def _DEL(self):
        def combinations(sl):
            '''Given a tuple of symbols "sl",
            returns an equivalent set of rules with inlined nullables and removed nulls'''
            if len(sl) == 0:
                return {()}
            s = sl[0]
            rest = sl[1:]
            cs = combinations(rest)
            if self._is_null(s):
                return cs

            aug = {(s,) + t for t in cs}

            if s in self.VT or not self._is_nullable(s):
                return aug
            if self._is_nullable(s):
                return cs | aug

            assert False

        P2 = defaultdict(set)
        for left, right in self.production_rules():
            if len(right) == 0:
                if left[0] == self.S:
                    P2[left].add(right)
                continue
            cs = combinations(right)
            for rule in cs:
                if len(rule) == 0:
                    continue
                P2[left].add(rule)
        self.P = dict(P2)


    def _UNIT(self):
        P2 = defaultdict(set)

        for left, right in self.production_rules():
            if len(right) == 1 and right[0] in self.VN:
                P2[left] |= P2[right]
                continue
            P2[left].add(right)
        self.P = dict(P2)


    def _is_nullable(self, s):
        '''A nonterminal "A" is nullable if either is true:
        1. A rule A → ε exists
        2. A rule A → X1 ... Xn exists, and every single Xi is nullable
        '''
        if s in self.VT:
            return False

        assert self.P.get((s,)) != None
        for rule_right in self.P[(s,)]:
            if (len(self.P[(s,)]) == 0) \
               or all(self._is_nullable(s1) for s1 in rule_right if s1 != s):
                return True

        return False


    def _is_null(self, s):
        '''A nonterminal "A" is null if every single production from "A" is either:
        1. A → ε
        2. A → B, where B is null
        '''
        if s in self.VT:
            return False

        assert self.P.get((s,)) != None
        for rule_right in self.P[(s,)]:
            if not(len(rule_right) == 0
                   or all(self._is_null(s1) for s1 in rule_right if s1 != s)):
                return False

        return True


    def to_normal_form(self) -> Grammar:
        '''Convert a context-free grammar to its `Chomsky normal form
        <https://en.wikipedia.org/wiki/Chomsky_normal_form>`_.
        '''
        assert self.type() >= GrammarType.CONTEXT_FREE

        self._START()
        self._TERM()
        self._BIN()
        self._DEL()
        self._UNIT()

        return self


    def is_in_normal_form(self) -> bool:
        '''Check if grammar is in `Chomsky normal form
        <https://en.wikipedia.org/wiki/Chomsky_normal_form>`_.
        '''
        # We have to check that this Grammar is context-free.
        # We could do that using Grammar.type(),
        # but really we only need to check that the left side
        # of each rule has length 1

        for left, right in self.production_rules():
            # there are 3 only valid rule forms:
            # 1. S -> ε
            # 2. A -> a
            # 3. A -> BC
            if not (len(left) == 1 and left[0] in self.VN # check that it's context-free
                    and ((left[0] == self.S and len(right) == 0)  # form (1)
                         or (len(right) == 1 and right[0] in self.VT)  # form (2)
                         or (len(right) == 2 and right[0] in self.VN and right[1] in self.VN))):  # form (3)
                return False

        return True
