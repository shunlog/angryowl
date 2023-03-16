class Grammar:
    '''
    A grammar is represented by 4 variables:

    :param VN: set of nonterminals
    :param VT: set of terminals
    :param P: list of productions.
    :param S: starting state

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
    Rule = tuple[str]

    def __init__(self, VN: set[str], VT: set[str], P: dict[Rule, set[Rule]], S: str):
        self.VN = VN
        self.VT = VT
        self.P = P
        self.S = S

    def __repr__(self):
        return ', '.join([str(x) for x in [self.VN, self.VT, self.P, self.S]])

    def type(self):

        def rule_type(head, tail):
            if len(head) == 1 and \
                (len(tail) == 0 or \
                len(tail) == 1 and tail[0] in self.VT or \
                len(tail) == 2 and tail[0] in self.VT and tail[1] in self.VN):
                return 3
            elif len(head) == 1:
                return 2
            else:
                for i,l in enumerate(head):
                    if l not in self.VN:
                        continue
                    a = head[:i]
                    b = head[i+1:]
                    if a == tail[:i] and \
                       b == (tail[-len(b):] if len(b) != 0 else '') and \
                       len(head) <= len(tail):
                        return 1
                return 0

        return min([rule_type(h, t) for h in self.P.keys() for t in self.P[h]])

    def constr_word(self) -> str:
        '''Assuming *strictly* right-regular grammar.

        :returns: A string built using rules from the grammar picked at random.
        '''
        assert self.type() == 3

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
