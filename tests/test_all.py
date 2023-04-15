#!/usr/bin/env python3
import pytest
from angryowl.grammar import *
from angryowl.automata import *
from icecream import ic

'''
The test data components are:

- Grammar type
- Grammar
- list of example words valid according to the Grammar (tuples of symbols)
- FA constructed from Grammar (might be nondeterministic)
- whether the previous FA is deterministic or not
- DFA constructed from the previous FA, states must be represented by frozenset()
'''

tests = [
    (
        3,
        Grammar(VN = {"A", "B"},
                VT = {"a", "b"},
                S = "A",
                P = {("A",): {("a", "B"), ("a", "A"), ()},
                     ("B",): {("b",)}}),
        ('', 'a', 'ab', 'aab', 'aa'),
        FA(S = {'B', 'ε', 'A'},
           A = {'a', 'b'},
           s0 = 'A',
           d = {('A', 'a'): {'A', 'B'}, ('B', 'b'): {'ε'}},
           F = {'ε', 'A'}),
        False,
        FA(S = {frozenset(['A']), frozenset(['A', 'B']), frozenset(['ε'])},
           A = {'a', 'b'},
           s0 = frozenset(['A']),
           d = {(frozenset(['A']), 'a'): {frozenset(['A', 'B'])},
                (frozenset(['A', 'B']), 'a'): {frozenset(['A', 'B'])},
                (frozenset(['A', 'B']), 'b'): {frozenset(['ε'])}},
           F = {frozenset(['A']),
                frozenset(['A', 'B']),
                frozenset(['ε'])}
           )
    ),

    (
        3,
        Grammar(VN = {1, 2, 3},
                VT = {True, False},
                S = 1,
                P = {(1,): {(), (True, 2)},
                     (2,): {(False, 3)},
                     (3,): {(True, 1)}}),
        ((), (True, False, True), (True, False, True, True, False, True)),
        FA(S = {1, 2, 3},
           A = {True, False},
           s0 = 1,
           d = {(1, True): {2},
                (2, False): {3},
                (3, True): {1}},
           F = {1}),
        True,
        FA(S = {1, 2, 3},
           A = {True, False},
           s0 = 1,
           d = {(1, True): {2},
                (2, False): {3},
                (3, True): {1}},
           F = {1})
    ),
]

@pytest.mark.parametrize("t, g, wl, nfa, det, dfa", tests)
class TestRegularGrammars:
    def test_Grammar_type(self, g, wl, t, nfa, det, dfa):
        assert g.type() == t

    def test_Grammar_to_NFA(self, g, wl, t, nfa, det, dfa):
        test_nfa = g.to_NFA()
        assert nfa == test_nfa

    def test_NFA_to_Grammar(self, g, wl, t, nfa, det, dfa):
        test_g = nfa.to_grammar()
        assert test_g == g

    def test_is_deterministic(self, g, wl, t, nfa, det, dfa):
        assert nfa.is_deterministic() == det

    def test_NFA_to_DFA(self, g, wl, t, nfa, det, dfa):
        test_dfa = nfa.to_DFA()
        assert dfa == test_dfa

    def test_DFA_verify_word(self, g, wl, t, nfa, det, dfa):
        assert all(dfa.verify(w) for w in wl)

    def test_Grammar_constr_word(self, g, wl, t, nfa, det, dfa):
        assert all(dfa.verify(g.constr_word()) for _ in range(100))

    def test_draw(self, g, wl, t, nfa, det, dfa):
        from os.path import isfile
        assert isfile(nfa.draw('/tmp/', 'nfa'))
        assert isfile(dfa.draw('/tmp/', 'dfa'))


tests = [(0, Grammar(VN = {},
                     VT = {},
                     S = "",
                     P = {("A", "B"): {()}}))
         ]

@pytest.mark.parametrize("t, g", tests)
class TestNonRegularGrammars:
    def test_grammar_type(self, t, g):
        assert g.type() == t

    def test_grammar_to_FA(self, t, g):
        with pytest.raises(AssertionError):
            g.to_NFA()
