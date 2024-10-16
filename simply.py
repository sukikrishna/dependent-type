from dataclasses import dataclass
from typing import Dict, Union, List

@dataclass
class Var:
    name: str

@dataclass
class Abs:
    param: str
    param_type: 'Type'
    body: 'Expr'

@dataclass
class App:
    func: 'Expr'
    arg: 'Expr'

@dataclass
class TAbs:
    param: str
    body: 'Expr'

@dataclass
class TApp:
    func: 'Expr'
    type_arg: 'Type'

Expr = Union[Var, Abs, App, TAbs, TApp]

# Types
@dataclass
class TVar:
    name: str

@dataclass
class TArrow:
    param_type: 'Type'
    return_type: 'Type'

@dataclass
class TForall:
    param: str
    body: 'Type'

Type = Union[TVar, TArrow, TForall]

# Type checking
class TypeEnv:
    def __init__(self):
        self.var_types: Dict[str, Type] = {}
        self.type_vars: List[str] = []

    def extend(self, var: str, type: Type):
        new_env = TypeEnv()
        new_env.var_types = self.var_types.copy()
        new_env.var_types[var] = type
        new_env.type_vars = self.type_vars.copy()
        return new_env

    def extend_tvar(self, tvar: str):
        new_env = TypeEnv()
        new_env.var_types = self.var_types.copy()
        new_env.type_vars = self.type_vars.copy()
        new_env.type_vars.append(tvar)
        return new_env

def type_check(env: TypeEnv, expr: Expr) -> Type:
    if isinstance(expr, Var):
        if expr.name in env.var_types:
            return env.var_types[expr.name]
        else:
            raise TypeError(f"Unbound variable: {expr.name}")
    elif isinstance(expr, Abs):
        body_type = type_check(env.extend(expr.param, expr.param_type), expr.body)
        return TArrow(expr.param_type, body_type)
    elif isinstance(expr, App):
        func_type = type_check(env, expr.func)
        arg_type = type_check(env, expr.arg)
        if isinstance(func_type, TArrow) and func_type.param_type == arg_type:
            return func_type.return_type
        else:
            raise TypeError("Invalid application")
    elif isinstance(expr, TAbs):
        body_type = type_check(env.extend_tvar(expr.param), expr.body)
        return TForall(expr.param, body_type)
    elif isinstance(expr, TApp):
        func_type = type_check(env, expr.func)
        if isinstance(func_type, TForall):
            return substitute_type(func_type.body, func_type.param, expr.type_arg)
        else:
            raise TypeError("Invalid type application")

def substitute_type(t: Type, var: str, replacement: Type) -> Type:
    if isinstance(t, TVar):
        return replacement if t.name == var else t
    elif isinstance(t, TArrow):
        return TArrow(
            substitute_type(t.param_type, var, replacement),
            substitute_type(t.return_type, var, replacement)
        )
    elif isinstance(t, TForall):
        if t.param == var:
            return t
        else:
            return TForall(t.param, substitute_type(t.body, var, replacement))

# Evaluation
def eval_expr(expr: Expr) -> Expr:
    if isinstance(expr, (Var, Abs, TAbs)):
        return expr
    elif isinstance(expr, App):
        func = eval_expr(expr.func)
        arg = eval_expr(expr.arg)
        if isinstance(func, Abs):
            return eval_expr(substitute(func.body, func.param, arg))
        else:
            return App(func, arg)
    elif isinstance(expr, TApp):
        func = eval_expr(expr.func)
        if isinstance(func, TAbs):
            return eval_expr(substitute_tvar(func.body, func.param, expr.type_arg))
        else:
            return TApp(func, expr.type_arg)

def substitute(expr: Expr, var: str, replacement: Expr) -> Expr:
    if isinstance(expr, Var):
        return replacement if expr.name == var else expr
    elif isinstance(expr, Abs):
        if expr.param == var:
            return expr
        else:
            return Abs(expr.param, expr.param_type, substitute(expr.body, var, replacement))
    elif isinstance(expr, App):
        return App(substitute(expr.func, var, replacement), substitute(expr.arg, var, replacement))
    elif isinstance(expr, TAbs):
        return TAbs(expr.param, substitute(expr.body, var, replacement))
    elif isinstance(expr, TApp):
        return TApp(substitute(expr.func, var, replacement), expr.type_arg)

def substitute_tvar(expr: Expr, tvar: str, replacement: Type) -> Expr:
    if isinstance(expr, Var):
        return expr
    elif isinstance(expr, Abs):
        return Abs(
            expr.param,
            substitute_type(expr.param_type, tvar, replacement),
            substitute_tvar(expr.body, tvar, replacement)
        )
    elif isinstance(expr, App):
        return App(substitute_tvar(expr.func, tvar, replacement), substitute_tvar(expr.arg, tvar, replacement))
    elif isinstance(expr, TAbs):
        if expr.param == tvar:
            return expr
        else:
            return TAbs(expr.param, substitute_tvar(expr.body, tvar, replacement))
    elif isinstance(expr, TApp):
        return TApp(
            substitute_tvar(expr.func, tvar, replacement),
            substitute_type(expr.type_arg, tvar, replacement)
        )

# Example
if __name__ == "__main__":
    # Λα. λx:α. x
    id_expr = TAbs("α", Abs("x", TVar("α"), Var("x")))
    
    # type of the polymorphic identity function
    # TForall(param='α', body=TArrow(param_type=TVar(name='α'), return_type=TVar(name='α')))
    id_type = type_check(TypeEnv(), id_expr)
    print(f"Type of polymorphic identity: {id_type}")
    
    # run application of polymorphic identity function on a type
    # TArrow(param_type=TArrow(param_type=TVar(name='β'), return_type=TVar(name='β')), return_type=TArrow(param_type=TVar(name='β'), return_type=TVar(name='β')))
    # models (β → β) → (β → β) which is expected because the universal type is instantiated with a concrete type beta to beta
    applied_id = TApp(id_expr, TArrow(TVar("β"), TVar("β")))
    applied_id_type = type_check(TypeEnv(), applied_id)
    print(f"Type of applied polymorphic identity: {applied_id_type}")
    
    # Evaluate the applied polymorphic identity function
    # Abs(param='x', param_type=TArrow(param_type=TVar(name='β'), return_type=TVar(name='β')), body=Var(name='x'))
    # lambda abstraction λx:(β → β). x
    result = eval_expr(applied_id)
    print(f"Evaluated result: {result}")

    # after testing on the example, it seems the interpretor is correctly handling the types and the evaluation of the polymorphic function!