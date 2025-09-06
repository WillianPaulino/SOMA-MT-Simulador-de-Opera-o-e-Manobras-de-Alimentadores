from threading import Lock
from typing import Dict, Any

from app.sim.model import build_w0321p3
from app.sim.ops import open_line_by_name, run_powerflow, energized_buses

# Ties normalmente abertas (religadores centrais das interligações)
DEFAULT_OPEN = {"RCL-04", "RCL-05"}

_STATE = {"open": set(DEFAULT_OPEN), "fault": set()}
_LOCK = Lock()

def _solve() -> Dict[str, Any]:
    net = build_w0321p3()
    to_open = set(_STATE["open"]) | set(_STATE["fault"])
    for name in to_open:
        open_line_by_name(net, name)

    ok, err = run_powerflow(net)
    if not ok:
        return {"error": f"runpp falhou: {err}"}

    bus_idx2name = net.bus["name"].to_dict()
    line_rows = net.line[["from_bus", "to_bus", "name", "in_service"]]
    energ = energized_buses(net)

    buses = {bus_idx2name[i]: {"energized": bool(i in energ)} for i in net.bus.index}
    lines = {}
    for _, row in line_rows.iterrows():
        name = row["name"]; f = int(row["from_bus"]); t = int(row["to_bus"])
        is_open = not bool(row["in_service"])
        energized = (not is_open) and (f in energ and t in energ)
        lines[name] = {
            "open": is_open, "fault": name in _STATE["fault"], "energized": bool(energized),
            "from": bus_idx2name[f], "to": bus_idx2name[t]
        }
    return {"buses": buses, "lines": lines, "open": sorted(_STATE["open"]), "fault": sorted(_STATE["fault"])}

def get_state():
    with _LOCK: return _solve()

def set_switch(name: str, action: str):
    with _LOCK:
        if action == "open": _STATE["open"].add(name)
        elif action == "close": _STATE["open"].discard(name)
        return _solve()

def set_fault(name: str, action: str):
    with _LOCK:
        if action in ("apply", "set"): _STATE["fault"].add(name)
        elif action in ("clear", "remove"): _STATE["fault"].discard(name)
        return _solve()

def reset_state():
    with _LOCK:
        _STATE["open"] = set(DEFAULT_OPEN); _STATE["fault"] = set()
        return _solve()
