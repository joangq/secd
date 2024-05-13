from secd import SECD

if __name__ == '__main__':
    state = [[], [], [], []]
    expr = [['lambda', 'x', ['if', 'x', True, False]], True]
    code = SECD.compile(expr, state)
    print(code)
    print(SECD.execute(code, state))