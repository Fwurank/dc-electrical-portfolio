import math


def interp(table: dict, x: float) -> float:
    """Piecewise-linear interpolation in a {x: y} table, clamped at the ends."""
    ks = sorted(table)
    if x <= ks[0]:
        return table[ks[0]]
    if x >= ks[-1]:
        return table[ks[-1]]
    for a, b in zip(ks, ks[1:]):
        if a <= x <= b:
            return table[a] + (table[b] - table[a]) * (x - a) / (b - a)
    raise ValueError(x)


def step_lookup(table: dict, n: int) -> float:
    """Value for the largest key <= n (grouping tables: use the entry for n or the next tabulated)."""
    ks = sorted(table)
    best = table[ks[0]]
    for k in ks:
        if k <= n:
            best = table[k]
    return best


def i_3ph(p_kw: float, u_v: float = 400.0, pf: float = 1.0) -> float:
    """Line current (A) of a balanced three-phase load."""
    return p_kw * 1000.0 / (math.sqrt(3) * u_v * pf)


def next_std(value: float, series) -> float:
    for s in sorted(series):
        if s >= value - 1e-9:
            return s
    return None
