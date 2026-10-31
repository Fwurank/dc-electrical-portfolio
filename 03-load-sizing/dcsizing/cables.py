"""LV cable sizing per IEC 60364-5-52 (current-carrying capacity, correction factors, voltage drop)
and IEC 60364-4-43 (overload coordination, short-circuit withstand k²S² ≥ I²t)."""
import math
from dataclasses import dataclass, field
from .tables import (IZ_TABLES, K_AMBIENT_AIR_XLPE, K_GROUP_TRAY_MULTI, K_GROUP_TRAY_TREFOIL, K_SC,
                     R20_CU, R20_AL, ALPHA20, X_CABLE_OHM_PER_KM, STD_PROTECTIVE_DEVICE_A)
from .util import interp, step_lookup, next_std


def r_ohm_per_km(size: float, material: str = "Cu", temp_c: float = 90.0) -> float:
    r20 = (R20_CU if material == "Cu" else R20_AL)[size]
    return r20 * (1 + ALPHA20[material] * (temp_c - 20))


def k_ambient(t_c: float) -> float:
    """IEC 60364-5-52 Table B.52.14 (XLPE, in air)."""
    return interp(K_AMBIENT_AIR_XLPE, t_c)


def k_group(n_circuits: int, method: str) -> float:
    """Grouping factor: Table B.52.21 (single-core trefoil on perforated tray) or B.52.17 item 4
    (multicore single layer on perforated tray)."""
    tbl = K_GROUP_TRAY_TREFOIL if method.startswith("F") else K_GROUP_TRAY_MULTI
    return step_lookup(tbl, n_circuits)


def voltage_drop_pct(i_a: float, length_m: float, size: float, material: str, n_par: int = 1,
                     cosphi: float = 0.95, u_v: float = 400.0, temp_c: float = 90.0) -> float:
    """Three-phase voltage drop, IEC 60364-5-52 Annex G:  ΔU = √3·I·L·(R cosφ + X sinφ)."""
    r = r_ohm_per_km(size, material, temp_c) / 1000.0
    x = X_CABLE_OHM_PER_KM / 1000.0
    sinphi = math.sqrt(1 - cosphi ** 2)
    du = math.sqrt(3) * i_a * length_m * (r * cosphi + x * sinphi) / n_par
    return du / u_v * 100.0


def min_size_short_circuit(ik_ka: float, t_s: float, material: str = "Cu", insulation: str = "XLPE") -> float:
    """IEC 60364-4-43 §434.5.2:  t ≤ (k·S/I)²  →  S ≥ I·√t / k  (adiabatic, t ≤ 5 s)."""
    return ik_ka * 1000.0 * math.sqrt(t_s) / K_SC[(material, insulation)]


@dataclass
class CableResult:
    ok: bool
    size_mm2: float = None
    n_parallel: int = None
    material: str = None
    method: str = None
    ib_a: float = None
    in_a: float = None
    iz_a: float = None
    i0_a: float = None
    k_amb: float = None
    k_grp: float = None
    vd_pct: float = None
    s_min_sc_mm2: float = None
    notes: list = field(default_factory=list)

    def label(self):
        if not self.ok:
            return "no solution"
        core = "3×1×" if self.method.startswith("F") else "4G" if self.size_mm2 < 25 else "3×"
        return f"{self.n_parallel} × {core}{self.size_mm2:g} mm² {self.material} XLPE" if self.n_parallel > 1 \
            else f"{core}{self.size_mm2:g} mm² {self.material} XLPE"


def size_cable(ib_a: float, length_m: float, material: str = "Cu", method: str = "F_trefoil",
               ambient_c: float = 30.0, other_circuits: int = 0, cosphi: float = 0.95, vd_limit_pct: float = 2.0,
               ik_ka: float = 0.0, t_clear_s: float = 0.1, in_a: float = None, max_parallel: int = 12,
               max_size: float = 240, u_v: float = 400.0) -> CableResult:
    """Smallest conductor cross-section (minimum total copper/aluminium) satisfying
      1. Ib ≤ In ≤ Iz  with Iz = n·I0·k_amb·k_group                   (IEC 60364-4-43 §433.1)
         (I2 ≤ 1.45·Iz is satisfied by IEC 60947-2 / 60898 devices, I2 ≤ 1.3 In)
      2. ΔU ≤ limit                                                  (IEC 60364-5-52 §525, Annex G)
      3. S ≥ Ik·√t / k per conductor (conservative: full Ik on one conductor) (IEC 60364-4-43 §434.5.2)
    Parallel conductors: equal size/length/route required (IEC 60364-5-52 §523.7).
    Selection: fewest parallel runs, then smallest section, sections ≤ max_size (240 mm² practical
    termination limit for LV ACB/MCCB terminals) [ASSUMED practice].
    """
    table = IZ_TABLES[(material, method)]
    in_a = in_a or next_std(ib_a, STD_PROTECTIVE_DEVICE_A)
    ka = k_ambient(ambient_c)
    s_sc = min_size_short_circuit(ik_ka, t_clear_s, material) if ik_ka else 0.0
    best = None
    for n in range(1, max_parallel + 1):
        kg = k_group(n + other_circuits, method)
        for s in sorted(table):
            if s > max_size or s < s_sc:
                continue
            if n > 1 and s < 50:      # parallel cables only for large sections (practice) [ASSUMED]
                continue
            iz = n * table[s] * ka * kg
            if iz < in_a:
                continue
            vd = voltage_drop_pct(ib_a, length_m, s, material, n, cosphi, u_v)
            if vd > vd_limit_pct:
                continue
            cand = CableResult(True, s, n, material, method, ib_a, in_a, iz, table[s], ka, kg, vd, s_sc)
            best = cand          # fewest parallel runs first, then smallest section
            break
        if best is not None:
            break
    if best is None:
        return CableResult(False, ib_a=ib_a, in_a=in_a, k_amb=ka, s_min_sc_mm2=s_sc,
                           material=material, method=method, notes=["no size ≤ max_size / max_parallel"])
    if best.n_parallel > 6:
        best.notes.append("> 6 parallel runs — consider busbar trunking instead of cable")
    return best


def ik_after_cable(ik_up_ka: float, z_up_ohm: complex, size: float, length_m: float, material: str = "Cu",
                   n_par: int = 1, u_v: float = 400.0, c: float = 1.05) -> float:
    """I''k3 at the end of a cable (cable resistance at 20 °C for max. fault current, IEC 60909-0 §5)."""
    r = r_ohm_per_km(size, material, 20.0) / 1000.0 * length_m / n_par
    x = X_CABLE_OHM_PER_KM / 1000.0 * length_m / n_par
    z = z_up_ohm + complex(r, x)
    return c * u_v / 1000.0 / (math.sqrt(3) * abs(z))
