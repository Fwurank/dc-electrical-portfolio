import math
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scprot import campus as C, study as S, pp_model as P, earthing as E, arcflash as AF
from scprot.iec60909 import Network, z_transformer, mu_factor, m_factor, kt_factor, GenDecrement
from scprot.protection import iec_time


@pytest.fixture(scope="module")
def res():
    return S.run()


# ---------------------------------------------------------------- IEC 60909 solver
def test_infinite_bus_transformer_analytic():
    net = Network(); net.add_node("HV", 20.0); net.add_node("LV", 0.4)
    zt = z_transformer(2.5, 0.42, 0.06, 19.0, kt=True, cmax=1.05)
    net.add_branch("T", "HV", "LV", zt, 20 / 0.42)
    net.add_shunt("Q", "HV", complex(1e-9, 1e-9))
    r = net.fault("LV")
    assert r["ik_ka"] == pytest.approx(1.05 * 0.4 / (math.sqrt(3) * abs(zt)), rel=1e-4)


def test_kt_and_kappa():
    assert kt_factor(0.06, 1.05) == pytest.approx(0.95 * 1.05 / (1 + 0.6 * 0.06), rel=1e-9)
    net = Network(); net.add_node("A", 0.4); net.add_shunt("S", "A", complex(0.1, 1.0) * 1e-3)
    r = net.fault("A")
    assert r["kappa"] == pytest.approx(1.02 + 0.98 * math.exp(-0.3), rel=1e-3)


def test_mu_and_m_factors():
    assert mu_factor(4.0, 0.1) == pytest.approx(0.62 + 0.72 * math.exp(-0.32 * 4.0), rel=1e-6)
    assert mu_factor(4.0, 0.02) == pytest.approx(0.84 + 0.26 * math.exp(-0.26 * 4.0), rel=1e-6)
    assert mu_factor(1.5, 0.1) == 1.0                       # far from generator (I''kG/IrG <= 2)
    k = 1.8
    exp = 1 / (2 * 50 * 1.0 * math.log(k - 1)) * (math.exp(4 * 50 * 1.0 * math.log(k - 1)) - 1)
    assert m_factor(k, 1.0) == pytest.approx(exp, rel=1e-9)


def test_genset_decrement_endpoints():
    g = GenDecrement(0.15, 0.22)
    assert g.i_pu(0.0) == pytest.approx(1.05 / 0.15, rel=1e-6)
    assert g.i_pu(30.0) == pytest.approx(3.0, rel=1e-3)


# ---------------------------------------------------------------- campus vs hand values (project 02)
def test_reproduces_project02_hand_values():
    d = C.Data(feeder_km=1e-6, tx_cable_km=1e-6, tx_msb_busduct_m=1e-6)
    f = C.run_scenario(C.SCENARIOS[0], d)["faults"]
    assert f["MSB-A"]["ik_ka"] == pytest.approx(53.8, abs=0.3)
    assert f["MV-A"]["ik_ka"] == pytest.approx(13.0, abs=0.1)


def test_full_model_levels(res):
    f = res["R"]["S0max"]["faults"]
    assert 51 < f["MSB-A"]["ik_ka"] < 53.8                  # cables/busduct reduce the hand value slightly
    assert f["MSB-A"]["ip_ka"] < 143
    assert res["R"]["S4"]["faults"]["MSB-A"]["ik_ka"] == pytest.approx(27.5, abs=0.5)   # project 02: 27.5 kA


# ---------------------------------------------------------------- pandapower cross-check
@pytest.mark.parametrize("kw,key", [({}, "S0max"), ({"parallel_hv": True}, "S1"),
                                     ({"grid": False, "genset": True}, "S4")])
def test_pandapower_agreement_max(kw, key, res):
    pp = P.ik_pp(**kw)
    own = res["R"][key]["faults"]
    for n, v in pp.items():
        if n in own and own[n]["ik_ka"] > 0 and not math.isnan(v["ik_ka"]):
            assert own[n]["ik_ka"] == pytest.approx(v["ik_ka"], rel=0.005), n
            if key != "S4":
                assert own[n]["ip_ka"] == pytest.approx(v["ip_ka"], rel=0.02), n


def test_pandapower_min_within_kt_difference(res):
    pp = P.ik_pp(case="min")
    own = res["R"]["S0min"]["faults"]
    for n in ("MV-A", "MSB-A", "RACK"):
        assert 0 <= own[n]["ik_ka"] / pp[n]["ik_ka"] - 1 < 0.05     # pandapower omits KT for Ik min


# ---------------------------------------------------------------- scenarios & ratings
def test_parallel_hv_transformers_thin_margin(res):
    s1 = res["R"]["S1"]["faults"]["MV-A"]
    assert 20 < s1["ik_ka"] < 25 and s1["ip_ka"] > 0.9 * 62.5
    assert any(r["sk_mva"] == 4000 and r["ip_s1"] > 62.5 for r in res["s1_sens"])


def test_rating_flags(res):
    bad = {(r["item"], r["case"]) for r in res["ratings"] if not r["ok"]}
    assert ("Busway 800 A", "S0 normal (start)") in bad
    assert ("MSB-A", "S3 LV closed transition") in bad
    assert ("MSB-A", "S0 normal") not in bad


# ---------------------------------------------------------------- protection
def test_iec_curves():
    assert float(iec_time(10, 1, 1, "SI")) == pytest.approx(0.14 / (10 ** 0.02 - 1), rel=1e-9)
    assert float(iec_time(10, 1, 1, "VI")) == pytest.approx(1.5, rel=1e-9)
    assert float(iec_time(10, 1, 1, "EI")) == pytest.approx(80 / 99, rel=1e-9)
    assert math.isinf(float(iec_time(0.9, 1, 1, "SI")))


def test_mv_grading_margins(res):
    for k, m in res["devices"]["margins_mv"].items():
        assert m["min_margin_s"] >= 0.3 - 1e-9, k


def test_transformer_protection(res):
    rtx = res["devices"]["rtx"]
    i_withstand = 2.5e6 / (math.sqrt(3) * 20e3) / 0.06
    assert float(rtx.clear(i_withstand)) < 2.0
    assert 12 * 2.5e6 / (math.sqrt(3) * 20e3) < rtx.i50        # inrush below high-set


def test_lv_acb_tiers_time_selective(res):
    sel = {(r["downstream"][:6], r["upstream"][:6]): r for r in res["lv_sel"]}
    assert all(r["selective"] for k, r in sel.items() if not k[0].startswith("Rack"))
    rack = [r for k, r in sel.items() if k[0].startswith("Rack")][0]
    assert rack["current_limit_ka"] == pytest.approx(8.64, rel=1e-3)


def test_genset_and_ups_sensitivity(res):
    assert all(r["trips"] for r in res["genset"]["rows"])
    assert res["ups"]["mcb_inst_ok"]
    assert all(r["ik1_ka"] > 10 * 63 / 1000 for r in res["ik1_rack"])


def test_ct_checks(res):
    assert all(r["OK"] for r in res["ct"])


# ---------------------------------------------------------------- arc flash (IEEE 1584-2018 Annex D validation)
def test_annex_d2_via_wrapper():
    enc = AF.Enclosure("D.2", 0.48, "VCB", 32, 609.6, 610, 610, 254)
    r = AF.ieee1584(enc, 45.0, lambda ia: 0.0613 if ia > 27 else 0.319)
    full = [c for c in r["cases"] if c["variant"] == "full"][0]
    red = [c for c in r["cases"] if c["variant"] == "reduced"][0]
    assert full["iarc_ka"] == pytest.approx(28.793, abs=1e-3)
    assert full["e_jcm2"] == pytest.approx(11.585, abs=1e-3)
    assert full["afb_mm"] == pytest.approx(1029, abs=1)
    assert red["iarc_ka"] == pytest.approx(25.244, abs=1e-3)
    assert red["e_jcm2"] == pytest.approx(53.156, abs=1e-3)
    assert r["e_jcm2"] == red["e_jcm2"]


def test_annex_d1_via_wrapper():
    enc = AF.Enclosure("D.1", 4.16, "VCB", 104, 914.4, 1143, 762, 508)
    r = AF.ieee1584(enc, 15.0, lambda ia: 0.197 if ia > 12.8 else 0.223)
    full = [c for c in r["cases"] if c["variant"] == "full"][0]
    assert full["iarc_ka"] == pytest.approx(12.979, abs=1e-3)
    assert full["e_jcm2"] == pytest.approx(12.152, abs=1e-3)
    red = [c for c in r["cases"] if c["variant"] == "reduced"][0]
    assert red["e_jcm2"] == pytest.approx(13.343, abs=1e-3)


def test_lee_and_ppe():
    r = AF.lee(20, 10, 0.1, 910)
    assert r["e_jcm2"] == pytest.approx(2.142e6 * 20 * 10 * 0.1 / 910 ** 2, rel=1e-9)
    assert AF.ppe_category(3.0).startswith("PPE 1") and AF.ppe_category(50).startswith("> 40")


def test_mitigation_reduces_energy(res):
    base = {r["location"]: r["e_cal"] for r in res["arc"] if r["case"].startswith("Base")}
    for r in res["arc"]:
        if not r["case"].startswith("Base"):
            assert r["e_cal"] < base[r["location"]]


# ---------------------------------------------------------------- earthing
def test_earthing():
    e = E.compare()
    assert 15 < e["ic_a"] < 30
    assert e["compensated"]["if_a"] < 15 and e["low_resistance"]["if_a"] > 490
    assert e["compensated"]["rf_detect_ohm"] > 20 * e["low_resistance"]["rf_detect_ohm"]
    assert E.utp(0.5) == pytest.approx(220) and E.utp(10) == pytest.approx(85)
