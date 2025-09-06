# Layout ortogonal: tronco horizontal, ramais distribuídos e trafos organizados.

BUS_COORDS = {}
LINES = []
TRAFOS = []  # (nome_trafo, mv_bus, lv_bus)

# ---------------- Helpers ----------------
def setp(name, x, y):
    """Define ponto em coordenadas 'cartesianas' (unidades arbitrárias)."""
    BUS_COORDS[name] = [float(x), float(y)]

def seg(name, a, b):
    """Adiciona uma linha nomeada (para aparecer clicável no unifilar)."""
    LINES.append((name, a, b))

def add_trafos_on_rail(mv_bus, start_num, count, step=8, y_offset=12, direction=1):
    """
    Coloca N trafos ligados à mesma barra MV (B2/B3) em um 'trilho' paralelo ao tronco.
    direction: +1 => à direita; -1 => à esquerda
    """
    bx, by = BUS_COORDS[mv_bus]
    for i in range(count):
        n = start_num + i
        lv = f"TR-{n:02d}-LV"
        x = bx + direction * (step * (i + 1))
        y = by + y_offset
        BUS_COORDS[lv] = [x, y]
        TRAFOS.append((f"TR-{n:02d}", mv_bus, lv))

def add_ramal(code: str, up_bus: str, dir_vec: tuple, scale=6):
    """
    Cria CH-<code> (A/B) e L<code>-1/2 posicionados a partir de up_bus no vetor 'dir_vec'.
    Também posiciona TR-XX (dois) com leve offset perpendicular ao ramal.
    Mantém NOME das linhas compatível com o 'model.py'.
    """
    dx, dy = dir_vec
    # comprimentos em múltiplos de scale
    kA, kB, k1, k2 = 14, 20, 26, 32
    ux, uy = BUS_COORDS[up_bus]

    def off(k):  # deslocamento escalonado
        return ux + dx * (k / 6.0), uy + dy * (k / 6.0)

    a = f"CH{code}-A"; ax, ay = off(kA); setp(a, ax, ay)
    b = f"CH{code}-B"; bx, by = off(kB); setp(b, bx, by)
    l1 = f"L{code}-1"; x1, y1 = off(k1); setp(l1, x1, y1)
    l2 = f"L{code}-2"; x2, y2 = off(k2); setp(l2, x2, y2)

    seg(f"{up_bus}-CH{code}-A", up_bus, a)
    seg(f"CH-{code}", a, b)              # chave de ramal (clicável)
    seg(f"CH{code}-B-L1", b, l1)
    seg(f"L{code}-1-L2", l1, l2)

    # trafos no ramal (perpendicular leve)
    # perpendicular p = (-dy, dx)
    px, py = -dy, dx
    norm = max((px**2 + py**2) ** 0.5, 1e-9)
    px /= norm; py /= norm
    # alocar numeração crescente: TR-21..TR-44 (duas unidades por ramal)
    global NEXT_TR
    for k, lv_bus in enumerate([l1, l2], start=0):
        n = NEXT_TR + k
        lv = f"TR-{n:02d}-LV"
        lx, ly = BUS_COORDS[lv_bus]
        # desloca 3 unidades perpendiculares
        BUS_COORDS[lv] = [lx + px * 3.0, ly + py * 3.0]
        TRAFOS.append((f"TR-{n:02d}", lv_bus, lv))
    NEXT_TR += 2

# ---------------- Tronco (horizontal) ----------------
# espaçamento de ~20 unidades entre barras principais
setp("SE_Fortaleza_69kV",  0,   0)
setp("W0321P3-BarraMT",   10,   0)

setp("R1A",               30,   0)
setp("R1B",               50,   0)
setp("W0321P3-B1",        80,   0)

setp("R2A",              110,   0)
setp("R2B",              130,   0)
setp("W0321P3-B2",       160,   0)

setp("R3A",              190,   0)
setp("R3B",              210,   0)
setp("W0321P3-B3",       240,   0)

# interligações (acima e abaixo do tronco)
setp("Interligacao-B4",  150,  80)
setp("R4A",              150,  60)
setp("R4B",              160,  40)

setp("Interligacao-B5",  270, -80)
setp("R5A",              270, -60)
setp("R5B",              255, -40)

# linhas do tronco/interligações
seg("SE-R1A",      "W0321P3-BarraMT", "R1A")
seg("RCL-01",      "R1A", "R1B")
seg("R1B-B1",      "R1B", "W0321P3-B1")
seg("B1-R2A",      "W0321P3-B1", "R2A")
seg("RCL-02",      "R2A", "R2B")
seg("R2B-B2",      "R2B", "W0321P3-B2")
seg("B2-R3A",      "W0321P3-B2", "R3A")
seg("RCL-03",      "R3A", "R3B")
seg("R3B-B3",      "R3B", "W0321P3-B3")
seg("B4-R4A (tie)", "Interligacao-B4", "R4A")
seg("RCL-04",       "R4A", "R4B")
seg("R4B-B2 (tie)", "R4B", "W0321P3-B2")
seg("B5-R5A (tie)", "Interligacao-B5", "R5A")
seg("RCL-05",       "R5A", "R5B")
seg("R5B-B3 (tie)", "R5B", "W0321P3-B3")

# ---------------- Trafos 'em trilho' (TR-01..TR-20) ----------------
# 10 em B2 (acima do tronco), 10 em B3 (abaixo do tronco)
add_trafos_on_rail("W0321P3-B2", start_num=1,  count=10, step=8,  y_offset=+12, direction=+1)
add_trafos_on_rail("W0321P3-B3", start_num=11, count=10, step=8,  y_offset=-12, direction=+1)

# ---------------- Ramais com CH e TRs (TR-21..TR-44) ----------------
# Vetores (dx,dy) distribuídos para não cruzar; módulos relativos.
# Para cima/baixo: (0, +20)/(0, -20). Diagonais: (+/-18, +/-18). Horizontais: (+20, 0), (-20, 0).
NEXT_TR = 21

# B1: dois ramais (cima e baixo)
add_ramal("01", "W0321P3-B1", (0,  20))
add_ramal("02", "W0321P3-B1", (0, -20))

# B2: quatro ramais (diagonais)
add_ramal("03", "W0321P3-B2", ( 18,  18))
add_ramal("04", "W0321P3-B2", ( 18, -18))
add_ramal("05", "W0321P3-B2", (-18,  18))
add_ramal("06", "W0321P3-B2", (-18, -18))

# B3: seis ramais (diagonais + horizontais)
add_ramal("07", "W0321P3-B3", ( 18,  18))
add_ramal("08", "W0321P3-B3", ( 18, -18))
add_ramal("09", "W0321P3-B3", (-18,  18))
add_ramal("10", "W0321P3-B3", (-18, -18))
add_ramal("11", "W0321P3-B3", ( 24,   0))
add_ramal("12", "W0321P3-B3", (-24,   0))
