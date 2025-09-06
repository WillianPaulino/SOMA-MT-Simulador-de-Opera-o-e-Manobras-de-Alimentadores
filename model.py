import pandapower as pp

# ------------------------------------------------------------------
#  Rede W0321P3:
#   - SE 69/13,8 kV
#   - Tronco com 3 religadores (RCL-01..03)
#   - 2 interligações com religadores (RCL-04, RCL-05)
#   - 12 ramais com CH de ramal (CH-01..CH-12)
#   - 44 trafos 13,8/0,38 kV (TR-01..TR-44)
# ------------------------------------------------------------------

def build_w0321p3():
    net = pp.create_empty_network(sn_mva=100.)

    # ---------- SE / Barra principal ----------
    bus_se_69 = pp.create_bus(net, vn_kv=69, name="SE_Fortaleza_69kV")
    bus_mt    = pp.create_bus(net, vn_kv=13.8, name="W0321P3-BarraMT")
    pp.create_transformer_from_parameters(
        net, bus_se_69, bus_mt, sn_mva=25, vn_hv_kv=69, vn_lv_kv=13.8,
        vkr_percent=10, vk_percent=12, pfe_kw=15, i0_percent=0.1, name="TR-SE"
    )

    # ---------- Tronco e interligações ----------
    b1 = pp.create_bus(net, vn_kv=13.8, name="W0321P3-B1")
    b2 = pp.create_bus(net, vn_kv=13.8, name="W0321P3-B2")
    b3 = pp.create_bus(net, vn_kv=13.8, name="W0321P3-B3")
    b4 = pp.create_bus(net, vn_kv=13.8, name="Interligacao-B4")
    b5 = pp.create_bus(net, vn_kv=13.8, name="Interligacao-B5")

    r1a = pp.create_bus(net, vn_kv=13.8, name="R1A")
    r1b = pp.create_bus(net, vn_kv=13.8, name="R1B")
    r2a = pp.create_bus(net, vn_kv=13.8, name="R2A")
    r2b = pp.create_bus(net, vn_kv=13.8, name="R2B")
    r3a = pp.create_bus(net, vn_kv=13.8, name="R3A")
    r3b = pp.create_bus(net, vn_kv=13.8, name="R3B")

    # tronco
    pp.create_line_from_parameters(net, bus_mt, r1a, 0.10, 0.3, 0.4, 10, 0.8, name="SE-R1A")
    pp.create_line_from_parameters(net, r1a, r1b, 0.01, 0.1, 0.1,  1, 0.8, name="RCL-01")
    pp.create_line_from_parameters(net, r1b, b1,  0.20, 0.3, 0.4, 10, 0.8, name="R1B-B1")

    pp.create_line_from_parameters(net, b1, r2a,  0.30, 0.3, 0.4, 10, 0.8, name="B1-R2A")
    pp.create_line_from_parameters(net, r2a, r2b, 0.01, 0.1, 0.1,  1, 0.8, name="RCL-02")
    pp.create_line_from_parameters(net, r2b, b2,  0.30, 0.3, 0.4, 10, 0.8, name="R2B-B2")

    pp.create_line_from_parameters(net, b2, r3a,  0.30, 0.3, 0.4, 10, 0.8, name="B2-R3A")
    pp.create_line_from_parameters(net, r3a, r3b, 0.01, 0.1, 0.1,  1, 0.8, name="RCL-03")
    pp.create_line_from_parameters(net, r3b, b3,  0.30, 0.3, 0.4, 10, 0.8, name="R3B-B3")

    # interligações (NO)
    r4a = pp.create_bus(net, vn_kv=13.8, name="R4A")
    r4b = pp.create_bus(net, vn_kv=13.8, name="R4B")
    pp.create_line_from_parameters(net, b4, r4a,  0.10, 0.3, 0.4, 10, 0.6, name="B4-R4A (tie)")
    pp.create_line_from_parameters(net, r4a, r4b, 0.01, 0.1, 0.1,  1, 0.6, name="RCL-04")
    pp.create_line_from_parameters(net, r4b, b2,  0.10, 0.3, 0.4, 10, 0.6, name="R4B-B2 (tie)")

    r5a = pp.create_bus(net, vn_kv=13.8, name="R5A")
    r5b = pp.create_bus(net, vn_kv=13.8, name="R5B")
    pp.create_line_from_parameters(net, b5, r5a,  0.10, 0.3, 0.4, 10, 0.6, name="B5-R5A (tie)")
    pp.create_line_from_parameters(net, r5a, r5b, 0.01, 0.1, 0.1,  1, 0.6, name="RCL-05")
    pp.create_line_from_parameters(net, r5b, b3,  0.10, 0.3, 0.4, 10, 0.6, name="R5B-B3 (tie)")

    # Cargas MT agregadas em barras do tronco
    pp.create_load(net, b1, p_mw=0.8, q_mvar=0.2,  name="Carga_B1|prior:critica")
    pp.create_load(net, b2, p_mw=0.6, q_mvar=0.15, name="Carga_B2|prior:alta")
    pp.create_load(net, b3, p_mw=0.6, q_mvar=0.15, name="Carga_B3|prior:normal")

    # ---------- Helpers ----------
    def add_trafo(idx: int, mv_bus: int, p_mw: float = 0.08, q_mvar: float = 0.02):
        lv = pp.create_bus(net, vn_kv=0.38, name=f"TR-{idx:02d}-LV")
        pp.create_transformer_from_parameters(
            net, mv_bus, lv, sn_mva=0.5, vn_hv_kv=13.8, vn_lv_kv=0.38,
            vkr_percent=4, vk_percent=6, pfe_kw=1, i0_percent=0.2, name=f"TR-{idx:02d}"
        )
        pp.create_load(net, lv, p_mw=p_mw, q_mvar=q_mvar, name=f"LD-TR-{idx:02d}")
        return idx + 1

    def add_lateral(code: str, upstream_bus: int, start_idx: int, trafos: int = 2):
        """
        Cria um ramal com uma chave 'CH-<code>' e 1..N barras do ramal.
        Retorna o próximo índice de trafo.
        """
        # pequenos nós para a chave
        a = pp.create_bus(net, vn_kv=13.8, name=f"CH{code}-A")
        b = pp.create_bus(net, vn_kv=13.8, name=f"CH{code}-B")
        pp.create_line_from_parameters(net, upstream_bus, a, 0.05, 0.3, 0.4, 10, 0.6, name=f"{get_name(upstream_bus)}-CH{code}-A")
        pp.create_line_from_parameters(net, a, b, 0.01, 0.1, 0.1, 1, 0.6, name=f"CH-{code}")  # <- chave de ramal (clicável)

        # barra(s) do ramal
        l1 = pp.create_bus(net, vn_kv=13.8, name=f"L{code}-1")
        pp.create_line_from_parameters(net, b, l1, 0.15, 0.3, 0.4, 10, 0.6, name=f"CH{code}-B-L1")

        next_idx = start_idx
        next_idx = add_trafo(next_idx, l1)

        if trafos >= 2:
            l2 = pp.create_bus(net, vn_kv=13.8, name=f"L{code}-2")
            pp.create_line_from_parameters(net, l1, l2, 0.10, 0.3, 0.4, 10, 0.6, name=f"L{code}-1-L2")
            next_idx = add_trafo(next_idx, l2)
        if trafos >= 3:
            l3 = pp.create_bus(net, vn_kv=13.8, name=f"L{code}-3")
            pp.create_line_from_parameters(net, l2, l3, 0.10, 0.3, 0.4, 10, 0.6, name=f"L{code}-2-L3")
            next_idx = add_trafo(next_idx, l3)
        return next_idx

    def get_name(bus_idx: int) -> str:
        return net.bus.at[bus_idx, "name"]

    # ---------- Trafos "dispersos" originais (TR-01..TR-20) ----------
    # Mantemos 10 em B2 e 10 em B3 (como antes)
    nxt = 1
    for _ in range(10): nxt = add_trafo(nxt, b2)
    for _ in range(10): nxt = add_trafo(nxt, b3)

    # ---------- Novos RAMAIS com chave de ramal ----------
    # B1: dois ramais
    nxt = add_lateral("01", b1, nxt, trafos=2)    # CH-01, L01-1.., TR-21..TR-22
    nxt = add_lateral("02", b1, nxt, trafos=2)    # TR-23..TR-24

    # B2: quatro ramais
    nxt = add_lateral("03", b2, nxt, trafos=2)    # TR-25..TR-26
    nxt = add_lateral("04", b2, nxt, trafos=2)    # TR-27..TR-28
    nxt = add_lateral("05", b2, nxt, trafos=2)    # TR-29..TR-30
    nxt = add_lateral("06", b2, nxt, trafos=2)    # TR-31..TR-32

    # B3: seis ramais
    nxt = add_lateral("07", b3, nxt, trafos=2)    # TR-33..TR-34
    nxt = add_lateral("08", b3, nxt, trafos=2)    # TR-35..TR-36
    nxt = add_lateral("09", b3, nxt, trafos=2)    # TR-37..TR-38
    nxt = add_lateral("10", b3, nxt, trafos=2)    # TR-39..TR-40
    nxt = add_lateral("11", b3, nxt, trafos=2)    # TR-41..TR-42
    nxt = add_lateral("12", b3, nxt, trafos=2)    # TR-43..TR-44

    # Fonte externa
    pp.create_ext_grid(net, bus_se_69, vm_pu=1.0)
    return net

def customers_from_mw(p_mw: float, kw_per_customer: float = 5.0) -> int:
    return int(round((p_mw * 1000) / kw_per_customer))
