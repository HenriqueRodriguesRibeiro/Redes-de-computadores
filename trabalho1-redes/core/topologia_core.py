#!/usr/bin/env python3
"""
topologia_core.py - Monta a topologia do Trabalho 1 no CORE via API Python
(sem GUI) e executa validacao de rede + experimentos de GET/PUT.

Topologia:

    [servidor] --(acesso A)-- R1 ==(NUCLEO/gargalo)== R2 --(acesso B)-- [cliente]

    - servidor e cliente: nos finais (CoreNode) em redes de acesso distintas
    - R1, R2: roteadores do nucleo
    - enlace R1<->R2: gargalo (configura banda + atraso, sem perda)

Uso (DENTRO do container CORE, como root):

    # 1) so montar a topologia e validar a rede (ping/traceroute/iperf):
    /opt/core/venv/bin/python topologia_core.py --tech 4G --validar

    # 2) montar + rodar o experimento completo (GET/PUT, conc 1/10/50, n=15):
    /opt/core/venv/bin/python topologia_core.py --tech 4G --experimento --n 15
    /opt/core/venv/bin/python topologia_core.py --tech FIBRA --experimento --n 15

    # 3) manter a topologia aberta pra uso manual (abre terminais com vcmd):
    /opt/core/venv/bin/python topologia_core.py --tech 4G --manter

Tecnologias (gargalo):
    4G     -> 20 Mbps / 50 ms
    FIBRA  -> 100 Mbps / 5 ms

Requer root (cria network namespaces) e o core-daemon instalado.
"""
import argparse
import os
import sys
import time

from core.emulator.coreemu import CoreEmu
from core.emulator.data import IpPrefixes, LinkOptions
from core.emulator.enumerations import EventTypes
from core.errors import CoreCommandError
from core.nodes.base import CoreNode
from core.nodes.network import SwitchNode

# ------------------------------------------------------------------ parametros
# Parametros tipicos das 2 tecnologias de acesso (gargalo).
# bandwidth em bps, delay em microssegundos (us). Sem perda (loss) por requisito.
TECNOLOGIAS = {
    "4G":    {"bandwidth": 20_000_000,  "delay_us": 50_000},   # 20 Mbps, 50 ms
    "FIBRA": {"bandwidth": 100_000_000, "delay_us": 5_000},    # 100 Mbps, 5 ms
}

# Caminho do projeto compilado DENTRO do container (ajuste se necessario).
PROJ = "/root/trabalho1-redes"
PORT = 8080

# IPs fixos para facilitar os comandos (o helper atribui em ordem).
IP_SERVIDOR = "10.0.0.20"
IP_CLIENTE = "10.0.3.20"


def _position(x, y):
    """Compatibilidade entre versoes: algumas usam Position, outras x=/y=."""
    try:
        from core.nodes.base import Position
        return {"position": Position(x=x, y=y)}
    except Exception:
        return {"_x": x, "_y": y}


def add_node(session, cls, x, y, name=None):
    """add_node compativel entre versoes do CORE."""
    pos = _position(x, y)
    if "position" in pos:
        try:
            return session.add_node(cls, position=pos["position"], name=name) if name \
                else session.add_node(cls, position=pos["position"])
        except TypeError:
            return session.add_node(cls, position=pos["position"])
    # fallback versoes antigas
    try:
        return session.add_node(cls, _x=pos["_x"], _y=pos["_y"])
    except TypeError:
        return session.add_node(cls)


def montar_topologia(session, prefixes):
    """Cria nos, redes de acesso, roteadores de nucleo e enlaces."""
    # redes de acesso (switches) e nucleo
    acessoA = add_node(session, SwitchNode, 150, 200, "acessoA")
    acessoB = add_node(session, SwitchNode, 650, 200, "acessoB")

    r1 = add_node(session, CoreNode, 300, 200, "R1")
    r2 = add_node(session, CoreNode, 500, 200, "R2")

    servidor = add_node(session, CoreNode, 60, 200, "servidor")
    cliente = add_node(session, CoreNode, 740, 200, "cliente")

    # --- rede de acesso A: servidor <-> acessoA <-> R1 (10.0.0.0/24)
    pa = IpPrefixes(ip4_prefix="10.0.0.0/24")
    session.add_link(servidor.id, acessoA.id, pa.create_iface(servidor))
    session.add_link(r1.id, acessoA.id, pa.create_iface(r1))

    # --- nucleo: R1 <-> R2 (10.0.1.0/24)  [ENLACE GARGALO]
    pn = IpPrefixes(ip4_prefix="10.0.1.0/24")
    iface_r1 = pn.create_iface(r1)
    iface_r2 = pn.create_iface(r2)

    # --- rede de acesso B: R2 <-> acessoB <-> cliente (10.0.3.0/24)
    pb = IpPrefixes(ip4_prefix="10.0.3.0/24")
    session.add_link(r2.id, acessoB.id, pb.create_iface(r2))
    session.add_link(cliente.id, acessoB.id, pb.create_iface(cliente))

    nodes = {
        "servidor": servidor, "cliente": cliente,
        "r1": r1, "r2": r2, "acessoA": acessoA, "acessoB": acessoB,
    }
    core_link = {"r1_iface": iface_r1, "r2_iface": iface_r2}
    return nodes, core_link


def configurar_gargalo(session, nodes, core_link, tech):
    """Adiciona o enlace de nucleo R1<->R2 ja com banda e atraso (gargalo)."""
    cfg = TECNOLOGIAS[tech]
    options = LinkOptions(bandwidth=cfg["bandwidth"], delay=cfg["delay_us"], loss=0.0)
    session.add_link(
        nodes["r1"].id, nodes["r2"].id,
        core_link["r1_iface"], core_link["r2_iface"], options,
    )
    print(f"[gargalo] R1<->R2 = {tech}: "
          f"{cfg['bandwidth'] // 1_000_000} Mbps / {cfg['delay_us'] // 1000} ms (loss=0)")


def ncmd(node, cmd, shell=False, ignore_erro=False, wait=True):
    """Executa comando num no, com suporte a shell e a erros esperados.

    No CORE 9.x, node.cmd() NAO usa shell por padrao, entao operadores como
    &&, ||, |, >, & exigem shell=True. Alem disso, comandos como 'ip route add'
    de uma rota que ja existe retornam status != 0 e levantam CoreCommandError;
    ignore_erro=True captura e ignora essas falhas esperadas. Para processos
    em background use wait=False.
    """
    try:
        try:
            return node.cmd(cmd, wait=wait, shell=shell)
        except TypeError:
            # versoes que nao aceitam 'wait'
            return node.cmd(cmd, shell=shell)
    except CoreCommandError as e:
        if ignore_erro:
            return str(e)
        raise


def ip_na_rede(node, prefixo):
    """Retorna o IPv4 do no cujo endereco comeca por 'prefixo' (ex.: '10.0.1.')."""
    out = node.cmd("ip -4 -o addr show")
    for linha in out.splitlines():
        campos = linha.split()
        for i, c in enumerate(campos):
            if c == "inet" and i + 1 < len(campos):
                addr = campos[i + 1].split("/")[0]
                if addr.startswith(prefixo):
                    return addr
    return None


def rotas_estaticas(nodes):
    """Monta as rotas entre as 3 sub-redes descobrindo os IPs reais.

    Topologia:
      servidor(10.0.0.x) -- acessoA -- R1 == nucleo(10.0.1.x) == R2 -- acessoB -- cliente(10.0.3.x)
    """
    servidor, cliente = nodes["servidor"], nodes["cliente"]
    r1, r2 = nodes["r1"], nodes["r2"]

    # IPs reais de cada interface relevante
    r1_acessoA = ip_na_rede(r1, "10.0.0.")   # R1 na rede do servidor
    r1_nucleo = ip_na_rede(r1, "10.0.1.")    # R1 no nucleo
    r2_nucleo = ip_na_rede(r2, "10.0.1.")    # R2 no nucleo
    r2_acessoB = ip_na_rede(r2, "10.0.3.")   # R2 na rede do cliente

    print(f"[rotas] R1: acessoA={r1_acessoA} nucleo={r1_nucleo} | "
          f"R2: nucleo={r2_nucleo} acessoB={r2_acessoB}")

    # habilita encaminhamento IP nos roteadores do nucleo
    for r in (r1, r2):
        ncmd(r, "sysctl -w net.ipv4.ip_forward=1", ignore_erro=True)

    # servidor -> rede do cliente, saindo por R1 (gateway na propria rede de acesso)
    ncmd(servidor, f"ip route replace 10.0.3.0/24 via {r1_acessoA}", ignore_erro=True)
    # cliente -> rede do servidor, saindo por R2
    ncmd(cliente, f"ip route replace 10.0.0.0/24 via {r2_acessoB}", ignore_erro=True)

    # R1 -> rede do cliente, atravessando o nucleo ate R2
    ncmd(r1, f"ip route replace 10.0.3.0/24 via {r2_nucleo}", ignore_erro=True)
    # R2 -> rede do servidor, atravessando o nucleo ate R1
    ncmd(r2, f"ip route replace 10.0.0.0/24 via {r1_nucleo}", ignore_erro=True)


def ip_do_no(node, prefixo):
    """Descobre o IPv4 do no numa dada sub-rede (ex.: '10.0.0')."""
    out = node.cmd("ip -4 addr show")
    for linha in out.splitlines():
        linha = linha.strip()
        if linha.startswith("inet ") and prefixo in linha:
            return linha.split()[1].split("/")[0]
    return None


def tem_binario(node, nome):
    """True se o binario 'nome' existe no PATH do no."""
    try:
        out = node.cmd(f"sh -c 'command -v {nome} || true'", shell=True)
        return bool(out.strip())
    except Exception:
        return False


def validar_rede(nodes):
    """Executa ping, traceroute e iperf entre cliente e servidor.

    traceroute/iperf podem nao estar instalados nos nos; nesse caso usamos
    alternativas (tracepath) ou avisamos. Os nos compartilham o filesystem do
    container, entao 'apt install traceroute iperf' no container resolve.
    """
    servidor, cliente = nodes["servidor"], nodes["cliente"]
    ip_srv = ip_na_rede(servidor, "10.0.0.") or IP_SERVIDOR
    print(f"\n=== Validacao de rede (servidor={ip_srv}) ===")

    print("\n--- ping -c 5 (RTT fim-a-fim) ---")
    print(ncmd(cliente, f"ping -c 5 {ip_srv}", ignore_erro=True))

    print("\n--- traceroute (RTT por salto) ---")
    if tem_binario(cliente, "traceroute"):
        print(ncmd(cliente, f"traceroute -n {ip_srv}", ignore_erro=True))
    elif tem_binario(cliente, "tracepath"):
        print(ncmd(cliente, f"tracepath -n {ip_srv}", ignore_erro=True))
    else:
        print("  (traceroute/tracepath ausentes. Instale no container: "
              "'sudo docker exec core apt-get install -y traceroute')")

    print("\n--- iperf (vazao do gargalo) ---")
    iperf = "iperf" if tem_binario(cliente, "iperf") else (
        "iperf3" if tem_binario(cliente, "iperf3") else None)
    if iperf:
        ncmd(servidor, f"pkill -f '{iperf} -s'", shell=True, ignore_erro=True)
        ncmd(servidor, f"{iperf} -s > /tmp/iperf_srv.log 2>&1 &",
             shell=True, ignore_erro=True, wait=False)
        time.sleep(1)
        print(ncmd(cliente, f"{iperf} -c {ip_srv} -t 5", ignore_erro=True))
        ncmd(servidor, f"pkill -f '{iperf} -s'", shell=True, ignore_erro=True)
    else:
        print("  (iperf ausente. Instale no container: "
              "'sudo docker exec core apt-get install -y iperf')")
        print("  Alternativa: a vazao tambem e medida pelo proprio cliente do "
              "trabalho (coluna vazao_mbps no CSV do experimento).")


def _vcmd_prefix(session, node):
    """Monta o prefixo 'vcmd -c <ctrl-path> --' para executar no namespace do no.

    No CORE 9.x o diretorio de controle do no fica em
    <session_dir>/<node_name> e e consumido pelo vcmd.
    """
    base = (getattr(session, "directory", None)
            or getattr(session, "session_dir", None)
            or f"/tmp/pycore.{session.id}")
    base = str(base)
    return ["vcmd", "-c", os.path.join(base, node.name), "--"]


def _stream(args):
    """Executa 'args' transmitindo stdout/stderr em tempo real para a tela."""
    import subprocess
    p = subprocess.Popen(
        args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1,
    )
    for linha in iter(p.stdout.readline, ""):
        sys.stdout.write(linha)
        sys.stdout.flush()
    p.stdout.close()
    return p.wait()


def rodar_experimento(session, nodes, tech, n):
    """Sobe o servidor e roda o grid de experimentos com saida EM TEMPO REAL.

    A saida do run_experiment.sh e transmitida ao vivo (via vcmd + Popen),
    para que cada '-> concluido:' apareca na hora, em vez de ficar bufferizada
    ate o fim (o que fazia parecer travado).
    """
    servidor, cliente = nodes["servidor"], nodes["cliente"]
    ip_srv = ip_na_rede(servidor, "10.0.0.") or IP_SERVIDOR

    print(f"\n=== Experimento | tech={tech} | n={n} | servidor={ip_srv} ===")

    # compila (idempotente)
    ncmd(servidor, f"cd {PROJ} && make", shell=True, ignore_erro=True)
    ncmd(cliente, f"cd {PROJ} && make", shell=True, ignore_erro=True)

    # gera arquivos de teste no CLIENTE (origem dos PUTs), em testfiles/
    print("[gen] gerando arquivos de teste no cliente (100 KB e 10 MB)...")
    ncmd(cliente, f"cd {PROJ} && ./scripts/gen_files.sh testfiles",
         shell=True, ignore_erro=True)

    # IMPORTANTE: o GET baixa arquivos que precisam EXISTIR no servidor.
    # O servidor serve a partir de serverfiles/, entao populamos esse diretorio
    # com os mesmos arquivos de teste (gerados diretamente no servidor).
    print("[gen] populando serverfiles/ no servidor (para os GETs)...")
    ncmd(servidor, f"cd {PROJ} && ./scripts/gen_files.sh serverfiles",
         shell=True, ignore_erro=True)
    print("[gen] ok.")

    # sobe o servidor em background no no servidor
    ncmd(servidor, "pkill -f 'bin/server'", shell=True, ignore_erro=True)
    ncmd(servidor, f"cd {PROJ} && nohup ./bin/server {PORT} serverfiles "
                   f"> /tmp/server.log 2>&1 &",
         shell=True, ignore_erro=True, wait=False)
    time.sleep(1)

    # roda o experimento a partir do no cliente, com saida ao vivo
    cli_pref = _vcmd_prefix(session, cliente)
    script = f"cd {PROJ} && ./scripts/run_experiment.sh {ip_srv} {PORT} {tech} {n}"
    print("[exp] iniciando grid (voce vera '-> concluido:' por bloco)...\n")
    rc = _stream(cli_pref + ["bash", "-c", script])
    print(f"\n[exp] run_experiment.sh terminou (rc={rc})")

    ncmd(servidor, "pkill -f 'bin/server'", shell=True, ignore_erro=True)
    print(f"[ok] CSV acumulado em {PROJ}/data/resultados.csv")


def main():
    ap = argparse.ArgumentParser(description="Topologia CORE + experimentos (Trabalho 1)")
    ap.add_argument("--tech", choices=list(TECNOLOGIAS), default="4G",
                    help="tecnologia do gargalo (default: 4G)")
    ap.add_argument("--n", type=int, default=15, help="repeticoes (default 15)")
    ap.add_argument("--validar", action="store_true",
                    help="roda ping/traceroute/iperf e sai")
    ap.add_argument("--experimento", action="store_true",
                    help="roda o grid completo de GET/PUT")
    ap.add_argument("--manter", action="store_true",
                    help="mantem a sessao aberta (Ctrl+C para encerrar)")
    args = ap.parse_args()

    if os.geteuid() != 0:
        print("ERRO: rode como root (cria network namespaces).", file=sys.stderr)
        sys.exit(1)

    coreemu = CoreEmu()
    session = coreemu.create_session()
    session.set_state(EventTypes.CONFIGURATION_STATE)
    prefixes = IpPrefixes(ip4_prefix="10.0.0.0/24")

    try:
        nodes, core_link = montar_topologia(session, prefixes)
        configurar_gargalo(session, nodes, core_link, args.tech)
        session.instantiate()
        time.sleep(2)
        rotas_estaticas(nodes)
        time.sleep(1)

        if args.validar:
            validar_rede(nodes)
        if args.experimento:
            rodar_experimento(session, nodes, args.tech, args.n)
        if args.manter or (not args.validar and not args.experimento):
            print("\nTopologia ativa. Use 'sudo docker exec -it core vcmd -c "
                  "<node> -- bash' em outro terminal. Ctrl+C para encerrar.")
            try:
                while True:
                    time.sleep(3600)
            except KeyboardInterrupt:
                pass
    finally:
        print("\n[shutdown] encerrando sessao CORE...")
        session.shutdown()
        coreemu.shutdown()


if __name__ == "__main__":
    main()
