from abc import ABC as Interface
functionType = type(lambda: ...)

class Instruction:
    """ Base class for all instructions, dynamically creates methods based on annotations. """
    
    def __init__(self, **kwargs):
        if '__annotations__' not in dir(type(self)):
            return

        for field, field_type in self.__annotations__.items():
            if field in kwargs and isinstance(kwargs[field], field_type):
                setattr(self, field, kwargs[field])
            else:
                raise TypeError(f"Expected type {field_type} for field '{field}', got {type(kwargs[field])}")

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        
        if not hasattr(self, '__annotations__'):
            return True
        
        return all(getattr(self, field) == getattr(other, field) for field in self.__annotations__)

    def __str__(self):
        if not hasattr(self, '__annotations__'):
            return self.__class__.__name__
            
        fields_str = []
        for field in self.__annotations__:
            typeof_field = self.__annotations__[field]

            if typeof_field in (list, tuple):
                value = ', '.join(map(str, getattr(self, field)))
            else:
                value = str(getattr(self, field))
            
            fields_str.append(value)
        
        fields_str = ', '.join(fields_str)

        return f"{self.__class__.__name__}({fields_str})"

    def __repr__(self):
        return str(self)
    
class Code(list[Instruction]):
    def __str__(self):
        return ';'.join(map(str, self))
    
    def __repr__(self):
        return str(self)
    
    @classmethod
    def of(cls, *instructions):
        if len(instructions) == 1 and isinstance(instructions[0], list):
            return cls(instructions[0])
        
        return cls(instructions)

class Compiler:
    @staticmethod
    def rule(f_or_annotation):
        if isinstance(f_or_annotation, functionType):
            f_or_annotation.__rule__ = None
            return f_or_annotation
        
        else:
            def wrapper(func):
                func.__rule__ = f_or_annotation
                return func
            
            return wrapper
        
    def get(self, rule):
        if not isinstance(rule, type):
            return self.get(type(rule))

        return self.rules.get(rule, None)
    
    def compile_expr(self, code: Code, state):
        compile_func = self.get(code)
        
        if compile_func is None:
            raise ValueError(f"Unsupported expression type: {code}")
        
        return Code.of(compile_func(self, code, state))
    
    def compile(self, code, state=None, error_as_value=False):
        if not state:
            state = [[], [], [], []]
        
        try:
            return self.compile_expr(code, state)
        except Exception as e:
            if error_as_value:
                return e
            else:
                raise e
    
    def __init_subclass__(cls) -> None:
        rules = {(name if f.__rule__ is None else f.__rule__): f
                 for name in dir(cls)
                 for f in [getattr(cls, name)]
                 if hasattr(getattr(cls, name), '__rule__')}
        
        cls.rules = rules

class Machine(Interface):
    @staticmethod
    def compile(code, state=None, error_as_value=False):
        raise NotImplementedError
    
    @staticmethod
    def execute(code, state=None):
        raise NotImplementedError

class var(str): ...;
var = str
class function(object): ...
class conditional(object): ...
class application(object): ...