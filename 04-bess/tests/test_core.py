"""Behavioural tests of the BESS study modules (physics/economics sanity, not implementation details)."""
import math

import numpy as np
import pytest

from bessdc import assumptions as A, profiles as P, dispatch as D, backup as B, ai_swing as AI, business as Bz


@pytest.fixture(scope="module")
def load():
    return P.campus_load(A.Site())


# ---------------------------------------------------------------- profiles
def test_profile_calibrated_to_calc002_design_peak():
    L, per = P.campus_load(A.Site(), recharge=False)
    assert L.max() == pytest.approx(37.818, abs=0.01)          # 100 % IT at +32 °C = CALC-002 design peak
    assert len(L) == 8760 and 24 < L.mean() < 32


def test_recharge_peak_exceeds_subscription(load):
    L, _ = load
    assert L.max() == pytest.approx(37.818 + 4.8, abs=0.01)   # CALC-002 campus max incl. UPS recharge
    assert L.max() > 40.0


def test_spot_price_matches_public_mean_and_negative_share():
    s = P.spot_price(A.Prices())
    assert s.mean() == pytest.approx(46.23, rel=1e-6)
    assert 0.03 < (s <= 0).mean() < 0.05


def test_capacity_prices_match_table():
    cp = P.capacity_prices(A.Prices(scenario="2026"))
    for k, v in A.PRICE_TABLE["2026"].items():
        assert cp[k].mean() == pytest.approx(v, rel=1e-9)


# ---------------------------------------------------------------- (a) peak shaving
def test_no_bess_headroom_is_closed_form(load):
    L, per = load
    x = D.max_extra_it(L, per, 40.0, A.Bess(), 0, 0)["x_mw"]
    assert x == pytest.approx(np.min((40 - L) / per))
    assert x < 0                                              # recharge peak already above 40 MW


def test_bess_increases_extra_it_and_respects_limit(load):
    L, per = load
    b = A.Bess()
    r = D.max_extra_it(L, per, 40.0, b)
    assert r["x_mw"] > D.max_extra_it(L, per, 40.0, b, 0, 0)["x_mw"] + 2
    assert r["grid"].max() <= 40.0 + 1e-6
    assert r["e"].min() >= b.soc_min * b.e_mwh - 1e-6 and r["e"].max() <= b.soc_max * b.e_mwh + 1e-6
    assert np.all(r["d"] <= b.p_mw + 1e-6)


def test_soc_balance_with_losses(load):
    L, per = load
    b = A.Bess()
    r = D.max_extra_it(L, per, 40.0, b)
    eta = math.sqrt(b.eta_rt)
    # cyclic: energy in × ηc = energy out / ηd
    assert r["c"].sum() * eta == pytest.approx(r["d"].sum() / eta, rel=1e-6, abs=1e-6)


def test_extra_it_monotonic_in_energy(load):
    L, per = load
    xs = [D.max_extra_it(L, per, 40.0, A.Bess(), e_mwh=e)["x_mw"] for e in (5, 10, 20, 40)]
    assert all(b >= a - 1e-9 for a, b in zip(xs, xs[1:]))


# ---------------------------------------------------------------- (c) revenue
@pytest.fixture(scope="module")
def coopt(load):
    L, per = load
    pr = A.Prices()
    return D.co_optimise(L, 40.0, P.spot_price(pr), P.capacity_prices(pr), A.Bess())


def test_reserves_respect_power_and_endurance(coopt):
    b = A.Bess()
    r = coopt.reserves
    up = r["fcrn"] + r["fcrd_up"] + r["mfrr_up"] + coopt.d - coopt.c
    dn = r["fcrn"] + r["fcrd_dn"] + coopt.c - coopt.d
    assert up.max() <= b.p_mw + 1e-6 and dn.max() <= b.p_mw + 1e-6
    eta = math.sqrt(b.eta_rt)
    need_up = b.soc_min * b.e_mwh + (r["fcrn"] * 1 + r["fcrd_up"] / 3 + r["mfrr_up"] * 1) / eta
    assert np.all(coopt.e >= need_up - 1e-5)


def test_grid_limit_includes_down_activation(load, coopt):
    L, _ = load
    g = L + coopt.c - coopt.d + coopt.reserves["fcrn"] + coopt.reserves["fcrd_dn"]
    assert np.max(g) <= 40.0 + coopt.overshoot_mw + 1e-5


def test_revenue_scenarios_ordered(load):
    L, _ = load
    tot = {}
    for sc in ("2025", "2026", "saturated"):
        pr = A.Prices(scenario=sc)
        tot[sc] = D.co_optimise(L, 40.0, P.spot_price(pr), P.capacity_prices(pr), A.Bess()).total
    assert tot["2025"] > tot["2026"] > tot["saturated"] > 0


def test_grid_constraint_costs_revenue_not_creates_it(load):
    L, per = load
    pr = A.Prices()
    s, cp = P.spot_price(pr), P.capacity_prices(pr)
    free = D.co_optimise(L, 40.0, s, cp, A.Bess(), grid_limited=False).total
    tight = D.co_optimise(L + 2.4 * per, 40.0, s, cp, A.Bess()).total
    assert tight <= free + 1e-3


# ---------------------------------------------------------------- (b) backup
def test_backup_autonomy_and_replace_all():
    usable, rows = B.autonomy(A.Bess())
    assert usable == pytest.approx(0.9 * 20 * math.sqrt(0.88))
    assert rows[-1]["minutes"] < 30 and not rows[-1]["power_ok"]
    ra = B.replace_all_gensets()
    assert ra["e_mwh"] > 600 and ra["ratio"] > 2


def test_island_fault_current_too_low_for_mv_relays():
    isl = B.island_fault_check(A.Bess())
    assert isl["i_mv_a"] == pytest.approx(1.2 * 11e6 / (math.sqrt(3) * 20e3))
    r = {x["device"]: x for x in isl["rows"]}
    assert not r["R-FDR hall feeder 20 kV"]["ok"]            # inverse-time relay too slow
    assert r["R-INC 20 kV incomer"]["multiple"] < 1           # below pick-up
    assert isl["ik_msg20_worst_with_bess_ka"] < isl["switchgear_ka"]


# ---------------------------------------------------------------- (d) AI swing
def test_ai_smoothing_meets_ramp_with_fast_response():
    a = A.AiSwing()
    t, L = AI.ai_profile(a)
    m0 = AI.metrics(t, L, AI.smooth(L, a, response_ms=0), a)
    assert m0["load_1min_change_mw"] > 3 * a.ramp_mw_min
    assert m0["ok_ramp"]
    assert m0["p_bess_req_mw"] < a.p_ai_mw * 1.05 and m0["e_req_mwh"] < 1.5


def test_slow_response_leaves_ripple_and_hybrid_fixes_it():
    a = A.AiSwing()
    rs = AI.sweep_response(a, (0, 150, 600))
    pp = [r["grid_osc_pp_mw"] for r in rs]
    assert pp[0] < pp[1] < pp[2]
    _, _, _, mh = AI.hybrid(a)
    assert mh["ok_osc"] and mh["e_sc_kwh"] < 100


def test_tighter_ramp_needs_more_energy():
    sw = AI.sweep_ramp(A.AiSwing(), (1, 3, 10))
    e = [r["e_req_mwh"] for r in sw]
    assert e[0] > e[1] > e[2]


# ---------------------------------------------------------------- (e) business
def test_capex_formula():
    f = A.Finance()
    assert Bz.capex_eur(10, 20, f) == pytest.approx((120 * 20e3 + 75 * 10e3) * 1.2 + 300e3)


def test_kpis_simple_annuity():
    rows = [{"cf": 100.0}] * 10
    k = Bz.kpis(500.0, rows, 0.0)
    assert k["npv"] == pytest.approx(500.0)
    assert k["payback_y"] == pytest.approx(5.0)
    assert Bz.kpis(500.0, rows, 0.1)["irr"] == pytest.approx(0.1508, abs=1e-3)


def test_business_case_saturation_lowers_npv():
    base = Bz.case()
    sat = Bz.case(pr=A.Prices(scenario="saturated"))
    assert base["kpi"]["npv"] > sat["kpi"]["npv"]
    assert base["kpi"]["capex"] == pytest.approx(4.08e6)
    assert any(r["augmentation"] < 0 for r in base["rows"]) or base["rows"][-1]["soh_end"] >= 0.8


def test_register_has_provenance_tags():
    reg = A.register(A.Site(), A.Bess(), A.Prices(), A.Finance(), A.AiSwing())
    assert {r["tag"] for r in reg} <= {"PUBLIC", "ASSUMED", "PROJECT"}
    assert all(r["note"] for r in reg)
    titles = {t for t, _ in A.SOURCES.values()}
    assert all(r["source"] in titles for r in reg if r["tag"] == "PUBLIC")   # every PUBLIC value is cited
