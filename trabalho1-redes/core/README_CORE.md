# CORE sem GUI — topologia via script Python

Este diretório traz duas formas de montar a topologia do Trabalho 1 no CORE:

- **`topologia.imn`** — arquivo da topologia para abrir na GUI do CORE (`core-gui`).
- **`topologia_core.py`** — script Python que monta a topologia inteira **sem GUI**,
  valida a rede (ping/traceroute/iperf) e roda os experimentos. É a rota recomendada
  quando não há servidor X11 disponível (ex.: VM headless acessada por `vagrant ssh`).

## Topologia

```
[servidor] --(acesso A)-- R1 ==(NÚCLEO / gargalo)== R2 --(acesso B)-- [cliente]
```

- `servidor` e `cliente`: nós finais em **redes de acesso** distintas.
- `R1`, `R2`: roteadores do **núcleo**.
- enlace `R1<->R2`: **gargalo** (banda + atraso configuráveis, sem perda).

| Tecnologia | Banda     | Atraso |
|------------|-----------|--------|
| `4G`       | 20 Mbps   | 50 ms  |
| `FIBRA`    | 100 Mbps  | 5 ms   |

## Pré-requisitos

- Container CORE rodando (ver `SETUP.md`, passo 3).
- Projeto copiado e compilado dentro do container em `/root/trabalho1-redes`
  (`SETUP.md`, passo 4).

## Como usar (dentro do container, como root)

Entre no container:

```bash
sudo docker exec -it core bash
cd /root/trabalho1-redes/core
```

### 1) Validar a rede (ping / traceroute / iperf)

```bash
/opt/core/venv/bin/python topologia_core.py --tech 4G --validar
```

Confirma que o RTT (ping) reflete ~2× o atraso do gargalo e que a vazão (iperf)
bate perto da banda configurada. Troque `--tech FIBRA` para a outra tecnologia.

### 2) Rodar o experimento completo

```bash
# 4G (20 Mbps / 50 ms), n = 15 repetições
/opt/core/venv/bin/python topologia_core.py --tech 4G --experimento --n 15

# Fibra (100 Mbps / 5 ms)
/opt/core/venv/bin/python topologia_core.py --tech FIBRA --experimento --n 15
```

Cada execução acumula os dados em `/root/trabalho1-redes/data/resultados.csv`.

### 3) Extrair e analisar

Fora do container (na VM):

```bash
sudo docker cp core:/root/trabalho1-redes/data/resultados.csv ./data/
pip3 install pandas matplotlib numpy scipy   # se necessário
python3 scripts/analyze.py data/resultados.csv
```

Gera `data/resumo.csv` e os gráficos PNG (barras/tempo, boxplot, CDF, vazão).

## Observações

- O script roda **como root** porque o CORE cria network namespaces.
- A opção `--validar` sobe um `iperf -s` temporário no nó servidor e o encerra ao fim.
- `--manter` deixa a sessão ativa para inspeção manual via
  `sudo docker exec -it core vcmd -c <node> -- bash`.
- Se a versão do CORE instalada reclamar da API (ex.: `Position`, `add_node`),
  o script tem *fallbacks*, mas confirme a versão com:
  `sudo docker exec core /opt/core/venv/bin/python -c "import core; print(core.__version__)"`
