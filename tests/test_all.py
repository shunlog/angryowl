#!/usr/bin/env python3
from angryowl.grammar import *
from angryowl.automata import *
from icecream import ic

def test_type3_grammar():
    VN = {"A", "B"}
    VT = {"a", "b"}
    S = "A"
    P = {("A"): {("a", "B"), ("a", "A"), ()},
         ("B"): {("b",)}}
    g = Grammar(VN, VT, P, S)

    assert g.type() == Grammar.Type.REGULAR

def test_type1_grammar():
    VN = {"A", "B"}
    VT = {"a", "b"}
    S = "A"
    P = {("abAbC"): {("abAbC")}}
    g = Grammar(VN, VT, P, S)
    assert g.type() == Grammar.Type.CONTEXT_SENSITIVE

    P = {("abAbC"): {("abxxxbC")}}
    g = Grammar(VN, VT, P, S)
    assert g.type() == Grammar.Type.CONTEXT_SENSITIVE

    P = {("AbC"): {("xxxbC")}}
    g = Grammar(VN, VT, P, S)
    assert g.type() == Grammar.Type.CONTEXT_SENSITIVE

    P = {("bCA"): {("bCB")}}
    g = Grammar(VN, VT, P, S)
    assert g.type() == Grammar.Type.CONTEXT_SENSITIVE

def test_type0_grammar():
    VN = {"A", "B"}
    VT = {"a", "b"}
    S = "A"
    P = {("abbC"): {("abAbC")}}
    g = Grammar(VN, VT, P, S)
    assert g.type() == Grammar.Type.UNRESTRICTED_GRAMMAR

    P = {("abAbC"): {("abbC")}}
    g = Grammar(VN, VT, P, S)
    assert g.type() == Grammar.Type.UNRESTRICTED_GRAMMAR

def test_grammar_to_NFA():
    VN = {"A", "B"}
    VT = {"a", "b"}
    P = {("A"): {("a", "B"), ("a", "A"), ()},
        ("B"): {("b",)}}
    S = "A"
    g = Grammar(VN, VT, P, S)
    nfa = NFA.from_grammar(g)

    S = {'B', 'ε', 'A'}
    A = {'a', 'b'}
    s0 = 'A'
    d = {('A', 'a'): {'A', 'B'}, ('B', 'b'): {'ε'}}
    F = {'ε', 'A'}

    assert nfa.S == S
    assert nfa.A == A
    assert nfa.s0 == s0
    assert nfa.d == d
    assert nfa.F == F

def test_is_deterministic():
    VN = {"A", "B"}
    VT = {"a", "b"}
    P = {("A"): {("a", "B"), ("a", "A"), ()},
        ("B"): {("b",)}}
    S = "A"
    g = Grammar(VN, VT, P, S)
    nfa = NFA.from_grammar(g)
    assert not nfa.is_deterministic()

    P = {("A"): {("b", "B"), ("a", "A"), ()},
        ("B"): {("b",)}}
    g = Grammar(VN, VT, P, S)
    nfa = NFA.from_grammar(g)
    assert nfa.is_deterministic()

def test_NFA_to_DFA():
    S = {"q0","q1"}
    A = {"a","b"}
    s0 = "q0"
    F = {"ε"}
    d = {("q0","a"): {"q1", "q0"},
         ("q1","b"): {"ε"}}

    nfa = NFA(S=S, A=A, s0=s0, F=F, d=d)
    dfa = nfa.to_DFA()

    S = {frozenset({"q0"}), frozenset({"q0", "q1"}), frozenset({'ε'})}
    A = {'a', 'b'}
    s0 = {"q0"}
    d = {(frozenset({"q0"}), "a"): {"q0", "q1"},
         (frozenset({"q0", "q1"}), "a"): {"q0", "q1"},
         (frozenset({"q0", "q1"}), "b"): {"ε"}}
    F = {frozenset({'ε'})}

    assert dfa.S == S
    assert dfa.A == A
    assert dfa.s0 == s0
    assert dfa.d == d
    assert dfa.F == F

def test_DFA_verify_word():
    VN = {"A", "B"}
    VT = {"a", "b"}
    S = "A"
    P = {("A",): {("a", "B"), ("a", "A")},
         ("B",): {("b",)}}
    g = Grammar(VN=VN, VT=VT, P=P, S=S)
    ic(g)
    nfa = NFA.from_grammar(g)
    ic(nfa)
    dfa = nfa.to_DFA()
    ic(dfa)

    for _ in range(10):
        w = g.constr_word()
        ic(w)
        assert dfa.verify(w)
        assert not dfa.verify(w + "!")
