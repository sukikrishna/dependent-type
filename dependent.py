from dataclasses import dataclass
from typing import Union, List, Callable, Dict, Optional

# Expression types (not including Eval)
@dataclass
class Var:
    name: str

@dataclass
class Star:
    pass

@dataclass
class Pi:
    var: str
    domain: 'Expr'
    codomain: 'Expr'

@dataclass
class Lam:
    var: str
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

# Can have expressions that are made up of any of these types (previously defined)
Expr = Union[Var, Star, Pi, Lam, App, Nat, Zero, Succ, ElimNat]

# Environment
Env = Dict[str, Expr]

# Free variables
def free_vars(expr: Expr) -> set:
    match expr:
        case Var(name):
            return {name}
        case Star():
            return set()
        case Pi(var, domain, codomain):
            return free_vars(domain) | (free_vars(codomain) - {var})
        case Lam(var, domain, body):
            return free_vars(domain) | (free_vars(body) - {var})
        case App(func, arg):
            return free_vars(func) | free_vars(arg)
        case Nat():
            return set()
        case Zero():
            return set()
        case Succ(e):
            return free_vars(e)
        case ElimNat(motive, base, inductive, target):
            return free_vars(motive) | free_vars(base) | free_vars(inductive) | free_vars(target)

# Substitution

# Checks if variable substituted inside an expression is same as bound variable of the lambda term.
# If they match then won't substitute to avoid capturing the free variable

def subst(var: str, replacement: Expr, target: Expr) -> Expr:
    match target:
        case Var(name):
            return replacement if name == var else target
        case Star():
            return target
        case Pi(x, domain, codomain):
            new_domain = subst(var, replacement, domain)
            new_codomain = subst(var, replacement, codomain) if x != var else codomain
            return Pi(x, new_domain, new_codomain)
        case Lam(x, domain, body):
            new_domain = subst(var, replacement, domain)
            new_body = subst(var, replacement, body) if x != var else body
            return Lam(x, new_domain, new_body)
        case App(func, arg):
            return App(subst(var, replacement, func), subst(var, replacement, arg))
        case Nat():
            return target
        case Zero():
            return target
        case Succ(e):
            return Succ(subst(var, replacement, e))
        case ElimNat(motive, base, inductive, target):
            return ElimNat(
                subst(var, replacement, motive),
                subst(var, replacement, base),
                subst(var, replacement, inductive),
                subst(var, replacement, target)
            )

# Evaluation      
def eval_expr(expr: Expr) -> Expr:
    while True:
        new_expr = eval_step(expr)
        if new_expr is None:
            return expr
        expr = new_expr

def eval_step(expr: Expr) -> Optional[Expr]:
    match expr:
        case App(Lam(x, _, body), arg):
            return subst(x, arg, body)
        case App(func, arg):
            new_func = eval_step(func)
            if new_func:
                return App(new_func, arg)
            new_arg = eval_step(arg)
            if new_arg:
                return App(func, new_arg)
        case Lam(x, domain, body):
            new_body = eval_step(body)
            if new_body:
                return Lam(x, domain, new_body)
        case Pi(x, domain, codomain):
            new_domain = eval_step(domain)
            if new_domain:
                return Pi(x, new_domain, codomain)
            new_codomain = eval_step(codomain)
            if new_codomain:
                return Pi(x, domain, new_codomain)
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
    while True:
        new_expr = eval_step(expr)
        if not new_expr:
            return expr
        expr = new_expr

# Type Checking
def type_check(env: Env, expr: Expr) -> Expr:
    match expr:
        case Var(name):
            if name in env:
                return env[name]
            raise TypeError(f"Unbound variable: {name}")
        case Star():
            return Star()
        case Pi(x, domain, codomain):
            if eval_expr(type_check(env, domain)) != Star():
                raise TypeError("Domain of Pi must have type Star")
            if eval_expr(type_check({**env, x: domain}, codomain)) != Star():
                raise TypeError("Codomain of Pi must have type Star")
            return Star()
        case Lam(x, domain, body):
            if eval_expr(type_check(env, domain)) != Star():
                raise TypeError("Domain of Lambda must have type Star")
            body_type = type_check({**env, x: domain}, body)
            return Pi(x, domain, body_type)
        case App(func, arg):
            func_type = eval_expr(type_check(env, func))
            if not isinstance(func_type, Pi):
                raise TypeError("Function in application must have Pi type")
            arg_type = eval_expr(type_check(env, arg))
            if not eval_expr(arg_type) == eval_expr(func_type.domain):
                raise TypeError("Argument type mismatch in application")
            return eval_expr(subst(func_type.var, arg, func_type.codomain))
        case Nat():
            return Star()
        case Zero():
            return Nat()
        case Succ(e):
            if eval_expr(type_check(env, e)) != Nat():
                raise TypeError("Argument of Succ must have type Nat")
            return Nat()
        case ElimNat(motive, base, inductive, target):
            if eval_expr(type_check(env, target)) != Nat():
                raise TypeError("Target of ElimNat must have type Nat")
            motive_type = eval_expr(type_check(env, motive))
            if not isinstance(motive_type, Pi) or motive_type.domain != Nat() or motive_type.codomain != Star():
                raise TypeError("Motive of ElimNat must have type (n : Nat) -> Star")
            base_type = eval_expr(type_check(env, base))
            if not eval_expr(base_type) == eval_expr(App(motive, Zero())):
                raise TypeError("Zero case of ElimNat has incorrect type")
            expected_inductive_type = Pi("n", Nat(), Pi("ih", App(motive, Var("n")), App(motive, Succ(Var("n")))))
            inductive_type = eval_expr(type_check(env, inductive))
            if not eval_expr(inductive_type) == eval_expr(expected_inductive_type):
                raise TypeError("Succ case of ElimNat has incorrect type")
            return eval_expr(App(motive, target))
        
# Helper functions for working with natural numbers
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

# Example for testing the semantic model: Proving commutativity of addition
# def prove_add_comm():
#     # addition
#     add = Lam("a", Nat(),
#               Lam("b", Nat(),
#                   ElimNat(Lam("_", Nat(), Nat()),
#                           Var("b"),
#                           Lam("_", Nat(),
#                               Lam("rec", Nat(),
#                                   Succ(Var("rec")))),
#                           Var("a"))))

#     # commutativity property
#     comm_prop = Pi("a", Nat(),
#                    Pi("b", Nat(),
#                       Pi("_", App(App(add, Var("a")), Var("b")),
#                          App(App(add, Var("b")), Var("a")))))

#     # Proving the commutativity for the example 2 + 3 = 3 + 2 is True
#     a, b = 2, 3
#     result1 = eval_complete(App(App(add, int_to_nat(a)), int_to_nat(b)))
#     result2 = eval_complete(App(App(add, int_to_nat(b)), int_to_nat(a)))

#     print(f"Proving {a} + {b} = {b} + {a}:")
#     print(f"{a} + {b} = {nat_to_int(result1)}")
#     print(f"{b} + {a} = {nat_to_int(result2)}")
#     print(f"Commutativity holds for {a} and {b}: {result1 == result2}")

# prove_add_comm()



print("----------------")

add = Lam("a", Nat(),
              Lam("b", Nat(),
                  ElimNat(Lam("_", Nat(), Nat()),
                          Var("b"),
                          Lam("_", Nat(),
                              Lam("rec", Nat(),
                                  Succ(Var("rec")))),
                          Var("a"))))

# Following the above format to test some basic arithmetic operations
mult = Lam("a", Nat(),
           Lam("b", Nat(),
               ElimNat(Lam("_", Nat(), Nat()),
                       Zero(),
                       Lam("_", Nat(),
                           Lam("rec", Nat(),
                               App(App(add, Var("b")), Var("rec")))),
                       Var("a"))))

factorial = Lam("n", Nat(),
                ElimNat(Lam("_", Nat(), Nat()),
                        Succ(Zero()),  # 1
                        Lam("k", Nat(),
                            Lam("rec", Nat(),
                                App(App(mult, Succ(Var("k"))), Var("rec")))),
                        Var("n")))

def test_examples():
    print("Testing multiplication and factorial arithmetic operations:")
    a, b, c = 3, 4, 2
    print(f"{a} + {b} = {nat_to_int(eval_complete(App(App(add, int_to_nat(a)), int_to_nat(b))))}")
    print(f"{a} * {b} = {nat_to_int(eval_complete(App(App(mult, int_to_nat(a)), int_to_nat(b))))}")
    print(f"{a}! = {nat_to_int(eval_complete(App(factorial, int_to_nat(a))))}")

    print("Testing commutativity of addition:")
    result1 = eval_complete(App(App(add, int_to_nat(a)), int_to_nat(b)))
    result2 = eval_complete(App(App(add, int_to_nat(b)), int_to_nat(a)))
    print(f"{a} + {b} = {nat_to_int(result1)}")
    print(f"{b} + {a} = {nat_to_int(result2)}")
    print(f"{a} + {b} = {b} + {a}: {result1 == result2}")

    print("Testing associativity of multiplication:")
    result1 = eval_complete(App(App(mult, int_to_nat(a)), App(App(mult, int_to_nat(b)), int_to_nat(c))))
    result2 = eval_complete(App(App(mult, App(App(mult, int_to_nat(a)), int_to_nat(b))), int_to_nat(c)))
    print(f"{a} * {b} = {nat_to_int(result1)}")
    print(f"{b} * {a} = {nat_to_int(result2)}")
    print(f"({a} * {b}) * {c} = {a} * ({b} * {c}): {result1 == result2}")

test_examples()