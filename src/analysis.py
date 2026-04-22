"""Análise de métricas do grafo e visualização."""

import os

import matplotlib
matplotlib.use("Agg")  # Backend sem GUI — funciona em qualquer ambiente
import matplotlib.pyplot as plt
import networkx as nx

from utils import garantir_pasta, salvar_texto


def calcular_metricas(G: nx.Graph) -> dict:
    """Calcula métricas do grafo e retorna como dicionário."""
    if G.number_of_nodes() == 0:
        return {"erro": "Grafo vazio, sem métricas para calcular."}

    metricas = {}
    metricas["num_nos"] = G.number_of_nodes()
    metricas["num_arestas"] = G.number_of_edges()
    metricas["densidade"] = round(nx.density(G), 6)

    componentes = list(nx.connected_components(G))
    metricas["componentes_conectados"] = len(componentes)

    # Top 10 nós por grau
    graus = sorted(G.degree(), key=lambda x: x[1], reverse=True)
    metricas["top10_grau"] = graus[:10]

    # Clustering médio
    metricas["clustering_medio"] = round(nx.average_clustering(G), 6)

    # Diâmetro do maior componente
    if componentes:
        maior = max(componentes, key=len)
        subgrafo = G.subgraph(maior)
        if len(maior) > 1:
            metricas["diametro_maior_componente"] = nx.diameter(subgrafo)
        else:
            metricas["diametro_maior_componente"] = 0
        metricas["tamanho_maior_componente"] = len(maior)

    return metricas


def detectar_comunidades(G: nx.Graph, seed: int = 42) -> dict:
    """
    Detecta comunidades com o algoritmo de Louvain (NetworkX nativo).

    Usa o atributo 'weight' das arestas (coocorrência) como peso na modularidade.

    Retorna dict com:
        - comunidades: list[set[str]]  — uma lista por comunidade
        - mapa: dict[str, int]         — nó → id da comunidade
        - num_comunidades: int
        - modularidade: float
        - tamanhos: list[int]          — tamanho de cada comunidade (ordenado desc)
        - top_por_comunidade: list[list[tuple[str, int]]]
              top 5 nós (por grau) das 5 maiores comunidades
    """
    if G.number_of_nodes() == 0:
        return {
            "comunidades": [],
            "mapa": {},
            "num_comunidades": 0,
            "modularidade": 0.0,
            "tamanhos": [],
            "top_por_comunidade": [],
        }

    comunidades = nx.community.louvain_communities(G, weight="weight", seed=seed)
    # Ordena por tamanho (maior primeiro) para IDs estáveis por relevância
    comunidades = sorted(comunidades, key=len, reverse=True)

    mapa = {}
    for idx, com in enumerate(comunidades):
        for no in com:
            mapa[no] = idx

    modularidade = nx.community.modularity(G, comunidades, weight="weight")
    tamanhos = [len(c) for c in comunidades]

    # Top 5 nós (por grau) das 5 maiores comunidades
    graus = dict(G.degree())
    top_por_comunidade = []
    for com in comunidades[:5]:
        nos_ordenados = sorted(com, key=lambda n: graus.get(n, 0), reverse=True)
        top_por_comunidade.append([(n, graus.get(n, 0)) for n in nos_ordenados[:5]])

    return {
        "comunidades": comunidades,
        "mapa": mapa,
        "num_comunidades": len(comunidades),
        "modularidade": round(modularidade, 6),
        "tamanhos": tamanhos,
        "top_por_comunidade": top_por_comunidade,
    }


def formatar_metricas(metricas: dict, modo: str, comunidades: dict | None = None) -> str:
    """Formata métricas em texto legível.

    Se `comunidades` for fornecido (resultado de detectar_comunidades),
    inclui modularidade e resumo das maiores comunidades.
    """
    if "erro" in metricas:
        return metricas["erro"]

    linhas = [
        f"=== Métricas do Grafo (modo: {modo}) ===",
        f"Nós:                        {metricas['num_nos']}",
        f"Arestas:                    {metricas['num_arestas']}",
        f"Densidade:                  {metricas['densidade']}",
        f"Componentes conectados:     {metricas['componentes_conectados']}",
        f"Tamanho maior componente:   {metricas.get('tamanho_maior_componente', '-')}",
        f"Diâmetro maior componente:  {metricas.get('diametro_maior_componente', '-')}",
        f"Clustering médio:           {metricas['clustering_medio']}",
    ]

    if comunidades and comunidades.get("num_comunidades", 0) > 0:
        linhas += [
            f"Comunidades (Louvain):      {comunidades['num_comunidades']}",
            f"Modularidade:               {comunidades['modularidade']}",
            f"Tamanhos (5 maiores):       {comunidades['tamanhos'][:5]}",
        ]

    linhas += ["", "Top 10 nós por grau:"]
    for nome, grau in metricas["top10_grau"]:
        linhas.append(f"  {nome:40s} grau={grau}")

    if comunidades and comunidades.get("top_por_comunidade"):
        linhas += ["", "Top 5 entidades das 5 maiores comunidades:"]
        for idx, top in enumerate(comunidades["top_por_comunidade"]):
            tamanho = comunidades["tamanhos"][idx]
            linhas.append(f"  Comunidade {idx} (tam={tamanho}):")
            for nome, grau in top:
                linhas.append(f"    {nome:38s} grau={grau}")

    return "\n".join(linhas)


def salvar_metricas(
    metricas: dict,
    modo: str,
    pasta_saida: str,
    comunidades: dict | None = None,
) -> str:
    """Salva métricas em arquivo .txt. Retorna caminho do arquivo."""
    garantir_pasta(pasta_saida)
    texto = formatar_metricas(metricas, modo, comunidades)
    caminho = os.path.join(pasta_saida, f"metricas_{modo}.txt")
    salvar_texto(caminho, texto)
    return caminho


def salvar_metricas_csv(
    metricas: dict,
    modo: str,
    pasta_saida: str,
    comunidades: dict | None = None,
) -> str:
    """Salva métricas básicas em CSV para comparação fácil."""
    garantir_pasta(pasta_saida)
    caminho = os.path.join(pasta_saida, f"metricas_{modo}.csv")

    if "erro" in metricas:
        salvar_texto(caminho, "erro\n" + metricas["erro"])
        return caminho

    linhas = ["metrica,valor"]
    for chave in ["num_nos", "num_arestas", "densidade", "componentes_conectados",
                  "tamanho_maior_componente", "diametro_maior_componente", "clustering_medio"]:
        linhas.append(f"{chave},{metricas.get(chave, '')}")

    if comunidades and comunidades.get("num_comunidades", 0) > 0:
        linhas.append(f"num_comunidades,{comunidades['num_comunidades']}")
        linhas.append(f"modularidade,{comunidades['modularidade']}")

    salvar_texto(caminho, "\n".join(linhas))
    return caminho


def salvar_comunidades_csv(
    G: nx.Graph,
    comunidades: dict,
    modo: str,
    pasta_saida: str,
) -> str | None:
    """Salva mapeamento entidade → comunidade em CSV (uma linha por nó)."""
    if not comunidades or comunidades.get("num_comunidades", 0) == 0:
        return None

    garantir_pasta(pasta_saida)
    caminho = os.path.join(pasta_saida, f"comunidades_{modo}.csv")

    graus = dict(G.degree())
    mapa = comunidades["mapa"]
    # Ordena por (comunidade asc, grau desc) para leitura fácil
    itens = sorted(mapa.items(), key=lambda kv: (kv[1], -graus.get(kv[0], 0)))

    linhas = ["entidade,comunidade,grau"]
    for no, com_id in itens:
        # Escapa vírgulas em nomes de entidades
        nome = no.replace('"', '""')
        if "," in nome:
            nome = f'"{nome}"'
        linhas.append(f"{nome},{com_id},{graus.get(no, 0)}")

    salvar_texto(caminho, "\n".join(linhas))
    return caminho


def visualizar_grafo(
    G: nx.Graph,
    modo: str,
    pasta_saida: str,
    top_n: int = 50,
    comunidades: dict | None = None,
) -> str | None:
    """
    Gera imagem do grafo e salva como PNG.

    Se o grafo tiver muitos nós, mostra apenas os top_n por grau
    para evitar imagem poluída.

    Se `comunidades` for fornecido (resultado de detectar_comunidades),
    os nós são coloridos pela comunidade do Louvain.

    Retorna caminho da imagem ou None se grafo vazio.
    """
    if G.number_of_nodes() == 0:
        print("[AVISO] Grafo vazio — imagem não gerada.")
        return None

    garantir_pasta(pasta_saida)

    # Se grafo muito grande, filtra top_n nós por grau
    if G.number_of_nodes() > top_n:
        nos_top = sorted(G.degree(), key=lambda x: x[1], reverse=True)[:top_n]
        nos_top = [n for n, _ in nos_top]
        G_vis = G.subgraph(nos_top).copy()
        titulo_extra = f" (top {top_n} nós)"
    else:
        G_vis = G
        titulo_extra = ""

    # Tamanho dos nós proporcional ao grau
    graus = dict(G_vis.degree())
    max_grau = max(graus.values()) if graus else 1
    tamanhos = [300 * (graus[n] / max_grau) + 50 for n in G_vis.nodes()]

    # Pesos das arestas para espessura
    pesos = [G_vis[u][v]["weight"] for u, v in G_vis.edges()]
    max_peso = max(pesos) if pesos else 1
    larguras = [3 * (p / max_peso) + 0.3 for p in pesos]

    # Cores: por comunidade (se disponível) ou cor única
    if comunidades and comunidades.get("mapa"):
        mapa = comunidades["mapa"]
        cmap = plt.get_cmap("tab20")
        # Normaliza pelos 20 slots do colormap — se houver mais comunidades, cores se repetem
        cores_nos = [cmap(mapa.get(n, 0) % 20) for n in G_vis.nodes()]
        # Conta comunidades realmente visíveis após o corte top_n
        coms_visiveis = sorted({mapa.get(n, 0) for n in G_vis.nodes()})
        titulo_extra += f" — {len(coms_visiveis)} comunidades visíveis"
    else:
        cores_nos = "steelblue"

    fig, ax = plt.subplots(figsize=(16, 12))
    pos = nx.spring_layout(G_vis, k=2, iterations=50, seed=42)

    nx.draw_networkx_edges(G_vis, pos, width=larguras, alpha=0.3, edge_color="gray", ax=ax)
    nx.draw_networkx_nodes(G_vis, pos, node_size=tamanhos, node_color=cores_nos, alpha=0.85, ax=ax)
    nx.draw_networkx_labels(G_vis, pos, font_size=7, font_weight="bold", ax=ax)

    titulo = f"Grafo de Coocorrência — modo: {modo}{titulo_extra}"
    if comunidades:
        titulo += f"\nModularidade={comunidades['modularidade']} | {comunidades['num_comunidades']} comunidades no grafo completo"
    ax.set_title(titulo, fontsize=13)
    ax.axis("off")
    plt.tight_layout()

    caminho = os.path.join(pasta_saida, f"grafo_{modo}.png")
    fig.savefig(caminho, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[INFO] Imagem salva: {caminho}")
    return caminho
