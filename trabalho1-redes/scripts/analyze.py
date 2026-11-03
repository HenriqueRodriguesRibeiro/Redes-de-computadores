#!/usr/bin/env python3
"""analyze.py - Estatistica e graficos do experimento.
Uso: python3 analyze.py data/resultados.csv
Requer: pandas, matplotlib, numpy, scipy"""
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats


def intervalo_confianca(serie, conf=0.95):
    n = len(serie)
    if n < 2:
        return 0.0
    sem = stats.sem(serie)
    return sem * stats.t.ppf((1 + conf) / 2.0, n - 1)


def main(csv_path):
    df = pd.read_csv(csv_path)
    partes = df["tag"].str.split(";", expand=True)
    df["tecnologia"] = partes[1]
    df["arquivo"] = partes[2]
    df["concorrencia"] = partes[3].str.replace("conc=", "", regex=False).astype(int)
    ok = df[df["status"].isin([200, 201])].copy()

    resumo = (ok.groupby(["tecnologia", "operacao", "arquivo", "concorrencia"])
              .agg(tempo_medio=("tempo_s", "mean"),
                   tempo_mediana=("tempo_s", "median"),
                   tempo_std=("tempo_s", "std"),
                   vazao_media=("vazao_mbps", "mean"),
                   n=("tempo_s", "count")).reset_index())
    ic = (ok.groupby(["tecnologia", "operacao", "arquivo", "concorrencia"])["tempo_s"]
          .apply(intervalo_confianca).reset_index(name="tempo_ic95"))
    resumo = resumo.merge(ic, on=["tecnologia", "operacao", "arquivo", "concorrencia"])
    print(resumo.to_string(index=False))
    resumo.to_csv("data/resumo.csv", index=False)

    for arq in ok["arquivo"].unique():
        sub = resumo[resumo["arquivo"] == arq]
        fig, ax = plt.subplots()
        for (tec, oper), g in sub.groupby(["tecnologia", "operacao"]):
            ax.errorbar(g["concorrencia"], g["tempo_medio"], yerr=g["tempo_ic95"],
                        marker="o", capsize=4, label=f"{tec}-{oper}")
        ax.set_xlabel("Clientes concorrentes"); ax.set_ylabel("Tempo medio (s)")
        ax.set_title(f"Tempo de resposta - {arq}"); ax.legend()
        fig.savefig(f"data/tempo_{arq}.png", dpi=120, bbox_inches="tight")

    fig, ax = plt.subplots()
    grupos, rotulos = [], []
    for (tec, oper), g in ok.groupby(["tecnologia", "operacao"]):
        grupos.append(g["tempo_s"].values); rotulos.append(f"{tec}-{oper}")
    ax.boxplot(grupos, labels=rotulos)
    ax.set_ylabel("Tempo de resposta (s)"); ax.set_title("Distribuicao do tempo")
    plt.xticks(rotation=30)
    fig.savefig("data/boxplot_tempo.png", dpi=120, bbox_inches="tight")

    fig, ax = plt.subplots()
    for (tec, oper), g in ok.groupby(["tecnologia", "operacao"]):
        x = np.sort(g["tempo_s"].values); yv = np.arange(1, len(x) + 1) / len(x)
        ax.plot(x, yv, marker=".", label=f"{tec}-{oper}")
    ax.set_xlabel("Tempo de resposta (s)"); ax.set_ylabel("P(X <= x)")
    ax.set_title("CDF do tempo de resposta"); ax.legend()
    fig.savefig("data/cdf_tempo.png", dpi=120, bbox_inches="tight")

    fig, ax = plt.subplots()
    for (tec, oper), g in resumo.groupby(["tecnologia", "operacao"]):
        gg = g.groupby("concorrencia")["vazao_media"].mean().reset_index()
        ax.plot(gg["concorrencia"], gg["vazao_media"], marker="s", label=f"{tec}-{oper}")
    ax.set_xlabel("Clientes concorrentes"); ax.set_ylabel("Vazao media (Mbps)")
    ax.set_title("Vazao x concorrencia"); ax.legend()
    fig.savefig("data/vazao_concorrencia.png", dpi=120, bbox_inches="tight")

    print("Analise concluida. Veja PNGs e resumo.csv em data/.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 analyze.py <arquivo.csv>"); sys.exit(1)
    main(sys.argv[1])
