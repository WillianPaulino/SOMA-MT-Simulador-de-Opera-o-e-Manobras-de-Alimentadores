from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.sim.model import build_w0321p3, customers_from_mw
from app.sim.events import Event
from app.sim.ops import apply_event_and_operate, run_powerflow, energized_buses
from app.sim.kpis import compute_kpis
from app.sim.geo import BUS_COORDS, LINES, TRAFOS

from app.db import init_db, SessionLocal, Run
from app.state import get_state, set_switch, set_fault, reset_state

BASE_DIR = Path(__file__).resolve().parents[2]
TEMPLATES_DIR = BASE_DIR / "frontend" / "templates"
STATIC_DIR = BASE_DIR / "frontend" / "static"

app = FastAPI(title="Simulador W0321P3")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

init_db()

@app.get("/health")
def health():
    return {"ok": True, "service": "w0321p3-sim"}

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# ===== Topologia/estado para o unifilar =====
@app.get("/api/topology")
def topology():
    return {"buses": BUS_COORDS, "lines": LINES, "trafos": TRAFOS}

@app.get("/api/state")
def api_state():
    return get_state()

@app.post("/api/switch")
def api_switch(body: dict):
    name = body.get("name"); action = body.get("action", "open")
    if not name: return JSONResponse({"error": "name obrigatório"}, status_code=400)
    return set_switch(name, action)

@app.post("/api/fault")
def api_fault(body: dict):
    name = body.get("name"); action = body.get("action", "apply")
    if not name: return JSONResponse({"error": "name obrigatório"}, status_code=400)
    return set_fault(name, action)

@app.post("/api/reset")
def api_reset():
    return reset_state()

# ===== Simulação por cenário (continua) =====
@app.post("/api/run")
async def run_scenario(req: dict):
    event = req.get("event", {"type":"fault_permanent","target":"line:R3B-B3","t0_min":0})
    interruption_min = float(req.get("interruption_min", 20))
    limits = req.get("limits", None)

    net = build_w0321p3()
    ok, err = run_powerflow(net)
    if not ok: return JSONResponse({"error": f"Fluxo normal falhou: {err}"}, status_code=500)

    p_total = net.load.p_mw.sum()
    customers_total = customers_from_mw(p_total)

    ev = Event(**event)
    timeline, clients_initial, clients_after, _ = apply_event_and_operate(net, ev, limits=limits)

    kpis = compute_kpis(customers_total, clients_initial, clients_after, interruption_min)
    run_powerflow(net)
    buses_on = list(energized_buses(net))

    payload = {
        "feeder": "W0321P3",
        "timeline": timeline,
        "customers_total": customers_total,
        "clients_initial": clients_initial,
        "clients_after_reconfig": clients_after,
        "kpis": kpis.__dict__,
        "energized_buses_indices": buses_on
    }

    with SessionLocal() as s:
        r = Run(feeder="W0321P3", event_type=ev.type, target=ev.target,
                interruption_min=interruption_min, result_json=payload)
        s.add(r); s.commit(); payload["run_id"] = r.id
    return payload

@app.get("/api/runs")
def list_runs(limit: int = 20):
    with SessionLocal() as s:
        rows = s.query(Run).order_by(Run.id.desc()).limit(limit).all()
        return [{"id": r.id, "created_at": r.created_at.isoformat(), "feeder": r.feeder,
                 "event_type": r.event_type, "target": r.target,
                 "interruption_min": r.interruption_min} for r in rows]

@app.get("/api/runs/{run_id}")
def get_run(run_id: int):
    with SessionLocal() as s:
        r = s.query(Run).get(run_id)
        if not r: return JSONResponse({"error": "run não encontrado"}, status_code=404)
        return r.result_json
