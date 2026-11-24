"""Command line: python -m unitscheck convert|check|dims ..."""
import argparse
from fractions import Fraction

from .core import DimensionError, check_equation, convert, dim_text, dimension_of, traps


def show(x: Fraction) -> str:
    if x.denominator == 1:
        return str(x.numerator)
    return f"{x} (about {float(x):.6g})"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="unitscheck", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("convert", help='convert "72 km/h" "m/s"')
    c.add_argument("quantity")
    c.add_argument("target")
    k = sub.add_parser("check", help='check "v = d / t" --var v=m/s --var d=m --var t=s')
    k.add_argument("equation")
    k.add_argument("--var", action="append", default=[], metavar="NAME=UNIT")
    d = sub.add_parser("dims", help='dimensions of "km/h"')
    d.add_argument("expression")
    args = ap.parse_args(argv)
    try:
        if args.cmd == "convert":
            print(f"{args.quantity} = {show(convert(args.quantity, args.target))} {args.target}")
            for note in traps(args.quantity, args.target):
                print("watch out:", note)
        elif args.cmd == "check":
            v = dict(s.split("=", 1) for s in args.var)
            r = check_equation(args.equation, v)
            print(("OK: " if r["ok"] else "MISMATCH: ") + r["message"])
            return 0 if r["ok"] else 1
        else:
            print(dim_text(dimension_of(args.expression)))
    except DimensionError as e:
        print("error:", e)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
