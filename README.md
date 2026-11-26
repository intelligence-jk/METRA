# METRA: Measure-Error Tracker for Real Answers

Formerly `units-checker`.

Units and dimensions checker for school physics and maths.

## What it solves
Many lost marks come from units: km/h against m/s, cm^2 against m^2, or an equation whose two sides cannot possibly be equal. This tool converts between units exactly (as fractions, never rounded) and checks that both sides of an equation have the same dimensions in length (L), time (T) and mass (M). It also warns about the usual conversion traps. Standard library only, Python 3.10 or newer.

## Example
```bash
python -m unitscheck convert "72 km/h" m/s
```
```
72 km/h = 20 m/s
watch out: km/h to m/s: multiply by 5/18 (1000 m over 3600 s). m/s to km/h: multiply by 18/5.
```
```bash
python -m unitscheck convert "1 m^2" "cm^2"
```
```
1 m^2 = 10000 cm^2
watch out: Length appears to the power 2, so a length factor f becomes f^2 (for example 100 for cm to m becomes 10000).
```
Check an equation (here distance times time cannot be a speed):
```bash
python -m unitscheck check "v = d * t" --var v=m/s --var d=m --var t=s
```
```
MISMATCH: left side is L T^-1 but right side is L T
```
```bash
python -m unitscheck check "v = d / t" --var v=m/s --var d=km --var t=h
```
```
OK: both sides are L T^-1
```
Other commands: `python -m unitscheck dims "m/s^2"` prints `L T^-2`.

Units known: m, km, cm, mm, s, min, h, kg, g, N, J, W, Pa, L, ha. Use `^` for powers (`m^2`, `s^-1`). A number written next to a unit, as in `10 m / 2 s`, binds tighter than the division.

## The maths behind it
- Every unit is stored as an exact factor to SI (metre, second, kilogram) plus a dimension triple (L, T, M) of exponents. Multiplying quantities adds the exponents, dividing subtracts them, and a power multiplies them.
- Conversion: value in target = (value in SI) / (target factor). All arithmetic uses `Fraction`.
- km/h to m/s: 1 km/h = 1000 m / 3600 s = 5/18 m/s. So 72 km/h = 72 x 5/18 = 20 m/s.
- Area and volume: if a length factor is f, an area factor is f^2 and a volume factor is f^3. So 1 m = 100 cm gives 1 m^2 = 10000 cm^2 and 1 m^3 = 1000000 cm^3.
- A dimension check: two sides of an equation can only be equal if their exponent triples match. You can only add or subtract quantities of the same dimensions. A matching dimension does not prove an equation is right, but a mismatch proves it is wrong.

## Install and run
```bash
python -m pip install -e .
python -m pytest
python -m unitscheck convert "72 km/h" m/s
```

## Licence
MIT. Made by Math & Myth (mathandmyth.ae): one to one maths mentoring, online, across the UAE.
