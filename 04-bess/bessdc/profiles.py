"""Synthetic but realistic hourly profiles (8760 h) for the design year.

* Ambient temperature, Dalarna: annual mean ≈ +4.5 °C, seasonal + diurnal cycles, AR(1) weather noise,
  a 5-day July heat wave peaking at the +32 °C design ambient (DB-001 §3).
* Campus demand = IT nameplate × utilisation(t) × PUE(T) where PUE(T) comes from the project-02 bin model (dcsizing),
  calibrated so that 100 % utilisation at +32 °C equals the CALC-002 design peak (37.8 MW).
* SE3 day-ahead price: synthetic shape (season, double daily peak, multi-day regimes, spikes, negative hours)
  scaled to the public Nord Pool annual mean.  Capacity prices: public annual means + hourly noise.
"""
import os
import sys
from functools import lru_cache

import numpy as np

from .assumptions import Site, Prices, PRICE_TABLE

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "02-load-sizing"))
from dcsizing import scenario as _S  # noqa: E402

H = 8760
HOURS = np.arange(H)
DOY = HOURS // 24
HOD = HOURS % 24
DOW = DOY % 7                    # day 0 = Monday (design year)
HEATWAVE_DAYS = range(196, 201)  # 15–19 July


def _ar1(rng, n, rho, sigma):
    x = np.zeros(n)
    e = rng.normal(0, sigma * np.sqrt(1 - rho ** 2), n)
    for i in range(1, n):
        x[i] = rho * x[i - 1] + e[i]
    return x


def temperature(site: Site = None):
    site = site or Site()
    rng = np.random.default_rng(site.seed)
    season = 4.5 - 11.5 * np.cos(2 * np.pi * (DOY - 15) / 365)          # Jan ≈ −7, Jul ≈ +16
    diurnal_amp = 2.0 + 3.0 * (1 - np.cos(2 * np.pi * (DOY - 15) / 365)) / 2
    diurnal = diurnal_amp * np.cos(2 * np.pi * (HOD - 15) / 24)
    t = season + diurnal + _ar1(rng, H, 0.985, 4.0)
    for d in HEATWAVE_DAYS:                                               # design heat wave
        idx = DOY == d
        peak = site.heatwave_c - (2.0 if d in (196, 200) else 0.0)
        t[idx] = peak - 6 + 6 * np.cos(2 * np.pi * (HOD[idx] - 15) / 24)
    return np.clip(t, -30, site.heatwave_c)


@lru_cache(maxsize=4)
def _pue_bins(u):
    r = _S.run(_S.Inputs(it_util=u))
    b = r["annual"]["bins"]
    return np.array([x["t_c"] for x in b]), np.array([x["pue"] for x in b])


def pue_of_t(t, site: Site = None):
    site = site or Site()
    tb, pb = _pue_bins(0.8)
    pue = np.interp(t, tb, pb)
    k = site.design_peak_mw / (site.it_nameplate_mw * np.interp(site.heatwave_c, tb, pb))   # calibrate to 37.8 MW
    return pue * k


def utilisation(site: Site = None):
    site = site or Site()
    rng = np.random.default_rng(site.seed + 1)
    diurnal = np.where((HOD >= 9) & (HOD <= 22), np.sin(np.pi * (HOD - 9) / 13), 0.0) - 0.35
    weekday = np.where(DOW < 5, 0.015, -0.03)
    u = site.u_mean + site.u_diurnal * diurnal + weekday + _ar1(rng, H, 0.9, site.u_noise)
    # AI/batch campaigns: one 6-h block per week at near-full utilisation
    for w in range(52):
        d0 = w * 7 + rng.integers(0, 5)
        h0 = d0 * 24 + rng.integers(10, 16)
        u[h0:h0 + 6] = np.maximum(u[h0:h0 + 6], rng.uniform(0.93, 0.98))
    # design coincidence: heat-wave afternoons at 100 % nameplate
    for d in HEATWAVE_DAYS:
        idx = (DOY == d) & (HOD >= 12) & (HOD <= 18)
        u[idx] = np.maximum(u[idx], 0.97 if d != 198 else 1.0)
    return np.clip(u, 0.4, 1.0)


def recharge_event(site: Site = None):
    """UPS recharge after a campus-wide discharge, on the hottest afternoon (conservative coincidence)."""
    site = site or Site()
    r = np.zeros(H)
    h0 = 198 * 24 + 15
    n_full = int(round(site.recharge_h))
    r[h0:h0 + n_full] = site.recharge_mw
    r[h0 + n_full] = 0.5 * site.recharge_mw
    return r


def campus_load(site: Site = None, recharge=True):
    """Returns (load_mw, per_mw_it) — per_mw_it = demand per MW of IT nameplate (for adding extra IT)."""
    site = site or Site()
    t = temperature(site)
    per = utilisation(site) * pue_of_t(t, site)
    load = site.it_nameplate_mw * per + (recharge_event(site) if recharge else 0.0)
    return load, per


def spot_price(pr: Prices = None, seed=7):
    pr = pr or Prices()
    rng = np.random.default_rng(seed)
    season = 1 + 0.35 * np.cos(2 * np.pi * (DOY - 20) / 365)
    daily = (np.exp(-((HOD - 8) / 2.0) ** 2) + 1.1 * np.exp(-((HOD - 18) / 2.5) ** 2) - 0.45)
    regime = np.exp(_ar1(rng, H, 0.995, 0.55))                         # multi-day wind/hydro regimes
    p = season * regime * (1 + 2 * pr.spot_daily_spread * daily * np.clip(regime, 0.5, 2.0))
    p += np.where(rng.random(H) < 0.004, rng.lognormal(1.5, 0.6, H), 0.0)  # scarcity spikes (×)
    p = p / p.mean() * pr.spot_mean
    thr = np.quantile(p, pr.neg_share)                                  # low-price windy/hydro hours ≤ 0
    p = np.where(p <= thr, p - thr - rng.uniform(0, 3, H), p)
    return p * (pr.spot_mean / p.mean())


def capacity_prices(pr: Prices = None, seed=11):
    pr = pr or Prices()
    rng = np.random.default_rng(seed)
    base = PRICE_TABLE[pr.scenario]
    out = {}
    for i, (k, v) in enumerate(base.items()):
        x = rng.lognormal(0, 0.45, H) * (1 + 0.25 * np.cos(2 * np.pi * (DOY - 100) / 365))  # spring high (SVK-FCR-2025)
        out[k] = x / x.mean() * v
    return out
