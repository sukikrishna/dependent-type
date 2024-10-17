from dataclasses import dataclass
from typing import Union, List, Optional

# Expression types
@dataclass
class Var:
    index: int  # De Bruijn index

@dataclass
class Star:
    pass

@dataclass
class Pi:
    domain: 'Expr'
    codomain: 'Expr'

@dataclass
class Lam:
    domain: 'Expr'
    body: 'Expr'

@dataclass
class App:
    func: 'Expr'
    arg: 'Expr'

@dataclass
class Nat:
    pass

@dataclass
class Zero:
    pass

@dataclass
class Succ:
    expr: 'Expr'

@dataclass
class ElimNat:
    motive: 'Expr'
    base: 'Expr'
    inductive: 'Expr'
    target: 'Expr'

Expr = Union[Var, Star, Pi, Lam, App, Nat, Zero, Succ, ElimNat]

# Shifting indices around to adjust for the bound variables
def shift(expr: Expr, shift_by: int, cutoff: int = 0) -> Expr:
    match expr:
        case Var(index):
            return Var(index + shift_by if index >= cutoff else index)
        case Star():
            return expr
        case Pi(domain, codomain):
            return Pi(shift(domain, shift_by, cutoff), shift(codomain, shift_by, cutoff + 1))
        case Lam(domain, body):
            return Lam(shift(domain, shift_by, cutoff), shift(body, shift_by, cutoff + 1))
        case App(func, arg):
            return App(shift(func, shift_by, cutoff), shift(arg, shift_by, cutoff))
        case Nat():
            return expr
        case Zero():
            return expr
        case Succ(e):
            return Succ(shift(e, shift_by, cutoff))
        case ElimNat(motive, base, inductive, target):
            return ElimNat(shift(motive, shift_by, cutoff), shift(base, shift_by, cutoff),
                           shift(inductive, shift_by, cutoff), shift(target, shift_by, cutoff))

# Performing the substitution using De Bruijn indices
def subst(expr: Expr, index: int, replacement: Expr) -> Expr:
    match expr:
        case Var(i):
            return replacement if i == index else expr
        case Star():
            return expr
        case Pi(domain, codomain):
            return Pi(subst(domain, index, replacement), subst(codomain, index + 1, shift(replacement, 1)))
        case Lam(domain, body):
            return Lam(subst(domain, index, replacement), subst(body, index + 1, shift(replacement, 1)))
        case App(func, arg):
            return App(subst(func, index, replacement), subst(arg, index, replacement))
        case Nat():
            return expr
        case Zero():
            return expr
        case Succ(e):
            return Succ(subst(e, index, replacement))
        case ElimNat(motive, base, inductive, target):
            return ElimNat(subst(motive, index, replacement), subst(base, index, replacement),
                           subst(inductive, index, replacement), subst(target, index, replacement))

# Evaluation
def eval_step(expr: Expr) -> Optional[Expr]:
    match expr:
        case App(Lam(_, body), arg):
            return subst(body, 0, shift(arg, 1))
        case App(func, arg):
            new_func = eval_step(func)
            if new_func:
                return App(new_func, arg)
            new_arg = eval_step(arg)
            if new_arg:
                return App(func, new_arg)
        case Lam(domain, body):
            new_body = eval_step(body)
            if new_body:
                return Lam(domain, new_body)
        case Succ(e):
            new_e = eval_step(e)
            if new_e:
                return Succ(new_e)
        case ElimNat(motive, base, inductive, Zero()):
            return base
        case ElimNat(motive, base, inductive, Succ(n)):
            return App(App(inductive, n), ElimNat(motive, base, inductive, n))
        case ElimNat(motive, base, inductive, target):
            new_target = eval_step(target)
            if new_target:
                return ElimNat(motive, base, inductive, new_target)
    return None

def eval_complete(expr: Expr) -> Expr:
    steps = 0
    while True:
        print(f"Step {steps}: {expr}")
        new_expr = eval_step(expr)
        if not new_expr:
            return expr
        expr = new_expr
        steps += 1
        if steps > 100:  # to prevent infinite loops :(
            print("Evaluation exceeded 100 steps. Stopping.")
            return expr

# Type checking
def type_check(env: List[Expr], expr: Expr) -> Expr:
    match expr:
        case Var(index):
            return env[index]
        case Star():
            return Star()
        case Pi(domain, codomain):
            if type_check(env, domain) != Star():
                raise TypeError("Domain of Pi must have type Star")
            if type_check([domain] + env, codomain) != Star():
                raise TypeError("Codomain of Pi must have type Star")
            return Star()
        case Lam(domain, body):
            if type_check(env, domain) != Star():
                raise TypeError("Domain of Lambda must have type Star")
            body_type = type_check([domain] + env, body)
            return Pi(domain, body_type)
        case App(func, arg):
            func_type = type_check(env, func)
            if not isinstance(func_type, Pi):
                raise TypeError("Function in application must have Pi type")
            arg_type = type_check(env, arg)
            if arg_type != func_type.domain:
                raise TypeError("Argument type mismatch in application")
            return subst(func_type.codomain, 0, arg)
        case Nat():
            return Star()
        case Zero():
            return Nat()
        case Succ(e):
            if type_check(env, e) != Nat():
                raise TypeError("Argument of Succ must have type Nat")
            return Nat()
        case ElimNat(motive, base, inductive, target):
            if type_check(env, target) != Nat():
                raise TypeError("Target of ElimNat must have type Nat")
            motive_type = type_check(env, motive)
            if not isinstance(motive_type, Pi) or motive_type.domain != Nat() or motive_type.codomain != Star():
                raise TypeError("Motive of ElimNat must have type (n : Nat) -> Star")
            base_type = type_check(env, base)
            if base_type != App(motive, Zero()):
                raise TypeError("Zero case of ElimNat has incorrect type")
            expected_inductive_type = Pi(Nat(), Pi(App(motive, Var(0)), App(motive, Succ(Var(0)))))
            inductive_type = type_check(env, inductive)
            if inductive_type != expected_inductive_type:
                raise TypeError("Succ case of ElimNat has incorrect type")
            return App(motive, target)

def nat_to_int(expr: Expr) -> int:
    match expr:
        case Zero():
            return 0
        case Succ(n):
            return 1 + nat_to_int(n)
    raise ValueError("Expression is not a natural number")

def int_to_nat(n: int) -> Expr:
    if n == 0:
        return Zero()
    return Succ(int_to_nat(n - 1))

# Example for testing the model: Adding natural numbers (now with De Bruijn indices)
def prove_add_comm():
    add = Lam(Nat(),
              Lam(Nat(),
                  ElimNat(Lam(Nat(), Nat()),
                          Var(1),
                          Lam(Nat(), Lam(Nat(), Succ(Var(0)))),
                          Var(1))))

    a, b = int_to_nat(2), int_to_nat(3)

    print(a) #Succ(expr=Succ(expr=Zero()))
    print(b) #Succ(expr=Succ(expr=Succ(expr=Zero())))

    #App(func=Lam(domain=Nat(), body=Lam(domain=Nat(), body=ElimNat(motive=Lam(domain=Nat(), body=Nat()), base=Var(index=1), inductive=Lam(domain=Nat(), body=Lam(domain=Nat(), body=Succ(expr=Var(index=0)))), target=Var(index=1)))), arg=Succ(expr=Succ(expr=Zero())))
    print(App(add, a))

    #App(func=App(func=Lam(domain=Nat(), body=Lam(domain=Nat(), body=ElimNat(motive=Lam(domain=Nat(), body=Nat()), base=Var(index=1), inductive=Lam(domain=Nat(), body=Lam(domain=Nat(), body=Succ(expr=Var(index=0)))), target=Var(index=1)))), arg=Succ(expr=Succ(expr=Zero()))), arg=Succ(expr=Succ(expr=Succ(expr=Zero()))))
    print(App(App(add, a), b)) 


    result1 = eval_complete(App(App(add, a), b))
    result2 = eval_complete(App(App(add, b), a))

    print(result1)
    print(result2)

    print(f"Proving 2 + 3 = 3 + 2:")
    print(f"Result 1 (2 + 3): {nat_to_int(result1)}")
    print(f"Result 2 (3 + 2): {nat_to_int(result2)}")
    print(f"Commutativity holds: {result1 == result2}")

prove_add_comm()

'''
Output:
Proving 2 + 3 = 3 + 2:
Result 1 (2 + 3): 4
Result 2 (3 + 2): 6
Commutativity holds: False
'''