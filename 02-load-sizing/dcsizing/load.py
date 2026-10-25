"""IT load → facility load, PUE (design peak & annualised), diversity."""
from dataclasses import dataclass, asdict
from .tables import UPS_EFF_CURVE, CLIMATE_BINS_DALARNA
from .util import interp


def ups_efficiency(load_frac: float) -> float:
    """Double-conversion UPS efficiency vs. load fraction (IEC 62040-3 VFI mode, assumed curve)."""
    return interp(UPS_EFF_CURVE, max(load_frac, 0.10))


def mech_ppue(t_amb_c: float, ppue_free: float = 0.05, ppue_peak: float = 0.17,
              t_free_c: float = 12.0, t_peak_c: float = 32.0) -> float:
    """Mechanical partial PUE (cooling kW per IT kW) vs. outdoor dry bulb.

    Full free cooling (dry coolers) below t_free_c; linear rise to the design-peak value at
    t_peak_c (trim chillers); linear extrapolation above. [ASSUMED model]
    """
    if t_amb_c <= t_free_c:
        return ppue_free
    slope = (ppue_peak - ppue_free) / (t_peak_c - t_free_c)
    return ppue_free + slope * (t_amb_c - t_free_c)


@dataclass
class HallLoad:
    it_kw: float
    ups_loss_kw: float
    mech_kw: float
    dist_loss_kw: float
    house_kw: float
    recharge_kw: float = 0.0

    @property
    def total_kw(self):           # excluding battery recharge (PUE basis)
        return self.it_kw + self.ups_loss_kw + self.mech_kw + self.dist_loss_kw + self.house_kw

    @property
    def max_kw(self):             # including non-coincident battery recharge (sizing basis)
        return self.total_kw + self.recharge_kw

    @property
    def ppue(self):
        return self.total_kw / self.it_kw if self.it_kw else float("nan")

    def as_dict(self):
        d = asdict(self); d.update(total_kw=self.total_kw, max_kw=self.max_kw, ppue=self.ppue); return d


def hall_load(it_kw: float, t_amb_c: float, ups_load_frac: float, house_kw: float = 100.0,
              dist_loss_frac: float = 0.012, recharge_kw: float = 0.0, **mech_kw) -> HallLoad:
    """Facility load of one data hall.

    dist_loss_frac: transformer + LV distribution losses as fraction of (IT + UPS loss + mech) [ASSUMED].
    """
    eta = ups_efficiency(ups_load_frac)
    ups_loss = it_kw * (1.0 / eta - 1.0)
    mech = it_kw * mech_ppue(t_amb_c, **mech_kw)
    dist = dist_loss_frac * (it_kw + ups_loss + mech)
    return HallLoad(it_kw, ups_loss, mech, dist, house_kw, recharge_kw)


def campus_demand(hall: HallLoad, n_halls: int, campus_services_kw: float = 500.0,
                  hv_tx_loss_kw: float = 250.0, diversity: float = 1.0, pf: float = 0.95,
                  include_recharge: bool = False) -> dict:
    """Campus maximum demand at the grid connection.

    diversity: coincidence factor applied to the sum of hall loads (1.0 = no diversity, conservative).
    """
    per_hall = hall.max_kw if include_recharge else hall.total_kw
    p = n_halls * per_hall * diversity + campus_services_kw + hv_tx_loss_kw
    it = n_halls * hall.it_kw
    return {"p_kw": p, "s_kva": p / pf, "it_kw": it, "pue": p / it}


def annual_pue(it_design_kw_per_hall: float, n_halls: int, normal_ups_frac: float, it_util: float = 0.75,
               bins=CLIMATE_BINS_DALARNA, house_kw: float = 100.0, campus_services_kw: float = 500.0,
               hv_tx_p0_kw: float = 32.0, hv_tx_pk_kw: float = 250.0, hv_tx_kva: float = 63000.0,
               n_hv_tx: int = 2, **mech_kw) -> dict:
    """Energy-weighted annual PUE from temperature bins (EN 50600-4-2 definition: annual facility
    energy / annual IT energy)."""
    e_fac = e_it = 0.0
    hours = 0
    rows = []
    for t, h in bins:
        hl = hall_load(it_design_kw_per_hall * it_util, t, normal_ups_frac * it_util, house_kw=house_kw, **mech_kw)
        p_campus = n_halls * hl.total_kw + campus_services_kw
        # HV transformers share the load equally (each loaded at half)
        s_each = p_campus / 0.95 / n_hv_tx
        hv_loss = n_hv_tx * (hv_tx_p0_kw + hv_tx_pk_kw * (s_each / hv_tx_kva) ** 2)
        p_total = p_campus + hv_loss
        e_fac += p_total * h
        e_it += n_halls * hl.it_kw * h
        hours += h
        rows.append({"t_c": t, "hours": h, "pue": p_total / (n_halls * hl.it_kw)})
    return {"pue": e_fac / e_it, "facility_mwh": e_fac / 1000, "it_mwh": e_it / 1000, "hours": hours,
            "bins": rows}


def solve_mech_peak_for_target_pue(target_pue: float, it_kw: float, t_peak_c: float, ups_load_frac: float,
                                   house_kw: float = 100.0, dist_loss_frac: float = 0.012) -> float:
    """Back-solve the design-peak mechanical pPUE that gives a target hall design-peak pPUE."""
    eta = ups_efficiency(ups_load_frac)
    ups_loss = 1.0 / eta - 1.0
    # pPUE = 1 + ups + m + d(1 + ups + m) + house/it  → m = ((pPUE - house/it)/(1+d) - 1 - ups)
    m = (target_pue - house_kw / it_kw) / (1 + dist_loss_frac) - 1 - ups_loss
    return max(m, 0.0)
