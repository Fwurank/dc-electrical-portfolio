"""The study: short-circuit table, protection settings + coordination checks, rating checks, arc flash,
earthing. `run()` returns one dict that scripts/make_all.py and the report consume."""
import math

import numpy as np

from . import campus as C
from . import earthing as E
from . import arcflash as AF
from .iec60909 import GenDecrement
from .protection import Relay, LSI, MCB, CT, margin, margin_relay, pick_tms

LV_MV = 0.42 / 20.0          # LV amps → MV amps (rated ratio of block transformer)
CTI_MV = 0.30


def sc_table(R):
    rows = []
    for key, rr in R.items():
        for n in C.FAULT_NODES:
            f = rr["faults"][n]
            if f["ik_ka"] <= 0:
                continue
            rows.append({"scenario": key, "node": n, "label": C.NODE_LABEL[n], "ik_ka": f["ik_ka"],
                         "ip_ka": f["ip_ka"], "ib_ka": f["ib_ka"], "ith_ka": f["ith_ka"], "kappa": f["kappa"],
                         "r_x": f["r_x"]})
    return rows


def devices(d: C.Data, R):
    s0 = R["S0max"]["faults"]
    ik_lv_through = s0["MSB-A"]["ik_ka"] * 1e3            # A at 400 V
    # ---------------- LV (generic electronic trip units)
    mcb = MCB("Rack-group 63 A (tap-off), C-curve", 63.0, icn_ka=15.0)
    bw = LSI("Busway feeder MCCB 800 A (current-limiting)", 0.4, 800, 800, tr=6, isd=4 * 800, tsd=0.1,
             ii=12 * 800, icu_ka=70, icw_ka=0, t_open=0.03, color="C2")
    sbs = LSI("MSB→SBS/bypass ACB 3200 A", 0.4, 3200, 2900, tr=1, isd=2.5 * 2900, tsd=0.2, ii=None,
              icu_ka=65, icw_ka=65, color="C4")
    inc = LSI("MSB-A incomer ACB 4000 A", 0.4, 4000, 3600, tr=3, isd=4 * 3600, tsd=0.3, ii=None,
              icu_ka=65, icw_ka=65, color="C1", zsi=True)
    gen = LSI("Genset ACB 4000 A", 0.4, 4000, 4000, tr=12, isd=2.5 * 4000, tsd=0.4, ii=None,
              icu_ka=65, icw_ka=65, color="C5")
    # ---------------- MV relays (20 kV primary amps)
    rtx = Relay("R-TX block transformer (HV-DH1)", 20, 150, 100, 0.5, "EI", i50=1500, t50=0.05, color="C0")
    rfd = Relay("R-FDR hall feeder (MSG-20)", 20, 400, 320, 0.2, "VI", i50=2400, t50=0.35, color="C6")
    rin = Relay("R-INC 20 kV incomer (T1 LV)", 20, 2500, 2100, 0.2, "SI", i50=6000, t50=0.65, color="C7")
    # TMS selection, worst-case current range = max through fault at the downstream device
    lo_lv = inc.ir * 1.05 * (1 + inc.tol_i) * 1.02   # whole range: L pick-up → max through fault
    for k in range(1, 300):          # R-TX vs MSB incomer (relay trip − ACB clear ≥ 0.3 s)
        rtx.tms = round(0.05 * k, 2)
        m_tx = margin(inc, rtx, lo_lv, ik_lv_through, up_scale=LV_MV, n=400)
        if m_tx["min_margin_s"] >= CTI_MV:
            break
    ik_dh = s0["DH1-S1"]["ik_ka"] * 1e3
    _, m_fd = pick_tms(rtx, rfd, rfd.is51 * 1.05, ik_dh, CTI_MV, step=0.01)
    ik_mv = s0["MV-A"]["ik_ka"] * 1e3
    _, m_in = pick_tms(rfd, rin, rin.is51 * 1.05, ik_mv, CTI_MV, step=0.01)
    return {"mcb": mcb, "bw": bw, "sbs": sbs, "inc": inc, "gen": gen, "rtx": rtx, "rfd": rfd, "rin": rin,
            "margins_mv": {"R-TX vs MSB incomer": m_tx, "R-FDR vs R-TX": m_fd, "R-INC vs R-FDR": m_in}}


def lv_selectivity(dv, R):
    s0 = R["S0max"]["faults"]
    out = []
    pairs = [("mcb", "bw", s0["BW-A1-END"]["ik_ka"]), ("bw", "sbs", s0["BW-A1-0"]["ik_ka"]),
             ("sbs", "inc", s0["UOSB-A"]["ik_ka"]), ("inc", None, s0["MSB-A"]["ik_ka"])]
    for dn, up, ik in pairs:
        if up is None:
            continue
        a, b = dv[dn], dv[up]
        m = margin(a, b, 100, ik * 1e3)
        limit = None
        if getattr(b, "ii", None):
            limit = b.ii * (1 - b.tol_i) / 1e3
        out.append({"downstream": a.name, "upstream": b.name, "ik_max_ka": ik, "min_margin_s": m["min_margin_s"],
                    "at_ka": (m["at_a"] or 0) / 1e3,
                    "selective": m["min_margin_s"] > 0,
                    "current_limit_ka": limit})
    return out


def genset_checks(d, dv, R):
    dec = GenDecrement(d.gen_xd2, d.gen_xd1)
    ir = d.gen_sr_mva * 1e3 / (math.sqrt(3) * d.gen_ur_kv)
    s4 = R["S4min"]["faults"]
    rows = []
    for dev_key, node in (("gen", "MSB-A"), ("sbs", "UOSB-A"), ("bw", "BW-A1-END"), ("mcb", "RACK")):
        dvc = dv[dev_key]
        ratio = s4[node]["ik_ka"] / s4["MSB-A"]["ik_ka"]          # share of the generator current
        t_need = getattr(dvc, "tsd", 0.01) if dev_key != "mcb" else 0.01
        i_at_t = dec.i_pu(t_need + 0.05) * ir * ratio * (0.95 / 1.0)
        pick = (dvc.isd * (1 + dvc.tol_i)) if dev_key in ("gen", "sbs") else (
            dvc.ii * (1 + dvc.tol_i) if dev_key == "bw" else 10 * dvc.in_a)
        if dev_key == "bw":
            i_at_t = s4[node]["ik_ka"] * 1e3 * 0.9   # instantaneous: first cycles
            pick_alt = dvc.isd * (1 + dvc.tol_i)
        rows.append({"device": dvc.name, "fault_at": C.NODE_LABEL[node], "ik_initial_ka": s4[node]["ik_ka"],
                     "i_at_trip_ka": i_at_t / 1e3, "pickup_ka": pick / 1e3, "trips": i_at_t >= pick})
    return {"ir_gen_a": ir, "sustained_ka": dec.i_pu(10) * ir / 1e3, "rows": rows}


def ups_checks(d, dv, R):
    ik = C.ups_inverter_ik_ka(d)
    return {"ik_inverter_ka": ik, "limit_s": 0.1,
            "mcb_inst_ok": ik * 1e3 >= 10 * dv["mcb"].in_a,
            "mcb_clear_s": float(dv["mcb"].clear(ik * 1e3 * 0.9)),
            "bw_isd_ok": ik * 1e3 >= dv["bw"].isd * (1 + dv["bw"].tol_i),
            "bw_clear_s": float(dv["bw"].clear(ik * 1e3 * 0.9))}


def ct_checks(R, dv):
    s0, s1 = R["S0max"]["faults"], R["S1"]["faults"]
    cts = [(CT("CT R-INC", 2500, 20, 15, 8.0), s0["MV-A"]["ik_ka"], dv["rin"].i50),
           (CT("CT R-FDR", 400, 20, 15, 2.0), s0["MV-A"]["ik_ka"], dv["rfd"].i50),
           (CT("CT R-TX", 150, 20, 10, 1.5, ith_multiple=167), s0["DH1-S1"]["ik_ka"], dv["rtx"].i50)]
    rows = [ct.check(ik, i50) for ct, ik, i50 in cts]
    # same CTs if T1//T2 were paralleled
    rows_s1 = [ct.check(s1[n]["ik_ka"], i50)["OK"] for (ct, _, i50), n in zip(cts, ["MV-A", "MV-A", "DH1-S1"])]
    for r, ok in zip(rows, rows_s1):
        r["OK if T1//T2"] = ok
    return rows


def rating_checks(R, d):
    g = lambda k, n: R[k]["faults"][n]
    tau = lambda f: f["zk"].imag / (2 * math.pi * 50 * f["zk"].real)
    def asym(f, t_sep=0.045):
        dc = math.exp(-t_sep / tau(f)); return f["ik_ka"] * math.sqrt(1 + 2 * dc * dc), dc
    rated_asym_25 = 25 * math.sqrt(1 + 2 * math.exp(-0.045 / 0.045) ** 2)
    rows = []
    def add(item, rating, rating_ka, case, f, kind="ik", ok_note=""):
        val = f["ip_ka"] if kind == "ip" else f["ik_ka"]
        rows.append({"item": item, "rating": rating, "rating_ka": rating_ka, "case": case,
                     "value_ka": val, "util": val / rating_ka, "ok": val <= rating_ka, "kind": kind, "note": ok_note})
    add("MSG-20 (24 kV)", "Ik 25 kA / 3 s", 25, "S0 normal", g("S0max", "MV-A"))
    add("MSG-20 (24 kV)", "Ip 62.5 kA", 62.5, "S0 normal", g("S0max", "MV-A"), "ip")
    add("MSG-20 (24 kV)", "Ik 25 kA / 3 s", 25, "S1 T1//T2", g("S1", "MV-A"))
    add("MSG-20 (24 kV)", "Ip 62.5 kA", 62.5, "S1 T1//T2", g("S1", "MV-A"), "ip")
    a1, dc1 = asym(g("S1", "MV-A"))
    rows.append({"item": "MSG-20 VCB asym. breaking", "rating": f"{rated_asym_25:.1f} kA (τ 45 ms)",
                 "rating_ka": rated_asym_25, "case": "S1 T1//T2", "value_ka": a1, "util": a1 / rated_asym_25,
                 "ok": a1 <= rated_asym_25, "kind": "asym",
                 "note": f"τ = {tau(g('S1', 'MV-A')) * 1e3:.0f} ms, DC {dc1 * 100:.0f} % at 45 ms"})
    add("HV-DH1 (24 kV)", "Ik 25 kA", 25, "S0 normal", g("S0max", "DH1-S1"))
    add("MSB-A", "Icw 65 kA / 1 s", 65, "S0 normal", g("S0max", "MSB-A"))
    add("MSB-A", "Icm 143 kA", 143, "S0 normal", g("S0max", "MSB-A"), "ip")
    add("MSB-A", "Icw 65 kA / 1 s", 65, "S3 LV closed transition", g("S3", "MSB-A"))
    add("MSB-A", "Icm 143 kA", 143, "S3 LV closed transition", g("S3", "MSB-A"), "ip")
    add("UOSB-A (bypass)", "Icw 65 kA / 1 s", 65, "S0 normal", g("S0max", "UOSB-A"))
    add("Busway 800 A", "Icw 36 kA / 1 s", 36, "S0 normal (start)", g("S0max", "BW-A1-0"),
        ok_note="needs current-limiting MCCB, tested combination")
    add("Tap-off 63 A MCB", "Icn 15 kA (generic MCB)", 15, "S0 normal (busway end)", g("S0max", "BW-A1-END"),
        ok_note="use 63 A MCCB ≥ 36 kA or tested cascade")
    add("Rack PDU inlet", "Icc 10 kA [ASSUMED typ.]", 10, "S0 normal", g("S0max", "RACK"),
        ok_note="needs conditional rating with upstream current-limiting device")
    return rows


def arc_flash(d, dv, R):
    s0 = R["S0max"]["faults"]
    inc, sbs, bw, rtx, rfd, rin = (dv[k] for k in ("inc", "sbs", "bw", "rtx", "rfd", "rin"))
    clr = lambda dev: (lambda ia: float(dev.clear(ia * 1e3)))
    mv_clr = lambda rel: (lambda ia: float(rel.clear(ia * 1e3 * LV_MV)))
    rows = []
    def add(loc, case, r):
        rows.append(dict(r, location=loc, case=case))
    ib = s0["MSB-A"]["ik_ka"]
    add("MSB-A busbar (load side of incomer)", "Base: incomer ST tsd 0.3 s", AF.ieee1584(AF.LV_SWGR, ib, clr(inc)))
    add("MSB-A busbar (load side of incomer)", "ZSI (no restraint → 0.05 s)", AF.ieee1584(AF.LV_SWGR, ib, lambda ia: 0.10))
    add("MSB-A busbar (load side of incomer)", "Maintenance mode (ARMS, inst.)", AF.ieee1584(AF.LV_SWGR, ib, lambda ia: 0.05))
    add("MSB-A busbar (load side of incomer)", "Optical arc relay → ACB", AF.ieee1584(AF.LV_SWGR, ib, lambda ia: 0.055))
    add("MSB-A incomer line side / TX LV", "Base: cleared by R-TX (MV)", AF.ieee1584(AF.LV_SWGR, ib, mv_clr(rtx)))
    add("MSB-A incomer line side / TX LV", "Optical arc relay → MV VCB intertrip",
        AF.ieee1584(AF.LV_SWGR, ib, lambda ia: 0.002 + 0.06 + 0.005))
    add("UOSB-A (on bypass)", "Base: MSB→SBS ACB tsd 0.2 s", AF.ieee1584(AF.LV_SWGR, s0["UOSB-A"]["ik_ka"], clr(sbs)))
    add("UOSB-A (on bypass)", "ZSI / maintenance mode", AF.ieee1584(AF.LV_SWGR, s0["UOSB-A"]["ik_ka"], lambda ia: 0.07))
    add("Busway tap-off box (end)", "Base: busway MCCB", AF.ieee1584(AF.LV_PANEL, s0["BW-A1-END"]["ik_ka"], clr(bw)))
    # 20 kV — Lee
    add("MSG-20 busbar (20 kV)", "Base: R-INC 50 DT 0.65 s", AF.lee(20, s0["MV-A"]["ik_ka"], float(rin.clear(s0["MV-A"]["ik_ka"] * 1e3))))
    add("MSG-20 busbar (20 kV)", "Reverse blocking 0.1 s", AF.lee(20, s0["MV-A"]["ik_ka"], 0.1 + 0.06))
    add("MSG-20 busbar (20 kV)", "Optical arc relay", AF.lee(20, s0["MV-A"]["ik_ka"], 0.07))
    add("HV-DH1 busbar (20 kV)", "Base: R-FDR 50 DT 0.35 s", AF.lee(20, s0["DH1-S1"]["ik_ka"], float(rfd.clear(s0["DH1-S1"]["ik_ka"] * 1e3))))
    add("HV-DH1 busbar (20 kV)", "Optical arc relay", AF.lee(20, s0["DH1-S1"]["ik_ka"], 0.07))
    return rows


def s1_sensitivity(d: C.Data):
    """T1//T2 with a stronger future grid (DSO reinforcement) — why the interlock is kept."""
    out = []
    for sk in (3000, 4000, 5000, 8000):
        dd = C.Data(**{**d.__dict__, "sk_max_mva": sk})
        f = C.run_scenario(next(s for s in C.SCENARIOS if s.key == "S1"), dd)["faults"]["MV-A"]
        f0 = C.run_scenario(C.SCENARIOS[0], dd)["faults"]["MV-A"]
        out.append({"sk_mva": sk, "ik_s1": f["ik_ka"], "ip_s1": f["ip_ka"], "ik_s0": f0["ik_ka"], "ip_s0": f0["ip_ka"]})
    return out


def run(d: C.Data = None) -> dict:
    d = d or C.Data()
    R = C.run_all(d)
    dv = devices(d, R)
    return {"data": d, "R": R, "sc_table": sc_table(R), "devices": dv, "lv_sel": lv_selectivity(dv, R),
            "genset": genset_checks(d, dv, R), "ups": ups_checks(d, dv, R), "ct": ct_checks(R, dv),
            "ratings": rating_checks(R, d), "arc": arc_flash(d, dv, R), "earthing": E.compare(),
            "earthing_coupler": E.compare(coupler_closed=True),
            "hv_epr": [E.hv_earth_fault_epr(t_s=0.1), E.hv_earth_fault_epr(t_s=0.5)],
            "s1_sens": s1_sensitivity(d), "ik1_rack": [C.ik1_min_rack(d, "grid"), C.ik1_min_rack(d, "gen")]}
