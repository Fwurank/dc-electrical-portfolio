"""Campus scenario: ties the pure calculation modules together for one set of inputs."""
import math
from dataclasses import dataclass, asdict, field
from . import load as L, transformer as T, generator as G, ups as U, cables as C, busway as B
from .tables import DRY_TX_LOSSES_KW, HV_TX_LOSSES_KW
from .util import i_3ph, next_std

SCHEMES = {
    "DR": "Distributed redundant (n blocks, any n-1 carry the load, e.g. 4N/3)",
    "2N": "2N (n block pairs, each side carries 100 %)",
    "N+1": "N+1 parallel-redundant (n+1 blocks on one common critical bus)",
    "BR": "Block redundant / catcher (n primary blocks + 1 reserve)",
}

# Phase-1 first-pass ratings (DWU-DC-E-DB-001 §8) for comparison
PHASE1 = {
    "ups_rating_kw": 2000, "ups_modules": 2, "battery_kwh_per_module": 120, "tx_it_kva": 2500,
    "gen_it_kva": 2750, "tx_mech_kva": 1600, "gen_mech_kva": 1650, "msb_ka": 65, "msb_a": 4000,
    "uosb_a": 3200, "ups_input_breaker_a": 1600, "busway_run_a": 800, "hv_tx_mva": 63,
    "mv_feeder_a_capacity": 390, "pue_peak": 1.27, "pue_annual": 1.15, "fuel_m3_per_hall": 38,
}

SWBD_KA = [36, 50, 65, 85, 100]
SWBD_A = [1600, 2000, 2500, 3200, 4000, 5000, 6300]


@dataclass
class Inputs:
    it_mw_total: float = 30.0
    n_halls: int = 6
    scheme: str = "DR"
    n_blocks: int = 4
    ambient_design_c: float = 32.0
    altitude_m: float = 150.0
    ppue_mech_peak: float = 0.17
    ppue_mech_free: float = 0.05
    target_pue_peak: float = None          # if set, back-solves ppue_mech_peak
    it_util: float = 0.75
    house_kw_per_hall: float = 100.0
    block_aux_kw: float = 100.0
    ups_module_kw: float = 1000.0
    ups_max_loading: float = 0.90
    battery_min: float = 5.0
    battery_temp_c: float = 25.0
    battery_c_max: float = 8.0
    recharge_frac: float = 0.10
    recharge_frac_on_gen: float = 0.05
    gen_max_loading: float = 0.90
    fuel_hours: float = 24.0
    sk_hv_mva: float = 3000.0
    hv_tx_mva: float = 63.0
    hv_tx_uk: float = 0.12
    tx_uk: float = 0.06
    diversity: float = 1.0
    campus_services_kw: float = 500.0
    largest_chiller_kw: float = 400.0
    rack_kw: float = 25.0
    electrical_room_c: float = 35.0
    whitespace_busway_c: float = 40.0
    runs_per_group: int = 2

    def as_dict(self):
        return asdict(self)


def block_loads(p_hall_kw: float, scheme: str, n: int) -> dict:
    if scheme == "DR":
        if n < 3:
            raise ValueError("distributed redundant needs n ≥ 3 blocks")
        return {"blocks": n, "normal": p_hall_kw / n, "failure": p_hall_kw / (n - 1), "conc_maint": True,
                "pairs": n * (n - 1) // 2}
    if scheme == "2N":
        return {"blocks": 2 * n, "normal": p_hall_kw / (2 * n), "failure": p_hall_kw / n, "conc_maint": True,
                "pairs": n}
    if scheme == "N+1":
        return {"blocks": n + 1, "normal": p_hall_kw / (n + 1), "failure": p_hall_kw / n, "conc_maint": False,
                "pairs": None}
    if scheme == "BR":
        return {"blocks": n + 1, "normal": p_hall_kw / n, "failure": p_hall_kw / n, "conc_maint": True,
                "pairs": None}
    raise ValueError(scheme)


def _pq(p_kw, pf):
    return p_kw, p_kw * math.tan(math.acos(pf))


def run(inp: Inputs = None) -> dict:
    inp = inp or Inputs()
    flags = []

    def flag(item, value, limit, ok, note=""):
        flags.append({"item": item, "value": value, "limit": limit, "ok": bool(ok), "note": note})

    p_hall = inp.it_mw_total * 1000.0 / inp.n_halls
    bl = block_loads(p_hall, inp.scheme, inp.n_blocks)

    # ---------------- UPS & battery
    ups = U.select_ups(bl["failure"], inp.ups_module_kw, inp.ups_max_loading)
    ups["loading_normal"] = bl["normal"] / ups["rating_kw"]
    eff_n = L.ups_efficiency(ups["loading_normal"])
    eff_f = L.ups_efficiency(ups["loading_failure"])
    bat = U.size_battery(inp.ups_module_kw, inp.battery_min, inp.battery_temp_c, inp.battery_c_max)
    bat["autonomy_min_phase1"] = U.autonomy_min(PHASE1["battery_kwh_per_module"], inp.ups_module_kw, inp.battery_temp_c)
    bat["c_rate_phase1"] = U.c_rate(inp.ups_module_kw, PHASE1["battery_kwh_per_module"])
    bat["autonomy_min_at_failure_load"] = U.autonomy_min(bat["e_required_kwh"], ups["loading_failure"] * inp.ups_module_kw,
                                                         inp.battery_temp_c)
    bat["selected_kwh"] = math.ceil(bat["e_required_kwh"] / 5.0) * 5
    ups_in_a = U.input_current(inp.ups_module_kw, L.ups_efficiency(1.0), inp.recharge_frac * inp.ups_module_kw)
    ups["input_current_a"] = ups_in_a
    ups["input_breaker_a"] = next_std(ups_in_a, C.STD_PROTECTIVE_DEVICE_A)
    ups["eff_normal"], ups["eff_failure"] = eff_n, eff_f
    flag("UPS loading, failure mode", ups["loading_failure"], inp.ups_max_loading, ups["loading_failure"] <= inp.ups_max_loading)
    flag("UPS rectifier input breaker (P_r + recharge)", ups_in_a, PHASE1["ups_input_breaker_a"],
         ups_in_a <= PHASE1["ups_input_breaker_a"], "phase-1 breaker vs. computed max input current")
    flag("Battery nameplate vs phase-1 120 kWh/module", bat["e_required_kwh"], PHASE1["battery_kwh_per_module"],
         bat["e_required_kwh"] <= PHASE1["battery_kwh_per_module"], f"governed by {bat['governed_by']}")

    # ---------------- block transformer
    def ups_input(p_it, eff, recharge_frac):
        return p_it / eff + recharge_frac * ups["rating_kw"]
    pn, qn = _pq(ups_input(bl["normal"], eff_n, inp.recharge_frac), 0.99)
    pf_, qf_ = _pq(ups_input(bl["failure"], eff_f, inp.recharge_frac), 0.99)
    pa, qa = _pq(inp.block_aux_kw, 0.90)
    s_n = math.hypot(pn + pa, qn + qa)
    s_f = math.hypot(pf_ + pa, qf_ + qa)
    tx_kva = T.select_transformer(s_f, s_n)
    if tx_kva is None:
        tx_kva = T.STD_TX_KVA[-1]
        flag("Block transformer selectable", s_f, T.STD_TX_KVA[-1], False, "block too large for one MV/LV transformer — increase n")
    p0, pk = DRY_TX_LOSSES_KW[tx_kva]
    tx = {"kva": tx_kva, "s_normal_kva": s_n, "s_failure_kva": s_f, "loading_normal": s_n / tx_kva,
          "loading_failure": s_f / tx_kva, "losses_normal_kw": T.losses_kw(tx_kva, s_n),
          "losses_failure_kw": T.losses_kw(tx_kva, s_f), "i_rated_a": T.rated_current(tx_kva, 400), "p0_kw": p0, "pk_kw": pk}
    flag("Block transformer loading, failure mode", tx["loading_failure"], 1.0, tx["loading_failure"] <= 1.0)
    flag("Block transformer loading, normal", tx["loading_normal"], 0.80, tx["loading_normal"] <= 0.80)

    # ---------------- short circuit
    ik_mv = T.ik3_mv(inp.sk_hv_mva, inp.hv_tx_mva, inp.hv_tx_uk, HV_TX_LOSSES_KW.get(inp.hv_tx_mva * 1000, (0, 250))[1])
    sk_mv = math.sqrt(3) * 20.0 * ik_mv
    sc = T.ik3_at_lv_bus(tx_kva, inp.tx_uk, pk, sk_mv)

    # ---------------- genset (IT block)
    pg, qg = _pq(ups_input(bl["failure"], eff_f, inp.recharge_frac_on_gen), 0.99)
    pgn, _ = _pq(ups_input(bl["normal"], eff_n, inp.recharge_frac_on_gen), 0.99)
    gen = G.select_genset(pg + pa, qg + qa, inp.ambient_design_c, inp.altitude_m, inp.gen_max_loading)
    gen["load_failure_kw"] = pg + pa
    gen["load_normal_kw"] = pgn + pa
    if gen["kva"]:
        gen["i_rated_a"] = gen["kva"] * 1000 / (math.sqrt(3) * 400)
        gen["ik_ka"] = T.ik3_generator(gen["kva"], 0.15)
        walk = [inp.block_aux_kw] + [bl["failure"] / eff_f / (ups["modules"] * 4)] * (ups["modules"] * 4)
        gen["steps"] = G.step_load_check(walk, gen["kwe_site"], gen["kva"])
        flag("IT genset kW loading, failure mode", gen["loading_kw"], inp.gen_max_loading, gen["loading_kw"] <= inp.gen_max_loading)
        flag("IT genset load steps (UPS walk-in 25 %/step)", max(s["frac"] for s in gen["steps"]), 0.33,
             all(s["ok"] for s in gen["steps"]))
    else:
        flag("IT genset selectable", pg + pa, None, False, "exceeds largest standard LV genset — increase n")

    msb_a = next_std(max(tx["i_rated_a"], gen.get("i_rated_a", 0)), SWBD_A)
    msb_ka = next_std(sc["ik_ka"], SWBD_KA)
    flag("MSB prospective I''k vs phase-1 65 kA", sc["ik_ka"], 65, sc["ik_ka"] <= 65)
    flag("MSB rated current ≤ 4000 A (practical LV block limit)", max(tx["i_rated_a"], gen.get("i_rated_a", 0)), 4000,
         (msb_a or 99999) <= 4000)
    uosb_a = next_std(i_3ph(ups["rating_kw"], 400, 1.0), SWBD_A)

    # ---------------- hall loads, mechanical, MV feeder
    mech_peak = inp.ppue_mech_peak
    if inp.target_pue_peak:
        mech_peak = L.solve_mech_peak_for_target_pue(inp.target_pue_peak, p_hall, inp.ambient_design_c,
                                                     ups["loading_normal"], inp.house_kw_per_hall)
    mk = {"ppue_free": inp.ppue_mech_free, "ppue_peak": mech_peak}
    recharge_hall = bl["blocks"] * inp.recharge_frac * ups["rating_kw"]
    hall = L.hall_load(p_hall, inp.ambient_design_c, ups["loading_normal"], inp.house_kw_per_hall,
                       recharge_kw=recharge_hall, **mk)
    pm, qm = _pq(hall.mech_kw + inp.house_kw_per_hall, 0.92)
    s_mech_full = math.hypot(pm, qm)
    tx_m = T.select_transformer(s_mech_full, s_mech_full / 2)
    gen_m = G.select_genset(pm, qm, inp.ambient_design_c, inp.altitude_m, inp.gen_max_loading,
                            largest_step_kw=inp.largest_chiller_kw)
    if gen_m["kva"]:
        gen_m["steps"] = G.step_load_check([inp.largest_chiller_kw], gen_m["kwe_site"], gen_m["kva"])
        flag("Mech genset largest step (trim chiller restart)", gen_m["steps"][0]["frac"], 0.33, gen_m["steps"][0]["ok"])
    mech = {"p_kw": pm, "s_kva": s_mech_full, "tx_kva": tx_m,
            "tx_loading_failure": s_mech_full / tx_m if tx_m else None, "gen": gen_m,
            "ppue_mech_peak": mech_peak}
    s_hall_max = hall.max_kw / 0.95
    i_feeder = s_hall_max / (math.sqrt(3) * 20.0)
    flag("Hall 20 kV feeder current (one feeder carries hall)", i_feeder, PHASE1["mv_feeder_a_capacity"],
         i_feeder <= PHASE1["mv_feeder_a_capacity"], "3×1×240 Al 24 kV, in ground ≈ 390 A [ASSUMED]")

    # ---------------- campus
    hv_s_guess = inp.n_halls * hall.total_kw / 0.95
    hv_loss = 2 * (HV_TX_LOSSES_KW[63000][0] + HV_TX_LOSSES_KW[63000][1] * (hv_s_guess / 2 / 63000) ** 2)
    camp = L.campus_demand(hall, inp.n_halls, inp.campus_services_kw, hv_loss, inp.diversity)
    camp_max = L.campus_demand(hall, inp.n_halls, inp.campus_services_kw, hv_loss, inp.diversity, include_recharge=True)
    hv_loading = camp["s_kva"] / (inp.hv_tx_mva * 1000)
    flag("HV transformer N-1 loading (one unit carries campus)", hv_loading, 1.0, hv_loading <= 1.0)
    i_section = camp["s_kva"] / (math.sqrt(3) * 20.0)
    flag("20 kV MSG section current (coupler closed, full campus)", i_section, 2500, i_section <= 2500)
    flag("20 kV I''k (one HV transformer)", ik_mv, 25, ik_mv <= 25)
    ann = L.annual_pue(p_hall, inp.n_halls, ups["loading_normal"], inp.it_util, house_kw=inp.house_kw_per_hall,
                       campus_services_kw=inp.campus_services_kw, hv_tx_kva=inp.hv_tx_mva * 1000, **mk)
    flag("Annualised PUE target ≤ 1.15", ann["pue"], 1.15, ann["pue"] <= 1.15)

    # ---------------- fuel per hall (all gensets at normal share of design-peak load)
    gen_kwe_site = gen.get("kwe_site") or 1
    fuel_lph = bl["blocks"] * G.fuel_rate_lph(gen["load_normal_kw"] if bl["normal"] else 0, gen_kwe_site)
    if gen_m["kva"]:
        fuel_lph += 2 * G.fuel_rate_lph(pm / 2, gen_m["kwe_site"])
    fuel = {"lph_hall": fuel_lph, "tank_m3_hall": fuel_lph * inp.fuel_hours / 0.90 / 1000, "hours": inp.fuel_hours}
    if inp.scheme == "BR":
        fuel["lph_hall"] = inp.n_blocks * G.fuel_rate_lph(gen["load_normal_kw"], gen_kwe_site) + \
            2 * G.fuel_rate_lph(pm / 2, gen_m["kwe_site"] or 1)
        fuel["tank_m3_hall"] = fuel["lph_hall"] * inp.fuel_hours / 0.9 / 1000

    # ---------------- busway runs & cables (reference circuits of one IT block)
    if inp.scheme == "DR":
        run_kw = p_hall / bl["pairs"] / inp.runs_per_group
    else:
        run_kw = bl["failure"] / (3 * inp.runs_per_group)
    run_a = i_3ph(run_kw, 400, 0.98)
    bw_ws = B.select_busway(run_a, 60, inp.whitespace_busway_c, distributed=True, vd_limit_pct=1.0,
                            ik_ka=sc["ik_ka"], in_a=None)
    bw_tx = B.select_busway(tx["i_rated_a"], 10, inp.electrical_room_c, vd_limit_pct=0.5, ik_ka=sc["ik_ka"])
    flag("White-space busway run (survivor mode)", run_a, PHASE1["busway_run_a"], (bw_ws["rating_a"] or 1e9) <= PHASE1["busway_run_a"])
    if not bw_ws.get("sc_ok", True):
        flag("White-space busway Icw vs I''k", bw_ws["icw_ka"], sc["ik_ka"], False,
             "needs current-limiting upstream MCCB (conditional Icc per IEC 61439-6)")

    ik_uosb = sc["ik_ka"]  # on static bypass, ≈ MSB level (conservative)
    rack_a = i_3ph(inp.rack_kw, 400, 0.95)
    circuits = [
        ("C1", "MSB → UPS module rectifier input", dict(ib_a=ups_in_a, length_m=25, material="Cu", method="F_trefoil",
            ambient_c=inp.electrical_room_c, other_circuits=3, vd_limit_pct=1.0, ik_ka=sc["ik_ka"], t_clear_s=0.1,
            in_a=ups["input_breaker_a"])),
        ("C2", "MSB → static bypass input (SBS)", dict(ib_a=i_3ph(ups["rating_kw"], 400, 1.0), length_m=25, material="Cu",
            method="F_trefoil", ambient_c=inp.electrical_room_c, other_circuits=3, vd_limit_pct=1.0, ik_ka=sc["ik_ka"], t_clear_s=0.1)),
        ("C3", "Genset → MSB (generator incomer)", dict(ib_a=gen.get("i_rated_a", 0), length_m=40, material="Cu",
            method="F_trefoil", ambient_c=inp.electrical_room_c, other_circuits=0, vd_limit_pct=1.0,
            ik_ka=gen.get("ik_ka", 0), t_clear_s=0.5)),
        ("C4", "UOSB → white-space busway feeder", dict(ib_a=run_a, length_m=30, material="Cu", method="F_trefoil",
            ambient_c=inp.electrical_room_c, other_circuits=5, vd_limit_pct=1.0, ik_ka=ik_uosb, t_clear_s=0.1,
            in_a=bw_ws["rating_a"])),
        ("C5", "Busway tap-off → rack PDU (63 A)", dict(ib_a=rack_a, length_m=8, material="Cu", method="E_multi",
            ambient_c=inp.whitespace_busway_c, other_circuits=5, vd_limit_pct=1.0, ik_ka=15.0, t_clear_s=0.01, in_a=63)),
        ("C6", "MSB-M → trim chiller", dict(ib_a=i_3ph(inp.largest_chiller_kw, 400, 0.92), length_m=80, material="Al",
            method="F_trefoil", ambient_c=30, other_circuits=3, vd_limit_pct=2.0, ik_ka=40.0, t_clear_s=0.1)),
    ]
    cable_rows = []
    for tag, desc, kw in circuits:
        r = C.size_cable(**kw)
        cable_rows.append({"tag": tag, "circuit": desc, "result": r, "inputs": kw})
        flag(f"Cable {tag} {desc}", r.vd_pct if r.ok else None, kw["vd_limit_pct"], r.ok, "; ".join([r.label()] + r.notes))

    res = {
        "inputs": inp.as_dict(), "p_hall_kw": p_hall, "block": bl, "ups": ups, "battery": bat, "tx": tx,
        "sc": {"ik_mv_ka": ik_mv, "sk_mv_mva": sk_mv, "ik_msb_ka": sc["ik_ka"], "ip_msb_ka": sc["ip_ka"],
               "ik_gen_ka": gen.get("ik_ka")},
        "gen": gen, "msb": {"rating_a": msb_a, "rating_ka": msb_ka}, "uosb_a": uosb_a,
        "hall": hall.as_dict(), "mech": mech, "mv_feeder_a": i_feeder, "s_hall_max_kva": s_hall_max,
        "campus": camp, "campus_max": camp_max, "hv_loading": hv_loading, "i_section_a": i_section,
        "annual": ann, "fuel": fuel, "busway_ws": bw_ws, "busway_tx": bw_tx, "run_a": run_a, "rack_a": rack_a,
        "cables": cable_rows, "flags": flags,
        "installed": {"ups_kw_per_hall": bl["blocks"] * ups["rating_kw"] if inp.scheme != "BR" else (inp.n_blocks + 1) * ups["rating_kw"],
                      "tx_kva_per_hall": bl["blocks"] * tx_kva + 2 * (tx_m or 0),
                      "gens_per_hall": bl["blocks"] + 2},
    }
    res["installed"]["ups_ratio"] = res["installed"]["ups_kw_per_hall"] / p_hall
    flag("Concurrently maintainable distribution (Tier III / EN 50600 Class 3)", None, None, bl["conc_maint"],
         SCHEMES[inp.scheme])
    return res


def rating_changes(res: dict) -> list:
    """Compare computed ratings with phase-1 first-pass ratings."""
    out = []
    def add(item, p1, new, reason, optional=False):
        ch = p1 != new
        kind = "—" if not ch else ("optional (downsize possible)" if optional or (isinstance(new, (int, float)) and new < p1) else "required")
        out.append({"item": item, "phase1": p1, "project02": new, "change": ch, "kind": kind, "reason": reason})
    add("UPS per block (kW)", PHASE1["ups_rating_kw"], res["ups"]["rating_kw"], "N-1 loading ≤ 90 %")
    add("Battery per 1 000 kW module (kWh nameplate)", PHASE1["battery_kwh_per_module"], res["battery"]["selected_kwh"],
        f"governed by {res['battery']['governed_by']} (C-rate ≤ {res['inputs']['battery_c_max']:g}C at EoL)")
    add("UPS rectifier input breaker (A)", PHASE1["ups_input_breaker_a"], res["ups"]["input_breaker_a"],
        f"max input current {res['ups']['input_current_a']:.0f} A at P_r + 10 % recharge")
    add("IT block transformer (kVA)", PHASE1["tx_it_kva"], res["tx"]["kva"], "N-1 ≤ 100 %, normal ≤ 80 %")
    add("IT genset (kVA)", PHASE1["gen_it_kva"], res["gen"]["kva"], "DCC loading ≤ 90 % at 32 °C / 150 m")
    add("Mech transformer (kVA)", PHASE1["tx_mech_kva"], res["mech"]["tx_kva"], "2N, each 100 % of hall mech + house")
    add("Mech genset (kVA)", PHASE1["gen_mech_kva"], res["mech"]["gen"]["kva"], "DCC loading ≤ 90 %")
    add("MSB rating (A)", PHASE1["msb_a"], res["msb"]["rating_a"], "≥ transformer & genset rated current")
    add("MSB short-circuit rating (kA)", PHASE1["msb_ka"], res["msb"]["rating_ka"],
        f"I''k {res['sc']['ik_msb_ka']:.1f} kA (IEC 60909)")
    add("UOSB rating (A)", PHASE1["uosb_a"], res["uosb_a"], "UPS rated output current")
    add("White-space busway run (A)", PHASE1["busway_run_a"], res["busway_ws"]["rating_a"],
        f"survivor current {res['run_a']:.0f} A at 40 °C")
    add("White-space busway feeder protection", "MCCB (not specified)", "current-limiting MCCB, Icc ≥ 55 kA"
        if not res["busway_ws"].get("sc_ok", True) else "MCCB (not specified)",
        f"busway Icw {res['busway_ws'].get('icw_ka')} kA < I''k {res['sc']['ik_msb_ka']:.1f} kA (IEC 61439-6 conditional Icc)")
    for c in res["cables"]:
        r = c["result"]
        if r.ok and r.n_parallel > 6:
            add(f"{c['tag']} {c['circuit']} connection", "cable (not specified)", f"busbar trunking ≥ {r.in_a:.0f} A",
                f"cable would need {r.label()}", optional=False)
    add("Annualised PUE (75 % IT, Dalarna bins)", PHASE1["pue_annual"], round(res["annual"]["pue"], 3),
        "target at risk — see sensitivity: needs mech. pPUE ≤ ~0.035 in free-cooling hours or lower fixed loads")
    add("HV transformer (MVA)", PHASE1["hv_tx_mva"], res["inputs"]["hv_tx_mva"], f"N-1 loading {res['hv_loading']*100:.0f} %")
    add("Fuel storage per hall (m³, 24 h)", PHASE1["fuel_m3_per_hall"], round(res["fuel"]["tank_m3_hall"]),
        "gross volume, 90 % usable, HVO100 SFC")
    return out
