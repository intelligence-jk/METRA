"""Exact unit conversion and dimension checking for school physics and maths."""
from .core import (Dim, DimensionError, Quantity, check_equation, convert,
                   dimension_of, evaluate, parse_quantity, traps)

__all__ = ["Dim", "DimensionError", "Quantity", "check_equation", "convert",
           "dimension_of", "evaluate", "parse_quantity", "traps"]
