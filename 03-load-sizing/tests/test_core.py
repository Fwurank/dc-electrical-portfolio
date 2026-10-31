import math
import pytest
from dcsizing import load as L, transformer as T, generator as G, ups as U, cables as C, busway as B, scenario as S
from dcsizing.tables import CLIMATE_BINS_DALARNA, IZ_TABLES


# ---------------- load
def test_climate_bins_sum_to_year():
    assert sum(h for _, h in CLIMATE_BINS_DALARNA) == 8760


def test_ups_efficiency_interp_and_clamp():
    assert L.ups_efficiency(0.5) == pytest.approx(0.965)
    assert L.ups_efficiency(0.625) == pytest.approx(0.9655)
    assert L.ups_efficiency(0.0) == pytest.approx(0.90)


def test_mech_ppue_model():
    assert L.mech_ppue(0) == pytest.approx(0.05)
    assert L.mech_ppue(32) == pytest.approx(0.17)
    assert L.mech_ppue(22) == pytest.approx(0.11)


def test_hall_load_matches_phase1():
    h = L.hall_load(5000, 32, 0.625)
    assert h.mech_kw == pytest.approx(850)
    assert 6150 < h.total_kw < 6300          # phase-1: 6.24 MW
    assert 1.22 < h.ppue < 1.26


def test_back_solve_mech_ppue_roundtrip():
    m = L.solve_mech_peak_for_target_pue(1.25, 5000, 32, 0.625)
    h = L.hall_load(5000, 32, 0.625, ppue_peak=m)
    assert h.ppue == pytest.approx(1.25, abs=1e-9)


def test_annual_pue_reasonable():
    a = L.annual_pue(5000, 6, 0.625)
    assert a["hours"] == 8760
    assert 1.10 < a["pue"] < 1.20
    assert 180_000 < a["facility_mwh"] < 240_000


# ---------------- redundancy schemes
@pytest.mark.parametrize("scheme,n,blocks,normal,failure", [
    ("DR", 4, 4, 1250, 5000 / 3),
    ("2N", 2, 4, 1250, 2500),
    ("N+1", 3, 4, 1250, 5000 / 3),
    ("BR", 4, 5, 1250, 1250),
])
def test_block_loads(scheme, n, blocks, normal, failure):
    b = S.block_loads(5000, scheme, n)
    assert b["blocks"] == blocks
    assert b["normal"] == pytest.approx(normal)
    assert b["failure"] == pytest.approx(failure)


def test_dr_requires_three_blocks():
    with pytest.raises(ValueError):
        S.block_loads(5000, "DR", 2)


# ---------------- transformer & short circuit
def test_transformer_selection_limits():
    assert T.select_transformer(2050, 1620) == 2500
    assert T.select_transformer(2050, 2100) == 3150     # normal ≤ 80 % governs


def test_transformer_losses():
    assert T.losses_kw(2500, 2500, p0_pk=(3.1, 19.0)) == pytest.approx(22.1)
    assert T.losses_kw(2500, 1250, p0_pk=(3.1, 19.0)) == pytest.approx(3.1 + 19 / 4)


def test_lv_short_circuit_about_52_ka():
    r = T.ik3_at_lv_bus(2500, 0.06, 19.0, 450)
    assert r["ik_ka"] == pytest.approx(52, abs=3)
    assert 2.0 < r["ip_ka"] / r["ik_ka"] < 2.6


def test_lv_short_circuit_infinite_bus_bound():
    # infinite MV source: I''k ≈ c·Ir/uk·KT-ish → must exceed finite-source value
    r_inf = T.ik3_at_lv_bus(2500, 0.06, 19.0, 1e9)
    r = T.ik3_at_lv_bus(2500, 0.06, 19.0, 450)
    assert r_inf["ik_ka"] > r["ik_ka"]


def test_mv_short_circuit_about_14_ka():
    assert T.ik3_mv(3000, 63, 0.12, 250) == pytest.approx(13.5, abs=1.5)


# ---------------- generator
def test_generator_derating():
    assert G.derate_factor(32, 150) == 1.0
    assert G.derate_factor(45, 150) == pytest.approx(1 - 0.075)
    assert G.derate_factor(40, 1500) == pytest.approx(0.95)


def test_generator_selection_reference():
    g = G.select_genset(1927, 380, 32, 150, 0.90)
    assert g["kva"] == 2750 and g["loading_kw"] == pytest.approx(1927 / 2200)


def test_generator_step_load_governs():
    g = G.select_genset(950, 405, largest_step_kw=400)
    assert g["kva"] == 1650 and g["governed_by"] == "step load"


def test_voltage_dip():
    assert G.transient_voltage_dip(0, 2750) == 0
    assert G.transient_voltage_dip(2750 * 0.5, 2750, 0.22) == pytest.approx(0.11 / 1.11)


def test_fuel():
    assert G.sfc(1.0) == pytest.approx(0.26)
    assert G.fuel_rate_lph(2200, 2200) == pytest.approx(572)
    v = G.tank_volume_for_autonomy(24, 2200, 2200, usable_frac=1.0)
    assert G.autonomy_hours(v, 2200, 2200, usable_frac=1.0) == pytest.approx(24)


# ---------------- UPS & battery
def test_ups_selection():
    u = U.select_ups(5000 / 3, 1000, 0.9)
    assert u["modules"] == 2 and u["loading_failure"] == pytest.approx(0.8333, abs=1e-3)


def test_battery_energy_about_119_kwh():
    assert U.battery_energy_required(1000, 5, 25) == pytest.approx(119.3, abs=0.5)


def test_battery_c_rate_governs():
    b = U.size_battery(1000, 5, 25, c_max=8.0)
    assert b["governed_by"].startswith("C-rate")
    assert b["e_required_kwh"] == pytest.approx(161.1, abs=0.5)


def test_battery_cold_room_needs_more_energy():
    assert U.battery_energy_required(1000, 5, 15) > U.battery_energy_required(1000, 5, 25)


def test_autonomy_inverse():
    e = U.battery_energy_required(1000, 7, 25)
    assert U.autonomy_min(e, 1000, 25) == pytest.approx(7)


def test_ups_input_current_exceeds_1600():
    assert U.input_current(1000, 0.963, 100) == pytest.approx(1660, abs=10)


# ---------------- cables
def test_iz_tables_monotonic():
    for tbl in IZ_TABLES.values():
        v = [tbl[k] for k in sorted(tbl)]
        assert v == sorted(v)


def test_resistance_at_90c():
    assert C.r_ohm_per_km(240, "Cu", 20) == pytest.approx(0.0754)
    assert C.r_ohm_per_km(240, "Cu", 90) == pytest.approx(0.0754 * (1 + 0.00393 * 70))


def test_correction_factors():
    assert C.k_ambient(30) == pytest.approx(1.0)
    assert C.k_ambient(40) == pytest.approx(0.91)
    assert C.k_group(1, "F_trefoil") == pytest.approx(0.98)  # B.52.21, 1 tray, 1 circuit
    assert C.k_group(3, "E_multi") < 1.0


def test_short_circuit_min_section():
    # 50 kA for 0.1 s on Cu/XLPE (k = 143): S ≥ 50000·√0.1 / 143 ≈ 110.6 mm²
    assert C.min_size_short_circuit(50, 0.1) == pytest.approx(110.6, abs=0.2)


def test_voltage_drop_formula():
    vd = C.voltage_drop_pct(100, 100, 50, "Cu", 1, 1.0)
    r = C.r_ohm_per_km(50, "Cu", 90) / 1000
    assert vd == pytest.approx(math.sqrt(3) * 100 * 100 * r / 400 * 100)


def test_size_cable_satisfies_all_criteria():
    r = C.size_cable(1660, 25, "Cu", "F_trefoil", 35, 3, vd_limit_pct=1.0, ik_ka=54, t_clear_s=0.1, in_a=2000)
    assert r.ok
    assert r.ib_a <= r.in_a <= r.iz_a
    assert r.vd_pct <= 1.0
    assert r.size_mm2 >= r.s_min_sc_mm2


def test_size_cable_vd_governs_long_run():
    short = C.size_cable(100, 10, vd_limit_pct=3.0, method="E_multi")
    long_ = C.size_cable(100, 300, vd_limit_pct=3.0, method="E_multi")
    assert long_.size_mm2 * long_.n_parallel > short.size_mm2 * short.n_parallel


# ---------------- busway
def test_busway_selection_and_icw_flag():
    b = B.select_busway(614, 60, 40, distributed=True, ik_ka=54)
    assert b["rating_a"] == 800 and b["sc_ok"] is False


# ---------------- scenario integration
def test_reference_case():
    r = S.run()
    assert r["block"]["normal"] == pytest.approx(1250)
    assert r["block"]["failure"] == pytest.approx(1666.7, abs=0.1)
    assert r["tx"]["kva"] == 2500 and r["gen"]["kva"] == 2750
    assert r["ups"]["rating_kw"] == 2000
    assert r["sc"]["ik_msb_ka"] == pytest.approx(52, abs=3)
    assert 37_000 < r["campus"]["p_kw"] < 39_000           # ≈ 38 MW
    assert 1.24 < r["campus"]["pue"] < 1.29
    assert r["hv_loading"] < 1.0


def test_rating_changes_reference():
    ch = {c["item"]: c for c in S.rating_changes(S.run())}
    assert ch["Battery per 1 000 kW module (kWh nameplate)"]["change"]
    assert ch["UPS rectifier input breaker (A)"]["project03"] == 2000
    assert not ch["IT block transformer (kVA)"]["change"]


@pytest.mark.parametrize("scheme,n", [("DR", 3), ("DR", 4), ("DR", 5), ("2N", 2), ("N+1", 3), ("BR", 4)])
def test_all_schemes_run(scheme, n):
    r = S.run(S.Inputs(scheme=scheme, n_blocks=n))
    assert r["flags"]
    assert r["installed"]["ups_ratio"] >= 1.0


def test_hot_site_derates_genset():
    r = S.run(S.Inputs(ambient_design_c=45, altitude_m=1200))
    assert r["gen"]["derate"] < 1.0
