"""Regenerate every figure and result file of Project 04.   python scripts/make_all.py"""
import csv
import json
import math
import os
import sys
import warnings

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
warnings.filterwarnings("ignore")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from scprot import study as S, campus as C, pp_model as P
from scprot.iec60909 import GenDecrement
from scprot.protection import tx_damage_curve, inrush_point

FIG = os.path.join(ROOT, "figures")
RES = os.path.join(ROOT, "results")
os.makedirs(FIG, exist_ok=True); os.makedirs(RES, exist_ok=True)
plt.rcParams.update({"font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9, "legend.fontsize": 7.5,
                     "xtick.labelsize": 8, "ytick.labelsize": 8, "font.family": "DejaVu Sans"})
NOTE = "Conceptual study — generic LV curves, not manufacturer data"


def tcc_axes(ax, xlabel, xlim, ylim=(0.01, 1000)):
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlim(*xlim); ax.set_ylim(*ylim)
    ax.grid(True, which="major", lw=0.6, alpha=0.6); ax.grid(True, which="minor", lw=0.3, alpha=0.3)
    ax.set_xlabel(xlabel); ax.set_ylabel("Time (s)")


def band(ax, dev, i, label, color, scale=1.0, i_max=None):
    if i_max:
        i = i[i <= i_max]
    lo = np.asarray(dev.trip(i), float); hi = np.asarray(dev.clear(i), float)
    lo = np.where(np.isfinite(lo), np.clip(lo, 1e-3, 1e4), np.nan)
    hi = np.where(np.isfinite(hi), np.clip(hi, 1e-3, 1e4), np.nan)
    x = i * scale
    ax.fill_between(x, lo, hi, color=color, alpha=0.25, lw=0)
    ax.plot(x, hi, color=color, lw=1.3, label=label); ax.plot(x, lo, color=color, lw=0.6)


def relay_curve(ax, rel, i, label, scale=1.0, i_max=None):
    if i_max:
        i = i[i <= i_max]
    t = np.asarray(rel.trip(i), float)
    t = np.where(np.isfinite(t), t, np.nan)
    ax.plot(i * scale, t, color=rel.color, lw=1.8, label=label)


def vline(ax, x, txt, color="k", y=0.012, ls="--", left=False):
    ax.axvline(x, color=color, ls=ls, lw=0.8)
    ax.text(x / 1.03 if left else x * 1.03, y, txt, rotation=90, fontsize=7, color=color, va="bottom",
            ha="right" if left else "left")


def fig_ik(res):
    R = res["R"]
    nodes = ["MV-A", "DH1-S1", "TA-HV", "MSB-A", "UOSB-A", "BW-A1-0", "BW-A1-END", "RACK"]
    labels = ["MSG-20", "HV-DH1", "T-A HV", "MSB-A", "UOSB-A\n(bypass)", "Busway\nstart", "Busway\nend", "Rack\nPDU"]
    sc = [("S0max", "S0 normal, max", "#1f4e79"), ("S0min", "S0 normal, min", "#9dc3e6"),
          ("S1", "S1 T1//T2", "#c55a11"), ("S3", "S3 closed transition", "#ff0000"), ("S4", "S4 genset island", "#548235")]
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.3), gridspec_kw={"width_ratios": [3, 5]})
    for ax, sel, rat in ((axes[0], slice(0, 3), [(25, "25 kA switchgear")]),
                         (axes[1], slice(3, 8), [(65, "65 kA MSB/UOSB"), (36, "36 kA busway Icw"), (15, "15 kA MCB Icn")])):
        nn = nodes[sel]; ll = labels[sel]; x = np.arange(len(nn)); w = 0.16
        for k, (key, lab, col) in enumerate(sc):
            v = [R[key]["faults"][n]["ik_ka"] for n in nn]
            if all(vv <= 0 for vv in v):
                continue
            ax.bar(x + (k - 2) * w, v, w, color=col, label=lab)
        for val, txt in rat:
            ax.axhline(val, color="k", ls="--", lw=0.8); ax.text(len(nn) - 0.5, val + 0.8, txt, ha="right", fontsize=7)
        ax.set_xticks(x); ax.set_xticklabels(ll); ax.set_ylabel("Ik'' (kA)"); ax.grid(axis="y", alpha=0.4)
        ax.set_ylim(0, 30 if sel.start == 0 else 105)
    axes[0].set_title("20 kV"); axes[1].set_title("400 V")
    axes[1].legend(loc="upper right", ncol=2, framealpha=0.95, fontsize=7)
    fig.suptitle("Initial symmetrical short-circuit current Ik'' per bus and scenario (IEC 60909-0)", fontsize=10)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig1_ik_levels.png"), dpi=200); plt.close(fig)


def fig_tcc_mv(res):
    dv = res["devices"]; R = res["R"]
    fig, ax = plt.subplots(figsize=(7.4, 4.6))
    i = np.geomspace(50, 30000, 600)
    tcc_axes(ax, "Current at 20 kV (A)", (50, 30000))
    s0 = R["S0max"]["faults"]
    imax = {"rin": s0["MV-A"]["ik_ka"] * 1e3, "rfd": s0["MV-A"]["ik_ka"] * 1e3, "rtx": s0["DH1-S1"]["ik_ka"] * 1e3}
    for k, lab in (("rin", "R-INC incomer 51/50"), ("rfd", "R-FDR hall feeder 51/50"), ("rtx", "R-TX block TX 51/50")):
        r = dv[k]
        relay_curve(ax, r, i, f"{lab}: IEC {r.curve} Is {r.is51:.0f} A TMS {r.tms}, I>> {r.i50:.0f} A/{r.t50} s",
                    i_max=imax[k])
    band(ax, dv["inc"], i / S.LV_MV, "MSB-A incomer ACB (generic LSI) referred to 20 kV", "C1", S.LV_MV,
         i_max=s0["MSB-A"]["ik_ka"] * 1e3)
    ii, tt = tx_damage_curve(2.5, 0.06, 20.0)
    ax.plot(ii, tt, "k-", lw=1.2, label="2.5 MVA TX through-fault withstand (IEC 60076-5, 2 s)")
    ir, tr = inrush_point(2.5, 20.0)
    ax.plot([ir], [tr], "k^", ms=6, label="TX inrush 12×In / 0.1 s")
    s0 = R["S0max"]["faults"]
    vline(ax, s0["MSB-A"]["ik_ka"] * 1e3 * S.LV_MV, "LV fault via TX 1.10 kA", "C1")
    vline(ax, s0["DH1-S1"]["ik_ka"] * 1e3, "HV-DH1 12.1 kA", "C6", y=1.2, left=True)
    vline(ax, s0["MV-A"]["ik_ka"] * 1e3, "MSG-20 13.0 kA", "C7", y=1.2)
    vline(ax, R["S0min"]["faults"]["TA-HV"]["ik_ka"] * 1e3 * 0.87, "min 2ph TA-HV 8.3 kA", "grey", y=0.5)
    m = dv["margins_mv"]
    txt = "\n".join(f"{k}: ≥ {v['min_margin_s']:.2f} s" for k, v in m.items())
    ax.text(0.015, 0.015, "Minimum grading margins (CTI ≥ 0.30 s)\n" + txt, transform=ax.transAxes, fontsize=7.5,
            bbox=dict(fc="white", ec="0.6"), va="bottom")
    ax.legend(loc="upper left", bbox_to_anchor=(0.0, -0.13), ncol=1, fontsize=7.5, framealpha=0.95, title=NOTE, title_fontsize=7, alignment="left")
    ax.set_title("TCC 1 — 20 kV phase-overcurrent grading (IEC 60255-151), S0 normal")
    fig.savefig(os.path.join(FIG, "fig2_tcc_mv.png"), dpi=200, bbox_inches="tight", pad_inches=0.08); plt.close(fig)


def fig_tcc_lv(res):
    dv = res["devices"]; R = res["R"]
    fig, ax = plt.subplots(figsize=(7.4, 4.6))
    i = np.geomspace(40, 150000, 900)
    tcc_axes(ax, "Current at 400 V (A)", (40, 150000))
    s0 = R["S0max"]["faults"]
    band(ax, dv["mcb"], i, "Rack-group 63 A, C-curve (generic IEC 60898-1)", "C3", i_max=s0["BW-A1-END"]["ik_ka"] * 1e3)
    for k, n in (("bw", "BW-A1-0"), ("sbs", "UOSB-A"), ("inc", "MSB-A")):
        d = dv[k]
        lab = f"{d.name}: Ir {d.ir:.0f}, tr {d.tr:g} s, Isd {d.isd:.0f}/{d.tsd} s, Ii {'%.0f' % d.ii if d.ii else 'OFF'}"
        band(ax, d, i, lab, d.color, i_max=s0[n]["ik_ka"] * 1e3)
    relay_curve(ax, dv["rtx"], i * S.LV_MV, "R-TX (20 kV) referred to 400 V", 1 / S.LV_MV, i_max=s0["MSB-A"]["ik_ka"] * 1e3 * S.LV_MV)
    ii, tt = tx_damage_curve(2.5, 0.06, 0.42)
    ax.plot(ii, tt, "k-", lw=1.2, label="2.5 MVA TX withstand (IEC 60076-5)")
    for n, t, col, y in (("RACK", "Rack 14.0 kA", "C3", 0.012), ("BW-A1-END", "Busway end 25.1 kA", "C2", 0.012),
                         ("BW-A1-0", "Busway start 37.1 kA", "C2", 0.3), ("UOSB-A", "UOSB 49.3 kA", "C4", 0.012),
                         ("MSB-A", "MSB 52.3 kA", "C1", 0.3)):
        vline(ax, s0[n]["ik_ka"] * 1e3, t, col, y=y)
    ax.axvspan(36000, 150000, ymin=0, ymax=1, color="red", alpha=0.06)
    ax.text(90000, 3.0, "> busway\nIcw 36 kA", color="red", fontsize=7.5, ha="center")
    ax.text(0.985, 0.985, "MCB/MCCB: current-selective only up to MCCB Ii (8.6 kA);\n"
            "above that, energy selectivity per manufacturer tables.\nACB tiers: time-selective (tsd 0.1/0.2/0.3 s) + ZSI.",
            transform=ax.transAxes, fontsize=7.5, bbox=dict(fc="white", ec="0.6"), va="top", ha="right")
    ax.legend(loc="upper left", bbox_to_anchor=(0.0, -0.13), ncol=1, fontsize=7.5, framealpha=0.95, title=NOTE, title_fontsize=7, alignment="left")
    ax.set_title("TCC 2 — 400 V phase faults, grid supply (UOSB on bypass)")
    fig.savefig(os.path.join(FIG, "fig3_tcc_lv.png"), dpi=200, bbox_inches="tight", pad_inches=0.08); plt.close(fig)


def fig_tcc_gen(res):
    dv = res["devices"]; d = res["data"]
    dec = GenDecrement(d.gen_xd2, d.gen_xd1)
    irg = res["genset"]["ir_gen_a"]
    fig, ax = plt.subplots(figsize=(7.4, 4.2))
    i = np.geomspace(40, 60000, 900)
    tcc_axes(ax, "Current at 400 V (A)", (40, 60000))
    s4 = res["R"]["S4"]["faults"]
    band(ax, dv["mcb"], i, "Rack-group 63 A, C-curve", "C3", i_max=s4["BW-A1-END"]["ik_ka"] * 1e3)
    for k, n in (("bw", "BW-A1-0"), ("sbs", "UOSB-A"), ("gen", "MSB-A")):
        dd = dv[k]
        band(ax, dd, i, f"{dd.name}: Ir {dd.ir:.0f}, Isd {dd.isd:.0f}/{dd.tsd} s", dd.color, i_max=s4[n]["ik_ka"] * 1e3)
    t = np.geomspace(0.01, 10, 200)
    ig = np.array([dec.i_pu(x) for x in t]) * irg * 0.95
    ax.plot(ig, t, color="k", lw=2.2, label="Genset fault-current decrement (MSB fault, x''d 0.15, sustained 3 pu)")
    ups = res["ups"]["ik_inverter_ka"] * 1e3
    ax.plot([ups, ups], [0.01, 0.1], color="m", lw=2.5, label="UPS inverter current limit ≈ 2×In for 0.1 s [ASSUMED]")
    ax.text(0.015, 0.015, f"Genset sustained ≈ {res['genset']['sustained_ka']:.1f} kA\n⇒ genset ACB Isd ≤ 2.5×Ir = 10 kA.\n"
            "UPS on inverter: rack MCB trips\nmagnetically; busway MCCB (Isd 3.2 kA)\n"
            "needs 0.13 s → UPS transfers to bypass.",
            transform=ax.transAxes, fontsize=7.5, bbox=dict(fc="white", ec="0.6"), va="bottom")
    ax.legend(loc="upper left", bbox_to_anchor=(0.0, -0.13), ncol=1, fontsize=7.5, framealpha=0.95, title=NOTE, title_fontsize=7, alignment="left")
    ax.set_title("TCC 3 — genset island (S4) and UPS-inverter-only sources")
    fig.savefig(os.path.join(FIG, "fig4_tcc_genset.png"), dpi=200, bbox_inches="tight", pad_inches=0.08); plt.close(fig)


def fig_arc(res):
    rows = res["arc"]
    fig, ax = plt.subplots(figsize=(7.4, 3.9))
    lab = [f"{r['location'].split(' (')[0]} — {r['case']}" for r in rows]
    e = [r["e_cal"] for r in rows]
    cols = ["#c00000" if r["case"].startswith("Base") else "#2e75b6" for r in rows]
    y = np.arange(len(rows))[::-1]
    ax.barh(y, e, color=cols)
    for yy, v, r in zip(y, e, rows):
        ax.text(v * 1.08, yy, f"{v:.1f}  ({r['t_s']:.2f} s)", va="center", fontsize=7)
    ax.set_yticks(y); ax.set_yticklabels(lab, fontsize=7)
    ax.set_xscale("log"); ax.set_xlim(0.3, 600)
    for k, (v, t) in enumerate(((1.2, "1.2"), (4, "PPE 1"), (8, "PPE 2"), (25, "PPE 3"), (40, "PPE 4"))):
        ax.axvline(v, color="0.3", ls=":", lw=0.8)
        ax.text(v, len(rows) - 0.4 + 0.45 * (k % 2), t, fontsize=6.5, ha="center")
    ax.set_ylim(-0.6, len(rows) + 0.6)
    ax.set_xlabel("Incident energy (cal/cm², log).  Red = base design, blue = mitigated; (clearing time)")
    fig.suptitle("Arc-flash incident energy — IEEE 1584-2018 at 400 V, Lee method at 20 kV (conceptual)", fontsize=10)
    ax.grid(axis="x", which="both", alpha=0.3)
    fig.savefig(os.path.join(FIG, "fig5_arcflash.png"), dpi=200, bbox_inches="tight", pad_inches=0.08); plt.close(fig)


def write_results(res):
    with open(os.path.join(RES, "short_circuit.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(res["sc_table"][0].keys())); w.writeheader()
        for r in res["sc_table"]:
            w.writerow({k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()})
    pp_rows = []
    for lab, kw, key in (("S0max", {}, "S0max"), ("S0min", {"case": "min"}, "S0min"),
                         ("S1", {"parallel_hv": True}, "S1"), ("S4", {"grid": False, "genset": True}, "S4")):
        r = P.ik_pp(**kw)
        for n, v in r.items():
            if n in res["R"][key]["faults"] and not math.isnan(v["ik_ka"]):
                own = res["R"][key]["faults"][n]
                pp_rows.append({"scenario": lab, "node": n, "own_ik_ka": round(own["ik_ka"], 3),
                                "pp_ik_ka": round(v["ik_ka"], 3), "dev_pct": round(100 * (own["ik_ka"] / v["ik_ka"] - 1), 2),
                                "own_ip_ka": round(own["ip_ka"], 2), "pp_ip_ka": round(v["ip_ka"], 2)})
    with open(os.path.join(RES, "pandapower_crosscheck.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(pp_rows[0].keys())); w.writeheader(); w.writerows(pp_rows)

    def clean(o):
        if isinstance(o, dict):
            return {k: clean(v) for k, v in o.items() if k not in ("cases",)}
        if isinstance(o, (list, tuple)):
            return [clean(v) for v in o]
        if isinstance(o, (np.floating, np.bool_)):
            return o.item()
        if isinstance(o, complex):
            return str(o)
        return o
    dv = res["devices"]
    out = {"settings_mv": [dv[k].settings_row() for k in ("rin", "rfd", "rtx")],
           "settings_lv": [dv[k].settings_row() for k in ("inc", "sbs", "bw", "gen")],
           "margins_mv": dv["margins_mv"], "lv_selectivity": res["lv_sel"], "genset": res["genset"],
           "ups": res["ups"], "ct": res["ct"], "ratings": res["ratings"], "arc_flash": res["arc"],
           "earthing": res["earthing"], "earthing_coupler_closed": res["earthing_coupler"], "hv_epr": res["hv_epr"],
           "s1_sensitivity": res["s1_sens"], "ik1_rack": res["ik1_rack"], "data": res["data"].as_dict()}
    with open(os.path.join(RES, "study_results.json"), "w") as f:
        json.dump(clean(out), f, indent=1, ensure_ascii=False)
    return pp_rows


def main():
    res = S.run()
    fig_ik(res); fig_tcc_mv(res); fig_tcc_lv(res); fig_tcc_gen(res); fig_arc(res)
    pp_rows = write_results(res)
    print("figures:", sorted(os.listdir(FIG)))
    print("max |dev| own vs pandapower (max case): %.2f %%" % max(abs(r["dev_pct"]) for r in pp_rows if r["scenario"] != "S0min"))
    return res


if __name__ == "__main__":
    main()
