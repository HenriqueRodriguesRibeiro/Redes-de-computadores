#!/usr/bin/env python3
"""diagnostico.py - monta a topologia e imprime IPs, rotas e binarios
disponiveis em cada no, para depurar roteamento no CORE 9.2."""
import time
from core.emulator.coreemu import CoreEmu
from core.emulator.data import IpPrefixes, LinkOptions
from core.emulator.enumerations import EventTypes
from core.nodes.base import CoreNode
from core.nodes.network import SwitchNode


def addn(session, cls, name):
    try:
        from core.nodes.base import Position
        return session.add_node(cls, position=Position(x=100, y=100))
    except Exception:
        return session.add_node(cls)


def main():
    coreemu = CoreEmu()
    session = coreemu.create_session()
    session.set_state(EventTypes.CONFIGURATION_STATE)

    acessoA = addn(session, SwitchNode, "acessoA")
    acessoB = addn(session, SwitchNode, "acessoB")
    r1 = addn(session, CoreNode, "R1")
    r2 = addn(session, CoreNode, "R2")
    servidor = addn(session, CoreNode, "servidor")
    cliente = addn(session, CoreNode, "cliente")

    pa = IpPrefixes(ip4_prefix="10.0.0.0/24")
    session.add_link(servidor.id, acessoA.id, pa.create_iface(servidor))
    session.add_link(r1.id, acessoA.id, pa.create_iface(r1))

    pn = IpPrefixes(ip4_prefix="10.0.1.0/24")
    ir1 = pn.create_iface(r1)
    ir2 = pn.create_iface(r2)

    pb = IpPrefixes(ip4_prefix="10.0.3.0/24")
    session.add_link(r2.id, acessoB.id, pb.create_iface(r2))
    session.add_link(cliente.id, acessoB.id, pb.create_iface(cliente))

    opt = LinkOptions(bandwidth=20_000_000, delay=50_000, loss=0.0)
    session.add_link(r1.id, r2.id, ir1, ir2, opt)

    session.instantiate()
    time.sleep(2)

    nós = [("servidor", servidor), ("cliente", cliente), ("R1", r1), ("R2", r2)]
    for nome, n in nós:
        print(f"\n########## {nome} ##########")
        print("--- IPs ---")
        print(n.cmd("ip -4 -o addr show"))
        print("--- rotas ---")
        print(n.cmd("ip route"))

    print("\n########## binarios disponiveis (no cliente) ##########")
    for b in ["ping", "traceroute", "tracepath", "iperf", "iperf3", "mtr", "nc"]:
        try:
            out = cliente.cmd(f"which {b}", shell=True)
        except Exception:
            out = "(ausente)"
        print(f"{b:12s}: {out.strip() or '(ausente)'}")

    session.shutdown()
    coreemu.shutdown()


if __name__ == "__main__":
    main()
