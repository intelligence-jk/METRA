"""Core: units table, expression parser, exact conversion, dimension check.

Dimensions are exponent triples (L, T, M). Every value is a Fraction in SI
base units (metre, second, kilogram), so conversions are exact.
"""
import re
from dataclasses import dataclass
from fractions import Fraction
from typing import Optional

Dim = tuple  # (L, T, M)
NONE = (0, 0, 0)
L, T, M = (1, 0, 0), (0, 1, 0), (0, 0, 1)


class DimensionError(ValueError):
    """Raised when dimensions do not match or a unit is unknown."""


def _dim(l=0, t=0, m=0):
    return (l, t, m)


# name -> (factor to SI as Fraction, dimensions)
UNITS = {
    "m": (Fraction(1), L), "km": (Fraction(1000), L), "cm": (Fraction(1, 100), L),
    "mm": (Fraction(1, 1000), L),
    "s": (Fraction(1), T), "min": (Fraction(60), T), "h": (Fraction(3600), T),
    "kg": (Fraction(1), M), "g": (Fraction(1, 1000), M),
    "N": (Fraction(1), _dim(1, -2, 1)), "J": (Fraction(1), _dim(2, -2, 1)),
    "W": (Fraction(1), _dim(2, -3, 1)), "Pa": (Fraction(1), _dim(-1, -2, 1)),
    "L": (Fraction(1, 1000), _dim(3)), "ha": (Fraction(10000), _dim(2)),
}


def _add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def _scale(a, k):
    return tuple(x * k for x in a)


def dim_text(d: Dim) -> str:
    names = ("L", "T", "M")
    parts = [n if e == 1 else f"{n}^{e}" for n, e in zip(names, d) if e != 0]
    return " ".join(parts) if parts else "dimensionless"


@dataclass(frozen=True)
class Quantity:
    """A value in SI units with its dimensions. `value` is None for a bare variable."""
    value: Optional[Fraction]
    dims: Dim


_TOKEN = re.compile(r"\s*(?:(\d+\.\d+|\d+)|([A-Za-z]+)|(\^|\*|/|\+|-|\(|\)|=))")


def _tokenize(text: str):
    pos, out = 0, []
    text = text.strip()
    while pos < len(text):
        m = _TOKEN.match(text, pos)
        if not m:
            raise DimensionError(f"cannot read {text[pos:]!r}")
        if m.group(1):
            out.append(("num", Fraction(m.group(1))))
        elif m.group(2):
            out.append(("name", m.group(2)))
        else:
            out.append(("op", m.group(3)))
        pos = m.end()
    return out


class _Parser:
    """expr := term (('+'|'-') term)* ; term := factor (('*'|'/') factor)* ;
    factor := atom ('^' integer)? ; atom := number [name] | name | '(' expr ')'.
    A number followed by a name binds tighter than / (so '10 m / 2 s' is (10 m)/(2 s))."""

    def __init__(self, text, variables):
        self.toks = _tokenize(text)
        self.i = 0
        self.vars = variables or {}

    def peek(self):
        return self.toks[self.i] if self.i < len(self.toks) else (None, None)

    def take(self):
        t = self.peek()
        self.i += 1
        return t

    def parse(self):
        q = self.expr()
        if self.i != len(self.toks):
            raise DimensionError(f"unexpected {self.peek()[1]!r}")
        return q

    def expr(self):
        q = self.term()
        while self.peek() in (("op", "+"), ("op", "-")):
            sign = self.take()[1]
            r = self.term()
            if q.dims != r.dims:
                raise DimensionError(
                    f"cannot {'add' if sign == '+' else 'subtract'} "
                    f"{dim_text(q.dims)} and {dim_text(r.dims)}")
            if q.value is None or r.value is None:
                q = Quantity(None, q.dims)
            else:
                q = Quantity(q.value + r.value if sign == "+" else q.value - r.value, q.dims)
        return q

    def term(self):
        q = self.factor()
        while self.peek() in (("op", "*"), ("op", "/")):
            op = self.take()[1]
            r = self.factor()
            if op == "*":
                q = _mul(q, r)
            else:
                q = _div(q, r)
        return q

    def factor(self):
        q = self.atom()
        if self.peek() == ("op", "^"):
            self.take()
            neg = False
            if self.peek() == ("op", "-"):
                self.take()
                neg = True
            kind, n = self.take()
            if kind != "num" or n.denominator != 1:
                raise DimensionError("exponent must be a whole number")
            k = -int(n) if neg else int(n)
            q = Quantity(None if q.value is None else q.value ** k, _scale(q.dims, k))
        return q

    def atom(self):
        kind, v = self.take()
        if kind == "num":
            if self.peek()[0] == "name":
                u = self.unit_atom()
                if self.peek() == ("op", "^"):
                    self.take()
                    neg = self.peek() == ("op", "-")
                    if neg:
                        self.take()
                    k = int(self.take()[1]) * (-1 if neg else 1)
                    u = Quantity(None if u.value is None else u.value ** k, _scale(u.dims, k))
                return _mul(Quantity(v, NONE), u)
            return Quantity(v, NONE)
        if kind == "name":
            self.i -= 1
            return self.unit_atom()
        if (kind, v) == ("op", "("):
            q = self.expr()
            if self.take() != ("op", ")"):
                raise DimensionError("missing )")
            return q
        raise DimensionError(f"unexpected {v!r}")

    def unit_atom(self):
        name = self.take()[1]
        if name in self.vars:
            return Quantity(None, dimension_of(self.vars[name]))
        if name not in UNITS:
            raise DimensionError(f"unknown unit {name!r}")
        f, d = UNITS[name]
        return Quantity(f, d)


def _mul(a, b):
    v = None if a.value is None or b.value is None else a.value * b.value
    return Quantity(v, _add(a.dims, b.dims))


def _div(a, b):
    if b.value == 0:
        raise DimensionError("division by zero")
    v = None if a.value is None or b.value is None else a.value / b.value
    return Quantity(v, _add(a.dims, _scale(b.dims, -1)))


def evaluate(text: str, variables: Optional[dict] = None) -> Quantity:
    return _Parser(text, variables).parse()


def parse_quantity(text: str) -> Quantity:
    """'72 km/h' -> Quantity(value in m/s as Fraction, dims)."""
    q = evaluate(text)
    return q


def dimension_of(text: str, variables: Optional[dict] = None) -> Dim:
    return evaluate(text, variables).dims


def convert(text: str, target: str) -> Fraction:
    """Value of the quantity `text` expressed in `target` units, exactly."""
    q = parse_quantity(text)
    t = parse_quantity(target)
    if q.dims != t.dims:
        raise DimensionError(
            f"cannot convert {dim_text(q.dims)} to {dim_text(t.dims)}")
    return q.value / t.value


def check_equation(equation: str, variables: Optional[dict] = None) -> dict:
    """Check that both sides of 'lhs = rhs' have the same dimensions.

    `variables` maps a name to a unit expression, e.g. {'v': 'm/s', 'd': 'm', 't': 's'}.
    Returns {'ok': bool, 'lhs': dims, 'rhs': dims, 'message': str}.
    """
    if equation.count("=") != 1:
        raise DimensionError("an equation needs exactly one =")
    left, right = equation.split("=")
    a = evaluate(left, variables)
    b = evaluate(right, variables)
    ok = a.dims == b.dims
    msg = (f"both sides are {dim_text(a.dims)}" if ok else
           f"left side is {dim_text(a.dims)} but right side is {dim_text(b.dims)}")
    out = {"ok": ok, "lhs": a.dims, "rhs": b.dims, "message": msg}
    if ok and a.value is not None and b.value is not None:
        out["numbers_equal"] = a.value == b.value
    return out


def _exact_root(x: Fraction, n: int) -> Optional[Fraction]:
    def root(k):
        r = round(k ** (1 / n))
        for c in (r - 1, r, r + 1):
            if c >= 0 and c ** n == k:
                return c
        return None
    a, b = root(x.numerator), root(x.denominator)
    return None if a is None or b is None else Fraction(a, b)


def traps(text: str, target: str) -> list:
    """Plain-English warnings for a conversion that students often get wrong."""
    q, t = parse_quantity(text), parse_quantity(target)
    if q.dims != t.dims:
        return []
    notes = []
    names = set(re.findall(r"[A-Za-z]+", text + " " + target))
    if q.dims == (1, -1, 0) and {"km", "h", "m", "s"} <= names:
        notes.append("km/h to m/s: multiply by 5/18 (1000 m over 3600 s). "
                     "m/s to km/h: multiply by 18/5.")
    n = q.dims[0]
    if abs(n) >= 2 and q.dims[1] == 0 and q.dims[2] == 0:
        notes.append(f"Length appears to the power {abs(n)}, so a length factor "
                     f"f becomes f^{abs(n)} (for example 100 for cm to m "
                     f"becomes {100 ** abs(n)}).")
    if "L" in names:
        notes.append("1 L = 1000 cm^3, so 1 m^3 = 1000 L (not 100 L).")
    return notes
