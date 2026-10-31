"""UPS sizing and LFP battery autonomy (IEC 62040-3 terminology).

IEC 62040-3 terms used: rated output active power P_r, classification VFI-SS-111 (double
conversion, sinusoidal output, best dynamic class), stored energy time (backup time) t_s.
"""
import math
from .tables import LFP_TEMP_FACTOR, LFP_DEFAULTS, UPS_MODULE_KW
from .util import interp, i_3ph


def select_ups(failure_load_kw: float, module_kw: float = 1000.0, max_loading: float = 0.90,
               internal_redundant_modules: int = 0) -> dict:
    """Number of parallel modules so that the failure-mode load ≤ max_loading × P_r [ASSUMED policy]."""
    n = max(1, math.ceil(failure_load_kw / (module_kw * max_loading) - 1e-9)) + internal_redundant_modules
    pr = n * module_kw
    return {"modules": n, "module_kw": module_kw, "rating_kw": pr, "loading_failure": failure_load_kw / pr}


def battery_energy_required(p_load_kw: float, t_min: float, temp_c: float = 25.0, eol: float = None,
                            dod: float = None, eta_dc: float = None) -> float:
    """Nameplate energy (kWh) for the stored-energy time at end of life:
    E = P / η_dc · t / (DoD · EoL · k_T)."""
    d = LFP_DEFAULTS
    eol = eol or d["eol"]; dod = dod or d["dod"]; eta = eta_dc or d["eta_dc"]
    kt = interp(LFP_TEMP_FACTOR, temp_c)
    return p_load_kw / eta * (t_min / 60.0) / (dod * eol * kt)


def battery_power_required(p_load_kw: float, c_max: float = None, eol: float = None, eta_dc: float = None,
                           temp_c: float = 25.0) -> float:
    """Nameplate energy (kWh) needed so that the DC discharge power does not exceed c_max × E_EoL."""
    d = LFP_DEFAULTS
    c_max = c_max or d["c_max"]; eol = eol or d["eol"]; eta = eta_dc or d["eta_dc"]
    kt = interp(LFP_TEMP_FACTOR, temp_c)
    return p_load_kw / eta / (c_max * eol * kt)


def size_battery(p_load_kw: float, t_min: float, temp_c: float = 25.0, c_max: float = None) -> dict:
    e_energy = battery_energy_required(p_load_kw, t_min, temp_c)
    e_power = battery_power_required(p_load_kw, c_max=c_max, temp_c=temp_c)
    e = max(e_energy, e_power)
    return {"e_energy_kwh": e_energy, "e_power_kwh": e_power, "e_required_kwh": e,
            "governed_by": "C-rate (power)" if e_power > e_energy else "energy (autonomy)"}


def autonomy_min(e_nameplate_kwh: float, p_load_kw: float, temp_c: float = 25.0, eol: float = None,
                 dod: float = None, eta_dc: float = None) -> float:
    d = LFP_DEFAULTS
    eol = eol or d["eol"]; dod = dod or d["dod"]; eta = eta_dc or d["eta_dc"]
    kt = interp(LFP_TEMP_FACTOR, temp_c)
    return e_nameplate_kwh * dod * eol * kt * eta / p_load_kw * 60.0


def c_rate(p_load_kw: float, e_nameplate_kwh: float, eol: float = None, eta_dc: float = None) -> float:
    d = LFP_DEFAULTS
    eol = eol or d["eol"]; eta = eta_dc or d["eta_dc"]
    return p_load_kw / eta / (e_nameplate_kwh * eol)


def input_current(p_out_kw: float, eta: float, recharge_kw: float, u_v: float = 400.0, pf_in: float = 0.99) -> float:
    """Maximum rectifier input current (A): output at P_r plus battery recharge."""
    return i_3ph(p_out_kw / eta + recharge_kw, u_v, pf_in)
