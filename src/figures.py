"""Figuras comparativas entre modos de segmentação."""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx

from utils import garantir_pasta


def gerar_figuras_comparativas(resultados: dict, pasta_saida: str) -> list[str]:
    """
    Gera figuras comparativas entre modos de segmentação.

    resultados: {label: {"G": nx.Graph, "metricas": dict, "comunidades": dict}}
    """
    garantir_pasta(pasta_saida)
    arquivos = []

    for fn in [
        _figura_top_entidades,
        _figura_distribuicao_graus,
        _figura_distribuicao_comunidades,
        _figura_metricas_comparativas,
    ]:
        caminho = fn(resultados, pasta_saida)
        if caminho:
            arquivos.append(caminho)

    return arquivos


def _figura_metricas_comparativas(resultados: dict, pasta_saida: str) -> str | None:
    """Bar charts lado a lado com as principais métricas por modo."""
    modos = list(resultados.keys())
    if len(modos) < 2:
        return None

    campos = [
        ("num_nos",                 "Nós"),
        ("num_arestas",             "Arestas"),
        ("densidade",               "Densidade"),
        ("clustering_medio",        "Clustering Médio"),
        ("componentes_conectados",  "Componentes"),
        ("num_comunidades",         "Comunidades"),
        ("modularidade",            "Modularidade"),
    ]

    fig, axes = plt.subplots(2, 4, figsize=(18, 8))
    axes = axes.flatten()
    colors = [plt.get_cmap("tab10")(i) for i in range(len(modos))]

    for idx, (chave, titulo) in enumerate(campos):
        ax = axes[idx]
        valores = []
        for modo in modos:
            m = resultados[modo]["metricas"]
            c = resultados[modo].get("comunidades") or {}
            if chave in m:
                valores.append(m[chave])
            elif chave in c:
                valores.append(c[chave])
            else:
                valores.append(0)

        bars = ax.bar(modos, valores, color=colors)
        ax.set_title(titulo, fontsize=10, fontweight="bold")
        ax.tick_params(axis="x", labelsize=8)
        for bar, val in zip(bars, valores):
            fmt = f"{val:.4f}" if isinstance(val, float) else str(val)
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                fmt,
                ha="center", va="bottom", fontsize=7,
            )

    axes[-1].axis("off")
    fig.suptitle("Comparação de Métricas — Modos de Segmentação", fontsize=13, fontweight="bold")
    plt.tight_layout()

    caminho = os.path.join(pasta_saida, "comparacao_metricas.png")
    fig.savefig(caminho, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[INFO] Figura salva: {caminho}")
    return caminho


def _figura_distribuicao_graus(resultados: dict, pasta_saida: str) -> str | None:
    """Distribuição de graus em escala log-log para cada modo."""
    modos = list(resultados.keys())
    if not modos:
        return None

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = [plt.get_cmap("tab10")(i) for i in range(len(modos))]

    for modo, color in zip(modos, colors):
        G = resultados[modo]["G"]
        if G.number_of_nodes() == 0:
            continue
        contagem: dict[int, int] = {}
        for _, d in G.degree():
            contagem[d] = contagem.get(d, 0) + 1
        xs = sorted(contagem)
        ys = [contagem[x] for x in xs]
        ax.plot(xs, ys, "o-", label=modo, color=color, markersize=3, linewidth=1.5, alpha=0.85)

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Grau (escala log)", fontsize=11)
    ax.set_ylabel("Frequência (escala log)", fontsize=11)
    ax.set_title("Distribuição de Graus por Modo de Segmentação", fontsize=13, fontweight="bold")
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    caminho = os.path.join(pasta_saida, "distribuicao_graus.png")
    fig.savefig(caminho, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[INFO] Figura salva: {caminho}")
    return caminho


def _figura_top_entidades(resultados: dict, pasta_saida: str) -> str | None:
    """Top 15 entidades por grau para cada modo (barras horizontais)."""
    modos = list(resultados.keys())
    if not modos:
        return None

    n = len(modos)
    fig, axes = plt.subplots(1, n, figsize=(7 * n, 6))
    if n == 1:
        axes = [axes]
    colors = [plt.get_cmap("tab10")(i) for i in range(n)]

    for ax, modo, color in zip(axes, modos, colors):
        G = resultados[modo]["G"]
        if G.number_of_nodes() == 0:
            ax.text(0.5, 0.5, "Grafo vazio", ha="center", va="center", transform=ax.transAxes)
            ax.set_title(modo)
            continue

        top = sorted(G.degree(), key=lambda x: x[1], reverse=True)[:15]
        nomes = [t[0][:28] for t in top]
        graus = [t[1] for t in top]

        ax.barh(range(len(nomes)), graus[::-1], color=color, alpha=0.85)
        ax.set_yticks(range(len(nomes)))
        ax.set_yticklabels(nomes[::-1], fontsize=8)
        ax.set_xlabel("Grau", fontsize=10)
        ax.set_title(f"Top 15 Entidades — {modo}", fontsize=10, fontweight="bold")
        ax.grid(axis="x", alpha=0.3)

    plt.tight_layout()
    caminho = os.path.join(pasta_saida, "top_entidades.png")
    fig.savefig(caminho, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[INFO] Figura salva: {caminho}")
    return caminho


def _figura_distribuicao_comunidades(resultados: dict, pasta_saida: str) -> str | None:
    """Tamanho das comunidades (top 20) para cada modo."""
    modos = list(resultados.keys())
    if not modos:
        return None

    n = len(modos)
    fig, axes = plt.subplots(1, n, figsize=(6 * n, 5))
    if n == 1:
        axes = [axes]
    colors = [plt.get_cmap("tab10")(i) for i in range(n)]

    for ax, modo, color in zip(axes, modos, colors):
        com = resultados[modo].get("comunidades") or {}
        tamanhos = sorted(com.get("tamanhos", []), reverse=True)

        if not tamanhos:
            ax.text(0.5, 0.5, "Sem comunidades", ha="center", va="center", transform=ax.transAxes)
            ax.set_title(modo)
            continue

        top = tamanhos[:20]
        ax.bar(range(1, len(top) + 1), top, color=color, alpha=0.85)
        ax.set_xlabel("Rank da Comunidade", fontsize=10)
        ax.set_ylabel("Tamanho (nós)", fontsize=10)
        ax.set_title(
            f"Comunidades — {modo}\n"
            f"total={com.get('num_comunidades', '?')}  mod={com.get('modularidade', 0):.3f}",
            fontsize=9, fontweight="bold",
        )
        ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    caminho = os.path.join(pasta_saida, "distribuicao_comunidades.png")
    fig.savefig(caminho, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[INFO] Figura salva: {caminho}")
    return caminho
