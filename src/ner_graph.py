"""NER com spaCy e construção do grafo de coocorrência."""

import os
from itertools import combinations

import networkx as nx
import spacy

from utils import listar_arquivos

# Labels de entidades relevantes para TCCs em português
LABELS_RELEVANTES = {"PER", "ORG", "LOC", "MISC", "GPE", "NORP", "EVENT", "WORK_OF_ART"}


def carregar_modelo(nome_modelo: str = "pt_core_news_lg") -> spacy.language.Language:
    """Carrega o modelo do spaCy."""
    print(f"[INFO] Carregando modelo spaCy '{nome_modelo}'...")
    try:
        nlp = spacy.load(nome_modelo)
    except OSError:
        print(f"[ERRO] Modelo '{nome_modelo}' não encontrado.")
        print(f"       Rode: python -m spacy download {nome_modelo}")
        raise
    print("[INFO] Modelo carregado.")
    return nlp


def extrair_entidades_por_janela(
    texto: str,
    nlp: spacy.language.Language,
    modo: str = "sentenca",
    k: int = 500,
) -> list[list[str]]:
    """
    Processa o texto com spaCy e retorna listas de entidades por janela.

    modo:
        'sentenca'  -> cada sentença é uma janela
        'paragrafo' -> cada parágrafo (separado por \\n\\n) é uma janela
        'k_chars'   -> janelas fixas de k caracteres (sem sobreposição)
    """
    janelas_entidades = []

    if modo == "paragrafo":
        paragrafos = [p.strip() for p in texto.split("\n\n") if p.strip()]
        for paragrafo in paragrafos:
            doc = nlp(paragrafo)
            entidades = _coletar_entidades(doc)
            if entidades:
                janelas_entidades.append(entidades)
    elif modo == "k_chars":
        for inicio in range(0, len(texto), k):
            janela = texto[inicio : inicio + k]
            if not janela.strip():
                continue
            doc = nlp(janela)
            entidades = _coletar_entidades(doc)
            if entidades:
                janelas_entidades.append(entidades)
    else:  # sentenca
        doc = nlp(texto)
        for sent in doc.sents:
            entidades = _coletar_entidades(sent.as_doc())
            if entidades:
                janelas_entidades.append(entidades)

    return janelas_entidades


def _coletar_entidades(doc) -> list[str]:
    """Extrai entidades únicas relevantes de um doc do spaCy."""
    entidades = set()
    for ent in doc.ents:
        if ent.label_ in LABELS_RELEVANTES:
            nome = ent.text.strip()
            # Normalização leve: primeira letra maiúscula
            if len(nome) >= 2:
                entidades.add(nome.title())
    return sorted(entidades)


def construir_grafo(
    pasta_textos: str,
    nlp: spacy.language.Language,
    modo: str = "sentenca",
    peso_minimo: int = 1,
    k: int = 500,
) -> nx.Graph:
    """
    Constrói grafo de coocorrência a partir dos textos.

    Parâmetros:
        pasta_textos: pasta com arquivos .txt
        nlp: modelo spaCy carregado
        modo: 'sentenca' ou 'paragrafo'
        peso_minimo: peso mínimo para manter uma aresta (filtro de ruído)

    Retorna:
        networkx.Graph com pesos nas arestas
    """
    arquivos = listar_arquivos(pasta_textos, ".txt")

    if not arquivos:
        print(f"[AVISO] Nenhum .txt encontrado em '{pasta_textos}'.")
        return nx.Graph()

    print(f"[INFO] Processando {len(arquivos)} texto(s) no modo '{modo}'...")
    G = nx.Graph()

    for arq in arquivos:
        nome = os.path.basename(arq)
        print(f"  NER: {nome} ... ", end="")

        with open(arq, "r", encoding="utf-8") as f:
            texto = f.read()

        janelas = extrair_entidades_por_janela(texto, nlp, modo, k)
        total_entidades = sum(len(j) for j in janelas)
        print(f"{len(janelas)} janelas, {total_entidades} entidades")

        # Gera pares de coocorrência dentro de cada janela
        for entidades in janelas:
            for e1, e2 in combinations(entidades, 2):
                if G.has_edge(e1, e2):
                    G[e1][e2]["weight"] += 1
                else:
                    G.add_edge(e1, e2, weight=1)

    # Filtra arestas por peso mínimo
    if peso_minimo > 1:
        arestas_remover = [
            (u, v) for u, v, d in G.edges(data=True) if d["weight"] < peso_minimo
        ]
        G.remove_edges_from(arestas_remover)
        # Remove nós isolados após filtro
        nos_isolados = list(nx.isolates(G))
        G.remove_nodes_from(nos_isolados)
        print(f"[INFO] Filtro peso>={peso_minimo}: removidas {len(arestas_remover)} arestas, {len(nos_isolados)} nós isolados.")

    total_nos = G.number_of_nodes()
    total_arestas = G.number_of_edges()
    print(f"[INFO] Grafo construído: {total_nos} nós, {total_arestas} arestas.")

    if total_nos == 0:
        print("[AVISO] Grafo vazio — nenhuma entidade encontrada.")
        print("        Verifique se os PDFs contêm texto legível.")

    return G
