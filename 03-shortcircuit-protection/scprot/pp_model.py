"""Independent cross-check of the campus short-circuit levels with pandapower (IEC 60909 implementation
pandapower.shortcircuit.calc_sc). Same data as scprot.campus.Data."""
import math
import warnings

import pandapower as pp
import pandapower.shortcircuit as sc

from .campus import Data, BUSWAY_Z, R20_CU

warnings.filterwarnings("ignore")


def build_pp(d: Data = None, parallel_hv: bool = False, genset: bool = False, grid: bool = True):
    d = d or Data()
    net = pp.create_empty_network(f_hz=50.0)
    b = {}
    for n, u in [("HV130", 130), ("MV-A", 20), ("MV-B", 20), ("DH1-S1", 20), ("TA-HV", 20), ("MSB-A", 0.4),
                 ("GEN-A", 0.4), ("UOSB-A", 0.4), ("BW-A1-0", 0.4), ("BW-A1-END", 0.4), ("RACK", 0.4)]:
        b[n] = pp.create_bus(net, vn_kv=u, name=n)
    if grid:
        pp.create_ext_grid(net, b["HV130"], s_sc_max_mva=d.sk_max_mva, s_sc_min_mva=d.sk_min_mva,
                           rx_max=d.grid_r_x, rx_min=d.grid_r_x)
        vkr_hv = d.hv_pk_kw / (d.hv_sr_mva * 1000) * 100
        for name, lv in (("T1", "MV-A"), ("T2", "MV-B")):
            pp.create_transformer_from_parameters(net, b["HV130"], b[lv], sn_mva=d.hv_sr_mva, vn_hv_kv=d.hv_ur_hv,
                                                  vn_lv_kv=d.hv_ur_lv, vkr_percent=vkr_hv, vk_percent=d.hv_uk * 100,
                                                  pfe_kw=0, i0_percent=0, shift_degree=330, name=name)
        if parallel_hv:
            pp.create_switch(net, b["MV-A"], b["MV-B"], et="b", closed=True, name="coupler")
        pp.create_line_from_parameters(net, b["MV-A"], b["DH1-S1"], d.feeder_km, d.feeder_r20, d.feeder_x, 0, 0.63,
                                       name="F-DH1-A", endtemp_degree=d.theta_e_c)
        pp.create_line_from_parameters(net, b["DH1-S1"], b["TA-HV"], d.tx_cable_km, d.tx_cable_r20, d.tx_cable_x, 0,
                                       0.3, name="C-TA", endtemp_degree=d.theta_e_c)
        # transformer + 10 m 4000 A busduct (busduct modelled as a short line)
        msb_tx = pp.create_bus(net, vn_kv=0.4, name="TA-LV")
        pp.create_transformer_from_parameters(net, b["TA-HV"], msb_tx, sn_mva=d.bt_sr_mva, vn_hv_kv=d.bt_ur_hv,
                                              vn_lv_kv=d.bt_ur_lv, vkr_percent=d.bt_pk_kw / (d.bt_sr_mva * 1000) * 100,
                                              vk_percent=d.bt_uk * 100, pfe_kw=0, i0_percent=0, shift_degree=330, name="T-A")
        _bw(net, msb_tx, b["MSB-A"], 4000, d.tx_msb_busduct_m)
    if genset:
        rdss = 0.15 * d.gen_xd2 * d.gen_ur_kv ** 2 / d.gen_sr_mva
        pp.create_gen(net, b["GEN-A"], p_mw=0, vm_pu=1.0, sn_mva=d.gen_sr_mva, vn_kv=d.gen_ur_kv,
                      xdss_pu=d.gen_xd2, rdss_ohm=rdss, cos_phi=0.8, slack=not grid, name="Genset A")
        _bw(net, b["GEN-A"], b["MSB-A"], 4000, d.gen_msb_busduct_m)
    _bw(net, b["MSB-A"], b["UOSB-A"], 3200, d.msb_sbs_busduct_m, extra=d.sbs_z_mohm)
    r185 = R20_CU[d.uosb_feeder_size]
    pp.create_line_from_parameters(net, b["UOSB-A"], b["BW-A1-0"], d.uosb_feeder_m / 1000, r185 / d.uosb_feeder_par,
                                   0.08 / d.uosb_feeder_par, 0, 1.0, endtemp_degree=d.theta_e_c)
    _bw(net, b["BW-A1-0"], b["BW-A1-END"], d.busway_a, d.busway_m)
    pp.create_line_from_parameters(net, b["BW-A1-END"], b["RACK"], d.rack_cable_m / 1000, R20_CU[d.rack_cable_size],
                                   0.08, 0, 0.1, endtemp_degree=d.theta_e_c)
    return net, b


def _bw(net, f, t, rating, length_m, extra=0j):
    r_op, x = BUSWAY_Z[rating]
    r20 = r_op / (1 + 0.00393 * 70)
    km = length_m / 1000
    r = r20 + extra.real / 1000 / km if km else 0
    xx = x + extra.imag / 1000 / km if km else 0
    return pp.create_line_from_parameters(net, f, t, km, r, xx, 0, rating / 1000, endtemp_degree=80.0)


def ik_pp(case="max", **kw) -> dict:
    net, b = build_pp(**kw)
    sc.calc_sc(net, case=case, lv_tol_percent=6, ip=True, ith=True, kappa_method="C", tk_s=1.0)
    out = {}
    for n, i in b.items():
        out[n] = {"ik_ka": float(net.res_bus_sc.at[i, "ikss_ka"]),
                  "ip_ka": float(net.res_bus_sc.at[i, "ip_ka"]) if "ip_ka" in net.res_bus_sc else float("nan"),
                  "ith_ka": float(net.res_bus_sc.at[i, "ith_ka"]) if "ith_ka" in net.res_bus_sc else float("nan")}
    return out
