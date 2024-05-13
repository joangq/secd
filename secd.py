from functools import partial
from definitions import (
    Instruction,
    Machine,
    Compiler, 
    function, 
    var, 
    conditional, 
    application
)

class LDB(Instruction):
    value: bool

    # LDB(b): [l, pi, e, d] -> [l, b:pi, e, d]
    def execute(self, state):
        l, pi, e, d = state
        pi.append(self.value)
        return state
    
class TEST(Instruction):
    code1: list
    code2: list

    # TEST(l1, l2): [l, b:pi, e, d] -> [(l1 if b else l2):l, pi, e, d]
    def execute(self, state):
        l, pi, e, d = state
        b = pi.pop()
        code = [self.code1 if b else self.code2] + l
        return [code, pi, e, d]

class LD(Instruction):
    index: int

    # LD(n): [l, pi, e, d] -> [l, e[n]:pi, e, d]
    def execute(self, state):
        l, pi, e, d = state
        pi.append(e[self.index])

        return state
    
class MKCLO(Instruction):
    code: list
    
    # MCKLO(l'): [l, pi, e, d] -> [l, [l', e]:pi, e, d]
    def execute(self, state):
        l, pi, e, d = state
        pi.append([self.code, e.copy()])
        return state

class AP(Instruction):
    
    # AP: [l, v:[l', e']:pi, e, d] -> [l', [], v:e', [l, pi, e]:d]
    def execute(self, state):
        l, pi, e, d = state

        v = pi.pop()
        l_prime, e_prime = pi.pop()
        d.append([l, pi, e])

        return [l_prime, [v], e_prime, d]

class RET(Instruction):
    
    # RET: [l, v:pi, e, [l', pi', e']:d] -> [l', v:pi', e', d]
    def execute(self, state):
        l, pi, e, d = state
        v = pi.pop()
        l_prime, pi_prime, e_prime = d.pop()
        pi = [v] + pi_prime

        return [l_prime, pi, e_prime, d]

class SECD(Machine):
    class _compiler(Compiler):

        @Compiler.rule(bool)
        def compile_bool(self, args, state):
            value = args
            return [LDB(value=value)]

        @Compiler.rule(var)
        def compile_variable(self, args, state):
            name = args
            l, pi, e, d = state
            if name in e:
                return [LD(index=e.index(name))]
            else:
                raise ValueError(f"Variable {name} not found in environment.")
            
        @Compiler.rule(function)
        def compile_lambda(self, args, state):
            _, var, body = args
            l, pi, e, d = state
            new_env = [var] + e
            body_code = self.compile_expr(body, [None, None, new_env, None])
            return [MKCLO(code=body_code+[RET()])]
        
        @Compiler.rule(conditional)
        def compile_if(self, args, state):
            _, condition, true_branch, false_branch = args
            cond_code = self.compile_expr(condition, state)
            true_code = self.compile_expr(true_branch, state)
            false_code = self.compile_expr(false_branch, state)
            return cond_code + [TEST(code1=true_code, code2=false_code)]
        
        @Compiler.rule(application)
        def compile_application(self, args, state):
            func, arg = args
            func_code = self.compile_expr(func, state)
            arg_code = self.compile_expr(arg, state)
            return func_code + arg_code + [AP()]
        
        def list_selector(self, args, state):
            _map = {
                'lambda': function,
                'if': conditional,
                'application': application
            }

            first = args[0]
            
            if not isinstance(first, str):
                return self.get(application)

            return self.get(_map.get(first))
        
        @Compiler.rule(list)
        def compile_list(self, args, state):
            func = self.list_selector(args, state)
            return func(self, args, state)
    
    @staticmethod
    def Executor(code, state, instructions):
        execution = []
        for instruction in code:
            if not isinstance(instruction, instructions):
                raise ValueError(f"Unsupported instruction: {instruction}")
            
            execution.append((instruction, state))
            state = instruction.execute(state)

        execution.append((instruction, state))
        
        return state
    

    compiler = _compiler()
    instructions = (LDB, MKCLO, LD, AP, RET, TEST)
    executor = partial(Executor, instructions=instructions)

    @staticmethod
    def compile(code, state=None, error_as_value=False):
        return SECD.compiler.compile(code, state, error_as_value)
    
    @staticmethod
    def execute(code, state=None):
        return SECD.executor(code, state)