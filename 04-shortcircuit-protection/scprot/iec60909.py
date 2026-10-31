"""Generic IEC 60909-0:2016 three-phase short-circuit solver (equivalent voltage source method).

Model: a passive network of nodes (each with nominal voltage Un in kV) connected by branches with an
ideal transformer of ratio t = U_i/U_j (rated ratio, 1 for lines) and a series impedance z (ohm) on the
j side. Sources (network feeders, generators) appear as shunt impedances to the reference (their internal
EMF is replaced by the equivalent voltage source c·Un/√3 at the fault location, IEC 60909-0 §4.3).

Implemented:
  * I''k   eq. (29)   I''k = c·Un / (√3·|Zk|)
  * ip     §8.1.3.2 method C (equivalent frequency fc = 20 Hz), eq. (55) κ = 1.02 + 0.98·e^(−3R/X)
  * Ib     §9.1: far-from-generator Ib = I''k; near-to-generator μ-factor eq. (70) on generator partials
  * Ith    §12 eq. (100)-(102): Ith = I''k·√(m + n)
  * partial branch currents (for relay / breaker currents)
"""
import cmath
import math
from dataclasses import dataclass, field

import numpy as np

F_HZ = 50.0
C_MAX = {"LV": 1.05, "MV": 1.10, "HV": 1.10}   # Table 1 (LV with +6 % tolerance)
C_MIN = {"LV": 0.95, "MV": 1.00, "HV": 1.00}


def level(un_kv: float) -> str:
    return "LV" if un_kv <= 1.0 else ("MV" if un_kv <= 35 else "HV")


@dataclass
class Branch:
    name: str
    i: str
    j: str
    z: complex            # ohm, referred to the j side
    t: float = 1.0        # rated ratio U_i / U_j
    closed: bool = True


@dataclass
class Shunt:
    name: str
    node: str
    z: complex            # ohm at the node's voltage level
    kind: str = "network"  # "network" | "generator"
    ir_ka: float = 0.0     # rated current (generators, for μ)
    on: bool = True


@dataclass
class Network:
    nodes: dict = field(default_factory=dict)        # name -> Un (kV)
    branches: list = field(default_factory=list)
    shunts: list = field(default_factory=list)

    def add_node(self, name, un_kv):
        self.nodes[name] = un_kv

    def add_branch(self, *a, **k):
        self.branches.append(Branch(*a, **k))
        return self.branches[-1]

    def add_shunt(self, *a, **k):
        self.shunts.append(Shunt(*a, **k))
        return self.shunts[-1]

    def branch(self, name) -> Branch:
        return next(b for b in self.branches if b.name == name)

    def shunt(self, name) -> Shunt:
        return next(s for s in self.shunts if s.name == name)

    # ------------------------------------------------------------------ matrices
    def _ybus(self, fc_ratio: float = 1.0):
        """Nodal admittance matrix. fc_ratio = fc/f scales reactances (method C)."""
        idx = {n: k for k, n in enumerate(self.nodes)}
        y = np.zeros((len(idx), len(idx)), dtype=complex)

        def zz(z):
            return complex(z.real, z.imag * fc_ratio)

        for b in self.branches:
            if not b.closed:
                continue
            yb = 1 / zz(b.z)
            i, j = idx[b.i], idx[b.j]
            y[i, i] += yb / b.t ** 2
            y[j, j] += yb
            y[i, j] -= yb / b.t
            y[j, i] -= yb / b.t
        for s in self.shunts:
            if s.on:
                y[idx[s.node], idx[s.node]] += 1 / zz(s.z)
        return y, idx

    def _energised(self):
        """Nodes connected to at least one active source (others are excluded from the solve)."""
        adj = {n: set() for n in self.nodes}
        for b in self.branches:
            if b.closed:
                adj[b.i].add(b.j); adj[b.j].add(b.i)
        seen, stack = set(), [s.node for s in self.shunts if s.on]
        while stack:
            n = stack.pop()
            if n in seen:
                continue
            seen.add(n); stack.extend(adj[n] - seen)
        return seen

    def zbus(self, fc_ratio=1.0):
        live = self._energised()
        sub = Network({n: u for n, u in self.nodes.items() if n in live},
                      [b for b in self.branches if b.i in live and b.j in live],
                      [s for s in self.shunts if s.node in live])
        y, idx = sub._ybus(fc_ratio)
        return np.linalg.inv(y), idx

    # ------------------------------------------------------------------ fault
    def fault(self, node: str, c: float = None, case: str = "max", tk_s: float = 1.0, tmin_s: float = 0.05,
              gen_decrement=None) -> dict:
        """Balanced three-phase fault at `node`. Returns I''k, ip, Ib, Ith (kA), Zk (ohm), R/X and
        partial currents of every branch / shunt (kA, magnitude at the branch's j side / shunt node)."""
        un = self.nodes[node]
        lv = level(un)
        c = c if c is not None else (C_MAX if case == "max" else C_MIN)[lv]
        z, idx = self.zbus()
        if node not in idx:
            return {"node": node, "un_kv": un, "ik_ka": 0.0, "ip_ka": 0.0, "ib_ka": 0.0, "ith_ka": 0.0,
                    "zk": complex("nan"), "r_x": float("nan"), "kappa": float("nan"), "c": c, "partials": {}}
        k = idx[node]
        zk = z[k, k]
        e = c * un / math.sqrt(3)                     # kV
        ik = e / abs(zk)                              # kA
        # partial currents: injected current -If at k → ΔV = -Z[:,k]·If  (kV, kA, ohm)
        i_f = e / zk
        dv = {n: -z[i, k] * i_f for n, i in idx.items()}
        parts = {}
        for b in self.branches:
            if b.closed and b.i in idx and b.j in idx:
                i_j = (dv[b.i] / b.t - dv[b.j]) / b.z     # current i→j on j side, kA
                parts[b.name] = {"i_ka_jside": abs(i_j), "i_ka_iside": abs(i_j) / b.t, "phasor": i_j}
        for s in self.shunts:
            if s.on and s.node in idx:
                i_s = -dv[s.node] / s.z                    # current delivered by source into node
                parts[s.name] = {"i_ka_jside": abs(i_s), "i_ka_iside": abs(i_s), "phasor": i_s, "kind": s.kind}
        # ip, method C
        zc, idx_c = self.zbus(fc_ratio=20.0 / F_HZ)
        zkc = zc[idx_c[node], idx_c[node]]
        r_x = zkc.real / zkc.imag * (20.0 / F_HZ)
        kappa = 1.02 + 0.98 * math.exp(-3 * r_x)
        ip = kappa * math.sqrt(2) * ik
        # Ib: μ on generator partial currents (near-to-generator), eq. (75) simplified (scalar, conservative)
        ib = ik
        gen_parts = [(s, parts[s.name]["i_ka_jside"]) for s in self.shunts if s.on and s.kind == "generator" and s.name in parts]
        for s, ig in gen_parts:
            ib -= (1 - mu_factor(ig / s.ir_ka, tmin_s)) * ig
        # Ith: n = 1 far from generator; generator-only island → n from decrement model
        n = 1.0
        if gen_parts and gen_decrement is not None and len([s for s in self.shunts if s.on]) == len(gen_parts):
            n = gen_decrement.n_factor(ik, tk_s)
        m = m_factor(kappa, tk_s)
        ith = ik * math.sqrt(m + n)
        return {"node": node, "un_kv": un, "c": c, "ik_ka": ik, "ip_ka": ip, "ib_ka": ib, "ith_ka": ith,
                "zk": zk, "r_x": r_x, "kappa": kappa, "m": m, "n": n, "partials": parts}


def mu_factor(ikg_over_irg: float, tmin_s: float) -> float:
    """IEC 60909-0 eq. (70): decay factor μ for the symmetrical breaking current of a generator."""
    x = ikg_over_irg
    if x <= 2.0:
        return 1.0
    if tmin_s <= 0.02:
        mu = 0.84 + 0.26 * math.exp(-0.26 * x)
    elif tmin_s <= 0.05:
        mu = 0.71 + 0.51 * math.exp(-0.30 * x)
    elif tmin_s <= 0.10:
        mu = 0.62 + 0.72 * math.exp(-0.32 * x)
    else:
        mu = 0.56 + 0.94 * math.exp(-0.38 * x)
    return min(mu, 1.0)


def m_factor(kappa: float, tk_s: float, f: float = F_HZ) -> float:
    """IEC 60909-0 eq. (102)/(A.?) heat effect of the DC component:
    m = 1/(2·f·Tk·ln(κ−1)) · [e^(4·f·Tk·ln(κ−1)) − 1]"""
    if kappa <= 1.0 + 1e-9:
        return 0.0
    lk = math.log(kappa - 1)
    return 1 / (2 * f * tk_s * lk) * (math.exp(4 * f * tk_s * lk) - 1)


def kt_factor(xt_pu: float, cmax: float = 1.1) -> float:
    """Network-transformer correction factor, eq. (12a): KT = 0.95·cmax / (1 + 0.6·xT)."""
    return 0.95 * cmax / (1 + 0.6 * xt_pu)


def kg_factor(un_kv: float, urg_kv: float, xd2_pu: float, sin_phi: float = 0.6, cmax: float = 1.05) -> float:
    """Generator correction factor, eq. (18): KG = Un/UrG · cmax / (1 + x''d·sin φrG)."""
    return un_kv / urg_kv * cmax / (1 + xd2_pu * sin_phi)


def z_network_feeder(sk_mva: float, un_kv: float, c: float = 1.1, r_x: float = 0.1, t: float = 1.0) -> complex:
    """Eq. (1)/(4): ZQ = c·UnQ² / S''kQ, referred through ratio t (ZQt = ZQ / t²)."""
    zq = c * un_kv ** 2 / sk_mva / t ** 2
    xq = zq / math.sqrt(1 + r_x ** 2)
    return complex(r_x * xq, xq)


def z_transformer(sr_mva: float, ur_kv: float, uk: float, pkr_kw: float, kt: bool = True, cmax: float = 1.1) -> complex:
    """Eq. (7)-(9) on the side with rated voltage ur_kv, × KT eq. (12a) if kt."""
    zt = uk * ur_kv ** 2 / sr_mva
    rt = pkr_kw / 1000 * ur_kv ** 2 / sr_mva ** 2
    xt = math.sqrt(zt ** 2 - rt ** 2)
    k = kt_factor(xt / (ur_kv ** 2 / sr_mva), cmax) if kt else 1.0
    return complex(rt, xt) * k


def z_generator(sr_mva: float, ur_kv: float, xd2: float, un_kv: float = None, r_over_x: float = 0.15,
                sin_phi: float = 0.6, cmax: float = 1.05) -> complex:
    """Eq. (17)-(18): ZGK = KG·(RG + jX''d); RG = 0.15·X''d for UrG ≤ 1 kV (§6.6.1)."""
    x = xd2 * ur_kv ** 2 / sr_mva
    kg = kg_factor(un_kv or ur_kv, ur_kv, xd2, sin_phi, cmax)
    return complex(r_over_x * x, x) * kg


@dataclass
class GenDecrement:
    """AC short-circuit current decrement of a salient-pole genset with AVR / PMG excitation support
    (classic two-time-constant model). All values per unit of IrG. [ASSUMED vendor-typical]"""
    xd2: float = 0.15
    xd1: float = 0.22
    ik_sust_pu: float = 3.0      # sustained current with PMG excitation support (typ. spec ≥ 300 % for 10 s)
    td2_s: float = 0.015
    td1_s: float = 0.15
    c: float = 1.05

    def i_pu(self, t):
        i2, i1 = self.c / self.xd2, self.c / self.xd1
        return (i2 - i1) * math.exp(-t / self.td2_s) + (i1 - self.ik_sust_pu) * math.exp(-t / self.td1_s) + self.ik_sust_pu

    def n_factor(self, ik_ka_unused, tk_s, steps=2000):
        i0 = self.i_pu(0)
        dt = tk_s / steps
        acc = sum(self.i_pu((k + 0.5) * dt) ** 2 for k in range(steps)) * dt
        return acc / (i0 ** 2 * tk_s)
