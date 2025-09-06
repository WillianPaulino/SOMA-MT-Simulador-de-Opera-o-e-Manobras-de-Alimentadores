from typing import Tuple, List, Optional
import pandapower as pp

from .model import customers_from_mw
from .events import Event, parse_target

def open_line_by_name(net, name):
    idx = net.line[net.line.name == name].index
    if len(idx):
        net.line.at[idx[0], "in_service"] = False
        return idx[0]
    return None

def close_line_by_name(net, name):
    idx = net.line[net.line.name == name].index
    if len(idx):
        net.line.at[idx[0], "in_service"] = True
        return idx[0]
    return None

def run_powerflow(net):
    try:
        pp.runpp(net)
        return True, None
    except Exception as e:
        return False, str(e)

def energized_buses(net):
    if net.res_bus.empty:
        return set()
    return set(net.res_bus[net.res_bus.vm_pu.notna()].index)

def customers_interrupted(net, energized_bus_indices):
    p_total = 0.0
    for _, load in net.load.iterrows():
        if load.bus not in energized_bus_indices:
            p_total += load.p_mw
    return customers_from_mw(p_total)

def _fail_line(net, line_name: str):   open_line_by_name(net, line_name)
def _restore_line(net, line_name: str): close_line_by_name(net, line_name)
def _device_out_switch(net, switch_name: str): open_line_by_name(net, switch_name)

def _priority_of(name: str) -> int:
    if "|prior:critica" in name: return 3
    if "|prior:alta" in name: return 2
    return 1

def _priority_score_served(net, energized):
    score = 0
    for _, load in net.load.iterrows():
        if load.bus in energized: score += _priority_of(load.name or "")
    return score

def _violates_limits(net, limits) -> bool:
    if not limits: return False
    vmin = limits.get("vmin_pu", 0.93); vmax = limits.get("vmax_pu", 1.05)
    imax_percent = limits.get("imax_percent", 100.0)
    if not net.res_bus.empty:
        if (net.res_bus.vm_pu < vmin).any() or (net.res_bus.vm_pu > vmax).any(): return True
    if not net.res_line.empty and "loading_percent" in net.res_line:
        if (net.res_line.loading_percent > imax_percent).any(): return True
    return False

def isolate_and_reconfigure(net, target_line_name: str, limits=None) -> Tuple[List[dict], int, int]:
    timeline = []
    _fail_line(net, target_line_name); timeline.append({"t": 1, "op": f"abrir {target_line_name}"})
    open_line_by_name(net, "R1B-B1"); timeline.append({"t": 5, "op": "abrir R1B-B1"})
    ok, err = run_powerflow(net)
    if not ok: timeline.append({"t": 6, "op": f"fluxo falhou: {err}"})
    clients_iso = customers_interrupted(net, energized_buses(net))

    candidates = ["R4B-B2 (tie)", "R5B-B3 (tie)"]
    best = None
    for tie in candidates:
        close_line_by_name(net, tie)
        ok2, err2 = run_powerflow(net)
        if not ok2 or _violates_limits(net, limits):
            open_line_by_name(net, tie); continue
        energized = energized_buses(net)
        c_after = customers_interrupted(net, energized)
        prio = _priority_score_served(net, energized)
        key = (prio, -c_after)
        open_line_by_name(net, tie)
        if best is None or key > best[0]:
            best = (key, tie, c_after)
    if best:
        _, best_tie, _ = best
        close_line_by_name(net, best_tie)
        timeline.append({"t": 7, "op": f"fechar {best_tie}"})
        run_powerflow(net)
    clients_after = customers_interrupted(net, energized_buses(net))
    return timeline, clients_iso, clients_after

def apply_event_and_operate(net, event: Event, limits: Optional[dict] = None) -> Tuple[List[dict], int, int, List[dict]]:
    ops_extra: List[dict] = []
    kind, name = parse_target(event.target)
    if event.type == "fault_permanent":
        timeline, c_ini, c_pos = isolate_and_reconfigure(net, name, limits=limits)
        return timeline, c_ini, c_pos, ops_extra
    if event.type == "fault_temporary":
        _fail_line(net, name); t = 1
        ops = [{"t": t, "op": f"abrir {name} (falha temporária)"}]
        run_powerflow(net)
        clients_initial = customers_interrupted(net, energized_buses(net))
        t += max(1, int(event.duration_min or 2))
        _restore_line(net, name)
        ops.append({"t": t, "op": f"religar {name} (após falha temporária)"})
        ok2, err2 = run_powerflow(net)
        if not ok2: ops.append({"t": t+1, "op": f"religamento falhou: {err2}"})
        clients_after = customers_interrupted(net, energized_buses(net))
        return ops, clients_initial, clients_after, ops_extra
    if event.type == "device_out":
        _device_out_switch(net, name); ops_extra.append({"t": 1, "op": f"indisponibilidade: {name}"})
        timeline, c_ini, c_pos = isolate_and_reconfigure(net, "R3B-B3", limits=limits)
        return ops_extra + timeline, c_ini, c_pos, ops_extra
    return [], 0, 0, ops_extra
