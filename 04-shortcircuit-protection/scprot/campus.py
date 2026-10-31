"""Campus network model (from DWU-DC-E-DB-001 §8.1, project-02 ratings and TODO_final_fixes rating changes)
and the short-circuit scenarios of the study."""
import math
import os
import sys
from dataclasses import dataclass, asdict, field

from .iec60909 import (Network, z_network_feeder, z_transformer, z_generator, GenDecrement, C_MAX, C_MIN)

# re-use project-02 conductor data
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "03-load-sizing"))
from dcsizing.tables import R20_CU, R20_AL, ALPHA20, X_CABLE_OHM_PER_KM, BUSWAY_Z, BUSWAY_ICW_KA  # noqa: E402


@dataclass
class Data:
    # 130 kV grid (DB §8.1, assumed)
    sk_max_mva: float = 3000.0
    sk_min_mva: float = 1500.0          # one 130 kV line out / weak grid
    grid_r_x: float = 0.1
    # T1/T2
    hv_sr_mva: float = 63.0
    hv_ur_hv: float = 130.0
    hv_ur_lv: float = 21.0
    hv_uk: float = 0.12
    hv_pk_kw: float = 250.0
    # 20 kV cables
    feeder_km: float = 0.6               # 3×1×240 Al per hall feeder
    feeder_r20: float = 0.125
    feeder_x: float = 0.11
    tx_cable_km: float = 0.15            # 3×1×95 Al hall board → block transformer
    tx_cable_r20: float = 0.320
    tx_cable_x: float = 0.13
    # block transformer (project 03: Pk 19 kW)
    bt_sr_mva: float = 2.5
    bt_ur_hv: float = 20.0
    bt_ur_lv: float = 0.42
    bt_uk: float = 0.06
    bt_pk_kw: float = 19.0
    # genset (DB §8.1)
    gen_sr_mva: float = 2.75
    gen_ur_kv: float = 0.4
    gen_xd2: float = 0.15
    gen_xd1: float = 0.22
    gen_x0: float = 0.08
    # LV connections (TODO B4/B5: busbar trunking)
    tx_msb_busduct_m: float = 10.0       # 4000 A
    gen_msb_busduct_m: float = 40.0      # 4000 A (rating change B5)
    msb_sbs_busduct_m: float = 25.0      # 3200 A (rating change B4)
    sbs_z_mohm: complex = complex(0.05, 0.02)   # static switch + MBB/UOSB busbars [ASSUMED]
    uosb_feeder_m: float = 30.0          # 2 × 3×1×185 Cu (project 03 C4)
    uosb_feeder_size: float = 185
    uosb_feeder_par: int = 2
    busway_a: int = 800
    busway_m: float = 60.0
    rack_cable_m: float = 8.0            # 4G16 Cu (project 03 C5)
    rack_cable_size: float = 16
    # UPS (per block 2 × 1000 kW)
    ups_kw: float = 2000.0
    ups_ik_pu: float = 2.0               # inverter current limit, × rated, ≈ 100 ms [ASSUMED]
    # temperatures for min. short circuit (IEC 60909-0 §7.1.2), end-of-fault conductor temperature
    theta_e_c: float = 80.0

    def as_dict(self):
        d = asdict(self); d["sbs_z_mohm"] = str(self.sbs_z_mohm); return d


def _cable(length_m, size, mat="Cu", n=1, case="max", theta_e=80.0, x_ohm_km=X_CABLE_OHM_PER_KM):
    r20 = (R20_CU if mat == "Cu" else R20_AL)[size]
    r = r20 * (1 + ALPHA20[mat] * (theta_e - 20)) if case == "min" else r20
    return complex(r, x_ohm_km) * length_m / 1000.0 / n


def _busway(rating, length_m, case="max", theta_e=80.0):
    r_op, x = BUSWAY_Z[rating]          # mΩ/m at operating temperature
    r20 = r_op / (1 + 0.00393 * (90 - 20)) * 1.0   # back to 20 °C [ASSUMED operating 90 °C basis]
    r = r20 * (1 + 0.00393 * (theta_e - 20)) if case == "min" else r20
    return complex(r, x) * length_m / 1000.0


def _mv_cable(km, r20, x, case="max", theta_e=80.0):
    r = r20 * (1 + 0.00403 * (theta_e - 20)) if case == "min" else r20
    return complex(r, x) * km


@dataclass
class Scenario:
    key: str
    title: str
    case: str = "max"              # "max" | "min"
    grid: bool = True
    t1: bool = True
    t2: bool = True
    mv_coupler: bool = False       # MSG-20 coupler
    hall_coupler: bool = False     # HV-DH1 coupler
    block_b_out: bool = False
    feeder_dh1_a_out: bool = False
    genset: bool = False
    note: str = ""


SCENARIOS = [
    Scenario("S0max", "Normal: one HV transformer per 20 kV section (coupler open) — max", "max"),
    Scenario("S0min", "Normal — min (S''kQ 1 500 MVA, c_min, θe 80 °C)", "min"),
    Scenario("S1", "T1 // T2 in parallel (coupler closed, both incomers) — NOT allowed", "max", mv_coupler=True,
             note="interlocked out in operation"),
    Scenario("S2", "One HV transformer feeds both sections (T2 out, coupler closed)", "max", t2=False, mv_coupler=True),
    Scenario("S3", "Momentary closed-transition: MV coupler make-before-break (= S1) + LV grid/genset retransfer",
             "max", mv_coupler=True, genset=True, note="≤ 100–200 ms window"),
    Scenario("S4", "Genset island (grid lost, MSB on genset)", "max", grid=False, genset=True),
    Scenario("S4min", "Genset island — min (c_min, θe 80 °C)", "min", grid=False, genset=True),
    Scenario("S5", "N-1: block B out + hall feeder DH1-A out (hall coupler closed)", "max",
             block_b_out=True, feeder_dh1_a_out=True, hall_coupler=True),
    Scenario("S5b", "Hall coupler closed with BOTH hall feeders in service (T1 // T2 via the hall board)", "max",
             hall_coupler=True, note="must be interlocked out"),
]

FAULT_NODES = ["HV130", "MV-A", "DH1-S1", "TA-HV", "MSB-A", "UOSB-A", "BW-A1-0", "BW-A1-END", "RACK"]
NODE_LABEL = {"HV130": "130 kV bus", "MV-A": "MSG-20 sect. A (20 kV)", "DH1-S1": "HV-DH1 sect. 1 (20 kV)",
              "TA-HV": "T-A HV terminals (20 kV)", "MSB-A": "MSB-A (400 V)", "UOSB-A": "UOSB-A on bypass (400 V)",
              "BW-A1-0": "Busway A1 start (400 V)", "BW-A1-END": "Busway A1 end, 60 m (400 V)",
              "RACK": "Rack PDU inlet, 8 m 4G16 (400 V)"}


def build(sc: Scenario, d: Data = None) -> Network:
    d = d or Data()
    net = Network()
    case, th = sc.case, d.theta_e_c
    cq = C_MAX["HV"] if case == "max" else C_MIN["HV"]
    for n, u in [("HV130", 130.0), ("MV-A", 20.0), ("MV-B", 20.0), ("DH1-S1", 20.0), ("DH1-S2", 20.0),
                 ("TA-HV", 20.0), ("TB-HV", 20.0), ("TC-HV", 20.0), ("TD-HV", 20.0),
                 ("MSB-A", 0.4), ("MSB-B", 0.4), ("MSB-C", 0.4), ("MSB-D", 0.4), ("GEN-A", 0.4),
                 ("UOSB-A", 0.4), ("BW-A1-0", 0.4), ("BW-A1-END", 0.4), ("RACK", 0.4)]:
        net.add_node(n, u)
    # other halls: feeder ends only (no effect on I''k, kept for completeness of the model)
    for h in range(2, 7):
        net.add_node(f"DH{h}-S1", 20.0); net.add_node(f"DH{h}-S2", 20.0)
    sk = d.sk_max_mva if case == "max" else d.sk_min_mva
    if sc.grid:
        net.add_shunt("Grid 130 kV", "HV130", z_network_feeder(sk, 130.0, cq, d.grid_r_x))
    zt_hv = z_transformer(d.hv_sr_mva, d.hv_ur_lv, d.hv_uk, d.hv_pk_kw, kt=True, cmax=1.1)  # on 21 kV side
    t_hv = d.hv_ur_hv / d.hv_ur_lv
    net.add_branch("T1", "HV130", "MV-A", zt_hv, t_hv, closed=sc.t1 and sc.grid)
    net.add_branch("T2", "HV130", "MV-B", zt_hv, t_hv, closed=sc.t2 and sc.grid)
    net.add_branch("MSG coupler", "MV-A", "MV-B", complex(1e-6, 1e-6), closed=sc.mv_coupler)
    zf = _mv_cable(d.feeder_km, d.feeder_r20, d.feeder_x, case, th)
    net.add_branch("F-DH1-A", "MV-A", "DH1-S1", zf, closed=not sc.feeder_dh1_a_out)
    net.add_branch("F-DH1-B", "MV-B", "DH1-S2", zf)
    for h in range(2, 7):
        net.add_branch(f"F-DH{h}-A", "MV-A", f"DH{h}-S1", zf); net.add_branch(f"F-DH{h}-B", "MV-B", f"DH{h}-S2", zf)
    net.add_branch("HV-DH1 coupler", "DH1-S1", "DH1-S2", complex(1e-6, 1e-6), closed=sc.hall_coupler)
    zc = _mv_cable(d.tx_cable_km, d.tx_cable_r20, d.tx_cable_x, case, th)
    zt_b = z_transformer(d.bt_sr_mva, d.bt_ur_lv, d.bt_uk, d.bt_pk_kw, kt=True, cmax=1.05)
    t_b = d.bt_ur_hv / d.bt_ur_lv
    for blk, sec in (("A", "DH1-S1"), ("C", "DH1-S1"), ("B", "DH1-S2"), ("D", "DH1-S2")):
        out = sc.block_b_out and blk == "B"
        net.add_branch(f"C-T{blk}", sec, f"T{blk}-HV", zc, closed=not out)
        net.add_branch(f"T-{blk}", f"T{blk}-HV", f"MSB-{blk}", zt_b + _busway(4000, d.tx_msb_busduct_m, case, th),
                       t_b, closed=not out and sc.grid)
    # genset A on MSB-A via 4000 A busduct
    zg = z_generator(d.gen_sr_mva, d.gen_ur_kv, d.gen_xd2, 0.4)
    ir_g = d.gen_sr_mva / (math.sqrt(3) * d.gen_ur_kv)
    net.add_shunt("Genset A", "GEN-A", zg, kind="generator", ir_ka=ir_g, on=sc.genset)
    net.add_branch("Gen busduct", "GEN-A", "MSB-A", _busway(4000, d.gen_msb_busduct_m, case, th))
    # bypass path MSB-A → SBS → UOSB-A
    net.add_branch("SBS path", "MSB-A", "UOSB-A", _busway(3200, d.msb_sbs_busduct_m, case, th) + d.sbs_z_mohm / 1000)
    net.add_branch("UOSB→BW feeder", "UOSB-A", "BW-A1-0",
                   _cable(d.uosb_feeder_m, d.uosb_feeder_size, "Cu", d.uosb_feeder_par, case, th))
    net.add_branch("Busway A1", "BW-A1-0", "BW-A1-END", _busway(d.busway_a, d.busway_m, case, th))
    net.add_branch("Rack cable", "BW-A1-END", "RACK", _cable(d.rack_cable_m, d.rack_cable_size, "Cu", 1, case, th))
    return net


def run_scenario(sc: Scenario, d: Data = None, tk_s: float = 1.0) -> dict:
    d = d or Data()
    net = build(sc, d)
    dec = GenDecrement(d.gen_xd2, d.gen_xd1)
    res = {}
    for n in FAULT_NODES:
        r = net.fault(n, case=sc.case, tk_s=tk_s, gen_decrement=dec)
        res[n] = r
    return {"scenario": sc, "net": net, "faults": res}


def run_all(d: Data = None) -> dict:
    return {s.key: run_scenario(s, d) for s in SCENARIOS}


# ------------------------------------------------------------------ UPS inverter-only fault level
def ups_inverter_ik_ka(d: Data = None) -> float:
    d = d or Data()
    return d.ups_ik_pu * d.ups_kw / (math.sqrt(3) * 0.4) / 1000


# ------------------------------------------------------------------ single-phase (L-PE) minimum fault, TN-S
def ik1_min_rack(d: Data = None, source: str = "grid") -> dict:
    """Minimum line-to-PE fault current at the rack PDU inlet, for disconnection (IEC 60364-4-41) and
    MCB magnetic pick-up checks.  Ik1 = c·√3·Un / |2Z1 + Z0| with Z1/Z0 of the source and
    3·(Z_L + Z_PE) of each downstream conductor path (PE same section as phase for cables;
    busway PE = enclosure, Z_PE ≈ Z_L [ASSUMED])."""
    d = d or Data()
    c, un = C_MIN["LV"], 0.4
    sc = SCENARIOS[1] if source == "grid" else SCENARIOS[6]
    net = build(sc, d)
    z1 = net.fault("MSB-A", case="min")["zk"]
    if source == "grid":
        zt = z_transformer(d.bt_sr_mva, d.bt_ur_lv, d.bt_uk, d.bt_pk_kw, kt=True, cmax=1.05)
        z0 = 0.95 * zt + _busway(4000, d.tx_msb_busduct_m, "min") * 3
    else:
        zg0 = complex(0.15 * d.gen_x0, d.gen_x0) * d.gen_ur_kv ** 2 / d.gen_sr_mva
        z0 = zg0 + _busway(4000, d.gen_msb_busduct_m, "min") * 3
    loop = (_busway(3200, d.msb_sbs_busduct_m, "min") * 2 + d.sbs_z_mohm / 1000 * 2
            + _cable(d.uosb_feeder_m, d.uosb_feeder_size, "Cu", d.uosb_feeder_par, "min") * 2
            + _busway(d.busway_a, d.busway_m, "min") * 2
            + _cable(d.rack_cable_m, d.rack_cable_size, "Cu", 1, "min") * 2)
    ik1 = c * math.sqrt(3) * un / abs(2 * z1 + z0 + 3 * loop)
    return {"ik1_ka": ik1, "source": source}
