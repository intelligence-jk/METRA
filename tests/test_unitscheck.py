from fractions import Fraction

import pytest

from unitscheck import DimensionError, check_equation, convert, dimension_of, traps
from unitscheck.cli import main


def test_kmh_to_ms_exact():
    assert convert("72 km/h", "m/s") == 20


def test_ms_to_kmh():
    assert convert("20 m/s", "km/h") == 72


def test_five_over_eighteen():
    assert convert("1 km/h", "m/s") == Fraction(5, 18)


def test_area():
    assert convert("1 m^2", "cm^2") == 10000


def test_volume_and_litres():
    assert convert("1 m^3", "cm^3") == 1000000
    assert convert("1 m^3", "L") == 1000


def test_time_and_decimals():
    assert convert("1.5 h", "min") == 90
    assert convert("250 g", "kg") == Fraction(1, 4)


def test_convert_dimension_mismatch():
    with pytest.raises(DimensionError):
        convert("5 km", "kg")


def test_dimensions():
    assert dimension_of("m/s^2") == (1, -2, 0)
    assert dimension_of("N") == (1, -2, 1)


def test_equation_ok():
    r = check_equation("v = d / t", {"v": "m/s", "d": "km", "t": "h"})
    assert r["ok"]


def test_equation_mismatch_detected():
    r = check_equation("v = d * t", {"v": "m/s", "d": "m", "t": "s"})
    assert not r["ok"]


def test_adding_unlike_dimensions_rejected():
    with pytest.raises(DimensionError):
        check_equation("5 m + 3 s = 8 m")


def test_numeric_equation():
    r = check_equation("72 km / 1 h = 20 m / 1 s")
    assert r["ok"] and r["numbers_equal"]


def test_force_equation():
    assert check_equation("F = m * a", {"F": "N", "m": "kg", "a": "m/s^2"})["ok"]


def test_traps():
    assert any("5/18" in n for n in traps("72 km/h", "m/s"))
    assert any("f^2" in n for n in traps("1 m^2", "cm^2"))
    assert traps("5 km", "m") == []


def test_cli(capsys):
    assert main(["convert", "72 km/h", "m/s"]) == 0
    assert "= 20 m/s" in capsys.readouterr().out
    assert main(["check", "v = d * t", "--var", "v=m/s", "--var", "d=m", "--var", "t=s"]) == 1
