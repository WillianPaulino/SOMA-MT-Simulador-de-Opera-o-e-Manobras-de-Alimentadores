from dataclasses import dataclass

@dataclass
class KPIResult:
    saidi_h: float
    saifi: float
    caidi_h: float
    ens_mwh: float
    customers_interrupted_initial: int
    customers_after_reconfig: int

def compute_kpis(customers_total: int,
                 clients_initial: int,
                 clients_after: int,
                 interruption_min: float,
                 p_not_supplied_mw: float = 2.0):
    if clients_initial <= 0 or customers_total <= 0:
        return KPIResult(0, 0, 0, 0, 0, 0)
    saifi = 1.0
    saidi_h = (clients_initial * (interruption_min/60.0)) / customers_total
    caidi_h = saidi_h / saifi
    ens_mwh = p_not_supplied_mw * (interruption_min/60.0)
    return KPIResult(saidi_h, saifi, caidi_h, ens_mwh, clients_initial, clients_after)
