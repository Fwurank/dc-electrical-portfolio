"""Linear programmes (scipy.optimize.linprog / HiGHS) for BESS dispatch, hourly resolution.

Common BESS model (per hour t, Δt = 1 h):
    e[t+1] = e[t] + η_c·c[t] − d[t]/η_d ,   0 ≤ c,d ≤ P ,   E_min ≤ e ≤ E_max ,   e[T] = e[0]  (cyclic)
    η_c = η_d = √η_rt
(a) max_extra_it:  maximise x (MW IT nameplate) s.t.  L0[t] + x·s[t] + c[t] − d[t] ≤ P_lim
(c) co_optimise:   maximise Σ π_k·r_k + λ·(d − c) − c_deg·d − losses   with reserve head-room, endurance (LER) and
                   grid-limit constraints (down-regulation activation also consumes import head-room).
"""
from dataclasses import dataclass

import numpy as np
import scipy.sparse as sp
from scipy.optimize import linprog

from .assumptions import Bess, ENDURANCE_H

OVERSHOOT_EUR_MWH = 5000.0    # penalty on exceeding the subscription (soft constraint, keeps small BESS feasible)
PRODUCTS = ("fcrn", "fcrd_up", "fcrd_dn", "mfrr_up")
UP = {"fcrn": 1, "fcrd_up": 1, "fcrd_dn": 0, "mfrr_up": 1}
DN = {"fcrn": 1, "fcrd_up": 0, "fcrd_dn": 1, "mfrr_up": 0}


class _Idx:
    """Column layout helper: blocks of length T (or 1) in one decision vector."""

    def __init__(self, T, blocks):
        self.T, self.off, n = T, {}, 0
        for name, ln in blocks:
            self.off[name] = (n, ln)
            n += ln
        self.n = n

    def __getitem__(self, name):
        o, ln = self.off[name]
        return np.arange(o, o + ln)


def _soc_rows(ix, b: Bess, e_mwh, T):
    """Equality rows e[t+1] − e[t] − ηc c[t] + d[t]/ηd = 0 (cyclic)."""
    eta = np.sqrt(b.eta_rt)
    t = np.arange(T)
    tn = (t + 1) % T
    rows = np.concatenate([t, t, t, t])
    cols = np.concatenate([ix["e"][tn], ix["e"][t], ix["c"][t], ix["d"][t]])
    vals = np.concatenate([np.ones(T), -np.ones(T), -eta * np.ones(T), np.ones(T) / eta])
    return sp.csr_matrix((vals, (rows, cols)), shape=(T, ix.n))


def _solve(c, A_ub, b_ub, A_eq, b_eq, bounds):
    r = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method="highs")
    if r.status != 0:
        raise RuntimeError(f"LP failed: {r.message}")
    return r


def max_extra_it(load0, per_mw, p_lim, b: Bess, e_mwh=None, p_mw=None):
    """(a) Max. extra IT nameplate x (MW) under the import limit with BESS (P, E)."""
    p_mw = b.p_mw if p_mw is None else p_mw
    e_mwh = b.e_mwh if e_mwh is None else e_mwh
    T = len(load0)
    if p_mw <= 0 or e_mwh <= 0:
        x = float(np.min((p_lim - load0) / per_mw))       # negative = limit already exceeded
        return {"x_mw": x, "c": np.zeros(T), "d": np.zeros(T), "e": np.zeros(T), "grid": load0 + x * per_mw}
    ix = _Idx(T, [("x", 1), ("c", T), ("d", T), ("e", T)])
    t = np.arange(T)
    rows = np.concatenate([t, t, t])
    cols = np.concatenate([np.zeros(T, int), ix["c"], ix["d"]])
    vals = np.concatenate([per_mw, np.ones(T), -np.ones(T)])
    A_ub = sp.csr_matrix((vals, (rows, cols)), shape=(T, ix.n))
    b_ub = p_lim - load0
    A_eq = _soc_rows(ix, b, e_mwh, T)
    bounds = [(None, None)] + [(0, p_mw)] * (2 * T) + [(e_mwh * b.soc_min, e_mwh * b.soc_max)] * T
    cost = np.zeros(ix.n)
    cost[0] = -1.0
    cost[ix["d"]] = 1e-6          # tie-break: avoid needless cycling …
    cost[ix["e"]] = -1e-7         # … and keep the battery charged while waiting for the peak
    r = _solve(cost, A_ub, b_ub, A_eq, np.zeros(T), bounds)
    x = r.x[0]
    c, d, e = r.x[ix["c"]], r.x[ix["d"]], r.x[ix["e"]]
    return {"x_mw": float(x), "c": c, "d": d, "e": e, "grid": load0 + x * per_mw + c - d}


@dataclass
class CoOptResult:
    revenue: dict            # EUR/yr by stream (after availability)
    total: float
    reserves: dict           # MW profiles
    c: np.ndarray
    d: np.ndarray
    e: np.ndarray
    grid: np.ndarray
    efc: float               # equivalent full cycles per year (on usable energy)
    overshoot_mw: float = 0.0  # max. import above the limit that the BESS could not shave


def co_optimise(load, p_lim, spot, cap_prices, b: Bess, e_mwh=None, p_mw=None, products=PRODUCTS,
                grid_limited=True, energy_fee=1.5, fcrn_act=0.10, enforce_peak=True):
    """(c) Revenue stacking co-optimised with the grid import limit of (a).

    Arbitrage is behind-the-meter (no export): discharging offsets campus import valued at spot + transfer fee.
    """
    p_mw = b.p_mw if p_mw is None else p_mw
    e_mwh = b.e_mwh if e_mwh is None else e_mwh
    T = len(load)
    blocks = [("c", T), ("d", T), ("e", T)] + [(k, T) for k in products] + [("ov", T)]   # ov: overshoot slack
    ix = _Idx(T, blocks)
    t = np.arange(T)
    eta = np.sqrt(b.eta_rt)
    rows, cols, vals, rhs = [], [], [], []
    r0 = 0

    def add(row_cols, row_vals, b_vec):
        nonlocal r0
        for cc, vv in zip(row_cols, row_vals):
            rows.append(t + r0)
            cols.append(cc)
            vals.append(np.full(T, vv) if np.isscalar(vv) else vv)
        rhs.append(b_vec)
        r0 += T

    up = [k for k in products if UP[k]]
    dn = [k for k in products if DN[k]]
    # power head-room up:  d − c + Σ r_up ≤ P ;  down: c − d + Σ r_dn ≤ P
    add([ix["d"], ix["c"]] + [ix[k] for k in up], [1, -1] + [1] * len(up), np.full(T, p_mw))
    add([ix["c"], ix["d"]] + [ix[k] for k in dn], [1, -1] + [1] * len(dn), np.full(T, p_mw))
    # endurance (LER): e ≥ Emin + Σ r_up·h_up/ηd ;  e ≤ Emax − Σ r_dn·h_dn·ηc
    add([ix["e"]] + [ix[k] for k in up], [-1] + [ENDURANCE_H[k] / eta for k in up], np.full(T, -b.soc_min * e_mwh))
    add([ix["e"]] + [ix[k] for k in dn], [1] + [ENDURANCE_H[k] * eta for k in dn], np.full(T, b.soc_max * e_mwh))
    # grid limit incl. full down-activation:  L + c − d + Σ r_dn ≤ P_lim
    if grid_limited and enforce_peak:
        add([ix["c"], ix["d"], ix["ov"]] + [ix[k] for k in dn], [1, -1, -1] + [1] * len(dn), p_lim - load)
    A_ub = sp.csr_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(r0, ix.n))
    b_ub = np.concatenate(rhs)
    A_eq = _soc_rows(ix, b, e_mwh, T)
    bounds = [(0, p_mw)] * (2 * T) + [(b.soc_min * e_mwh, b.soc_max * e_mwh)] * T + [(0, p_mw)] * (len(products) * T) + [(0, None)] * T
    lam = spot + energy_fee
    cost = np.zeros(ix.n)
    cost[ix["c"]] = lam
    cost[ix["d"]] = -lam + b.deg_cost_eur_mwh
    loss_fcrn = fcrn_act * 2 * (1 - b.eta_rt) * (np.maximum(spot, 0) + energy_fee) + fcrn_act * b.deg_cost_eur_mwh
    for k in products:
        cost[ix[k]] = -cap_prices[k] + (loss_fcrn if k == "fcrn" else 0.0)
    cost[ix["ov"]] = OVERSHOOT_EUR_MWH
    r = _solve(cost, A_ub, b_ub, A_eq, np.zeros(T), bounds)
    x = r.x
    c, d, e = x[ix["c"]], x[ix["d"]], x[ix["e"]]
    res = {k: x[ix[k]] for k in products}
    av = b.availability
    rev = {k: float(np.sum(cap_prices[k] * res[k])) * av for k in products}
    rev["arbitrage"] = float(np.sum(lam * (d - c))) * av
    rev["degradation"] = -float(np.sum(b.deg_cost_eur_mwh * d)) * av
    rev["fcrn_losses"] = -float(np.sum(loss_fcrn * res["fcrn"])) * av if "fcrn" in res else 0.0
    usable = (b.soc_max - b.soc_min) * e_mwh
    efc = float((d.sum() + fcrn_act * res.get("fcrn", np.zeros(T)).sum()) / usable)
    ov = float(x[ix["ov"]].max())
    return CoOptResult(rev, float(sum(rev.values())), res, c, d, e, load + c - d, efc, ov)
