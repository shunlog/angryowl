from enum import IntEnum

class Grammar:
    '''
    A `formal grammar <https://en.wikipedia.org/wiki/Formal_grammar#Formal_definition>`_
    is defined by 4 components:

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

    SymbolsStr = tuple[str]

    class Type(IntEnum):
        '''Grammar classes according to the `Chomsky hierarchy
        <https://en.wikipedia.org/wiki/Chomsky_hierarchy>`_.
        '''
        UNRESTRICTED_GRAMMAR = 0
        CONTEXT_SENSITIVE = 1
        CONTEXT_FREE = 2
        REGULAR = 3

    def __init__(self, VN: set[str], VT: set[str], P: dict[SymbolsStr, set[SymbolsStr]], S: str):
        self.VN = VN
        self.VT = VT
        self.P = P
        self.S = S

    def __repr__(self):
        return ', '.join([str(x) for x in [self.VN, self.VT, self.P, self.S]])

    def type(self) -> Type:
        '''Returns the type of the grammar object according to the `Chomsky hierarchy`_.

        If we determine the type of each production rule in the grammar,
        then the type of the grammar will be the least restrictive type among them
        (i.e. with the lowest type number).
        '''

        def rule_type(head, tail):
            if len(head) == 1 and \
                (len(tail) == 0 or \
                len(tail) == 1 and tail[0] in self.VT or \
                len(tail) == 2 and tail[0] in self.VT and tail[1] in self.VN):
                return self.Type.REGULAR
            elif len(head) == 1:
                return self.Type.CONTEXT_FREE
            else:
                for i,l in enumerate(head):
                    if l not in self.VN:
                        continue
                    a = head[:i]
                    b = head[i+1:]
                    if a == tail[:i] and \
                       b == (tail[-len(b):] if len(b) != 0 else '') and \
                       len(head) <= len(tail):
                        return self.Type.CONTEXT_SENSITIVE
                return self.Type.UNRESTRICTED_GRAMMAR

        return min([rule_type(h, t) for h in self.P.keys() for t in self.P[h]])

    def constr_word(self) -> str:
        '''Assuming a `*strictly* regular grammar
        <https://en.wikipedia.org/wiki/Regular_grammar#Strictly_regular_grammars>`_,
        construct a word using rules from the grammar picked at random.

        :returns: A random string that is valid according to the grammar.
        '''
        assert self.type() == self.Type.REGULAR

        from random import choice
        s = self.S  # current state
        w = ""  # word
        while True:
            tail = choice(list(self.P[s,]))
            if len(tail) == 2:
                w += tail[0]
                s = tail[1]
            elif len(tail) == 1:
                w += tail[0]
                break
            elif len(tail) == 0:
                break
        return ''.join(w)
