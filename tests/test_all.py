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


tests = [(0, Grammar(VN = {'A', 'B'},
                     VT = {},
                     S = "",
                     P = {("A", "B"): {()}})),
         # Check that context-free grammars require non-terminals in left side
         (0, Grammar(VN = {'A'},
                     VT = {'a'},
                     S = "S",
                     P = {("a"): {()}}))
         ]

@pytest.mark.parametrize("t, g", tests)
class TestNonRegularGrammars:
    def test_grammar_type(self, t, g):
        assert g.type() == t

    def test_grammar_to_FA(self, t, g):
        with pytest.raises(AssertionError):
            g.to_NFA()

class TestGrammars:
    g1 = Grammar(VN = {'A', 'B'},
                 VT = {'a', 'b'},
                 S = 'A',
                 P = {('A', 'B'): {('a'), ('a', 'A'), ()},
                      ('B',): {('b',)},
                      ('B', 'A'): {}})
    g1_prules = {
        (('A', 'B'), ('a')),
        (('A', 'B'), ('a', 'A')),
        (('A', 'B'), ()),
        (('B',), ('b',))
    }

    @pytest.mark.parametrize("g, production_rules", [(g1, g1_prules)])
    def test_producion_rules(self, g, production_rules):
        assert set(g.production_rules()) == production_rules


class TestNormalForm:
    normal_grammar = Grammar(VN = {'S', 'A', 'B', 'C'},
                 VT = {'a', 'ε'},
                 S = 'S',
                 P = {('A',): {('B', 'C')},
                      ('A',): {('a',)},
                      ('S',): {()}})

    grammars_normality = (
        (normal_grammar, True),
        # 1. The start symbol S can't be in the right-hand side
        (Grammar(VN = {'S0', 'A'},
                 VT = {'a'},
                 S = 'S0', # test that S0 might exist already
                 P = {('A',): {('a',)},
                      ('S0',): {('A',)}}),
         False),
        # 2. There can only be exactly 1 terminal in the right-hand side
        (Grammar(VN = {'S', 'A'},
                 VT = {'a'},
                 S = 'S',
                 P = {('A',): {('a', 'A'), ('a',)},
                      ('S',): {('A',)}}),
         False),
        # 3. Right-hand sides can only have exactly 2 nonterminals
        (Grammar(VN = {'A', 'B'},
                 VT = {'a'},
                 S = 'A',
                 P = {('A',): {('B',)},
                      ('B',): {('a',)}}),
         False),
        (Grammar(VN = {'A', 'B'},
                 VT = {'a'},
                 S = 'A',
                 P = {('A',): {('B', 'B', 'B')},
                      ('B',): {('a',)}}),
         False),
        # 4. Only the start symbol can be an ε-rule
        (Grammar(VN = {'S', 'A'},
                 VT = {'a'},
                 S = 'S',
                 P = {('A',): {()},
                      ('S',): {()}}),
         False),
        # Random Grammar
        (Grammar(VN = {'S', 'A', 'B', 'C', 'E'},
                 VT = {'d', 'a'},
                 S = 'S',
                 P = {
                     ('S',): {('A',)},
                     ('A',): {('d',), ('d', 'S'), ('a', 'A', 'd', 'A', 'B')},
                     ('B',): {('a', 'C'), ('a', 'S'), ('A', 'C')},
                     ('C',): {()},
                     ('E',): {('A', 'S')},
                 }),
         False)
    )

    @pytest.mark.parametrize("g, expected", grammars_normality)
    def test_is_in_normal_form(self, g, expected):
        assert g.is_in_normal_form() == expected


    @pytest.mark.parametrize("g", (g[0] for g in grammars_normality))
    def test_grammar_to_normal_form(self, g):
        assert g.to_normal_form().is_in_normal_form()

    @pytest.mark.parametrize("g", [
        Grammar(VN = {'S', 'A'},
                VT = {'a'},
                S = 'S',
                P = {('A', 'B'): {('A', 'B')}})
    ])
    def test_non_context_free_grammar_to_normal_form(self, g):
        with pytest.raises(AssertionError):
            g.to_normal_form()


    @pytest.mark.parametrize("g_in, g_out", [
        (
            Grammar(VN = {'S', 'S0'},
                    VT = {},
                    S = 'S',
                    P = {}),
            Grammar(VN = {'S', 'S0', 'S1'},
                    VT = {},
                    S = 'S1',
                    P = {('S1',): {('S',)}}),
        )
    ])
    def test_procedure_START(self, g_in, g_out):
        g_in._START()
        assert g_in == g_out


    @pytest.mark.parametrize("g_in, g_out", [
        (
            Grammar(VN = {'S', 'A', 'B'},
                    VT = {'a'},
                    S = 'A',
                    P = {('A',): {('A', 'a', 'A'),
                                  ('a', 'A', 'B')}}),
            Grammar(VN = {'S', 'A', 'B', 'a0'},
                    VT = {'a'},
                    S = 'A',
                    P = {('A',): {('A', 'a0', 'A'),
                                  ('a0', 'A', 'B')},
                         ('a0',): {('a',)}}),
        )
    ])
    def test_procedure_TERM(self, g_in, g_out):
        g_in._TERM()
        assert g_in == g_out


    @pytest.mark.parametrize("g_in, g_out", [
        (
            Grammar(VN = {'A', 'B', 'C', 'D'},
                    VT = {},
                    S = 'A',
                    P = {('A',): {('A', 'B', 'C', 'D')}}),
            Grammar(VN = {'A', 'B', 'C', 'D', 'A0', 'A1'},
                    VT = {},
                    S = 'A',
                    P = {('A',): {('A', 'A0')},
                         ('A0',): {('B', 'A1')},
                         ('A1',): {('C', 'D')}}),
        )
    ])
    def test_procedure_BIN(self, g_in, g_out):
        g_in._BIN()
        assert g_in == g_out


    g_nullable = Grammar(VN = {'A', 'B', 'C'},
                         VT = {'b', 'd'},
                         S = 'A',
                         P = {('A',): {('B',), ('C',)},  # nullable because both B and C are nullable
                              ('B',): {(), ('b',)},  # is nullable but isn't null
                              ('C',): {()},  # null and hence nullable
                              ('D',): {('d',)},  # isn't nullable
                              ('E',): {('C',)},  # is null because C is null
                              ('F',): {('C', 'D')},  # not nullable because D isn't null
                              ('G',): {('G',), ('C',)},  # test recursion
                              })

    @pytest.mark.parametrize("s, g, expected", [
        ('A', g_nullable, True),
        ('B', g_nullable, True),
        ('C', g_nullable, True),
        ('D', g_nullable, False),
        ('E', g_nullable, True),
        ('F', g_nullable, False),
        ('G', g_nullable, True),
    ])
    def test_nullable(self, s, g, expected):
        assert g._is_nullable(s) == expected

    @pytest.mark.parametrize("s, g, expected", [
        ('A', g_nullable, False),
        ('B', g_nullable, False),
        ('C', g_nullable, True),
        ('D', g_nullable, False),
        ('E', g_nullable, True),
        ('F', g_nullable, False),
        ('G', g_nullable, True),
    ])
    def test_null(self, s, g, expected):
        assert g._is_null(s) == expected


    @pytest.mark.parametrize("g_in, g_out", [
        (
            # Basic example
            Grammar(VN = {'A', 'B', 'C', 'D', 'S'},
                    VT = {'a'},
                    S = 'S',
                    P = {('A',): {('a', 'B', 'C', 'D')},  # handle >2 nullables
                         ('S',): {()},  # don't delete ε-rules for start symbol
                         ('C',): {()},  # nullable
                         ('D',): {(), ('a',)},  # nullable with more than 1 rule
                         ('B',): {('C', 'D')}}),   # also nullable
            Grammar(VN = {'A', 'B', 'C', 'D', 'S'},
                    VT = {'a'},
                    S = 'S',
                    P = {('A',): {('a', 'B', 'D'),
                                  ('a', 'B'),
                                  ('a', 'D'),
                                  ('a',)
                                  },  # handle >2 nullables
                         ('S',): {()},  # the ε-rule isn't deleted for start symbol
                         # C was a null nonterminal (only had an ε-rule)
                         ('D',): {('a',)},  # the ε-rule was deleted
                         ('B',): {('D',)}}),  # the C was deleted from here
        )
    ])
    def test_procedure_DEL(self, g_in, g_out):
        g_in._DEL()
        assert g_in == g_out


    @pytest.mark.parametrize("g_in, g_out", [
        (
            Grammar(VN = {'A', 'B'},
                    VT = {'a', 'b'},
                    S = 'A',
                    P = {('B',): {('a', 'b')},
                         ('A',): {('B',)}}),
            Grammar(VN = {'A', 'B'},
                    VT = {'a', 'b'},
                    S = 'A',
                    P = {('B',): {('a', 'b')},
                         ('A',): {('a', 'b')}}),
        )
    ])
    def test_procedure_UNIT(self, g_in, g_out):
        g_in._UNIT()
        assert g_in == g_out
