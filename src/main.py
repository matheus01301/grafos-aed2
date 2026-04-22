"""
Ponto de entrada do projeto.

Uso:
    python main.py                      # roda modo sentenca (padrão)
    python main.py --modo paragrafo     # roda modo parágrafo
    python main.py --modo k_chars       # roda modo k-caracteres (padrão k=500)
    python main.py --modo todos         # roda os três modos para comparação
    python main.py --k-chars 1000       # define k=1000 caracteres
    python main.py --peso-minimo 2      # filtra arestas com peso < 2
    python main.py --sem-comunidades    # desliga detecção de comunidades (Louvain)
"""

import argparse
import os
import sys

from extract_text import extrair_todos
from ner_graph import carregar_modelo, construir_grafo
from analysis import (
    calcular_metricas,
    detectar_comunidades,
    formatar_metricas,
    salvar_comunidades_csv,
    salvar_metricas,
    salvar_metricas_csv,
    visualizar_grafo,
)
from figures import gerar_figuras_comparativas

# Caminhos relativos ao diretório src/
RAIZ = os.path.dirname(os.path.abspath(__file__))
PASTA_PDFS    = os.path.join(RAIZ, "..", "data",    "pdfs")
PASTA_TEXTOS  = os.path.join(RAIZ, "..", "data",    "textos")
PASTA_GRAFOS  = os.path.join(RAIZ, "..", "outputs", "grafos")
PASTA_METRICAS = os.path.join(RAIZ, "..", "outputs", "metricas")
PASTA_FIGURAS = os.path.join(RAIZ, "..", "outputs", "figuras")


def processar(
    modo: str,
    nlp,
    peso_minimo: int = 1,
    com_comunidades: bool = True,
    k: int = 500,
) -> dict:
    """Executa o pipeline completo para um modo. Retorna {"G", "metricas", "comunidades"}."""
    nome_arquivo = f"k{k}" if modo == "k_chars" else modo
    label        = f"k={k} chars" if modo == "k_chars" else modo

    print(f"\n{'='*60}")
    print(f"  MODO: {label.upper()}")
    print(f"{'='*60}\n")

    G = construir_grafo(PASTA_TEXTOS, nlp, modo=modo, peso_minimo=peso_minimo, k=k)

    if G.number_of_nodes() == 0:
        print(f"\n[AVISO] Nenhum resultado para o modo '{label}'. Pulando.\n")
        return {}

    metricas = calcular_metricas(G)

    comunidades = None
    if com_comunidades:
        print("[INFO] Detectando comunidades (Louvain)...")
        comunidades = detectar_comunidades(G)
        print(
            f"[INFO] {comunidades['num_comunidades']} comunidades, "
            f"modularidade={comunidades['modularidade']}"
        )

    print()
    print(formatar_metricas(metricas, label, comunidades))
    print()

    caminho_txt = salvar_metricas(metricas, nome_arquivo, PASTA_METRICAS, comunidades)
    caminho_csv = salvar_metricas_csv(metricas, nome_arquivo, PASTA_METRICAS, comunidades)
    print(f"[INFO] Métricas salvas: {caminho_txt}")
    print(f"[INFO] Métricas CSV:    {caminho_csv}")

    if comunidades:
        caminho_com = salvar_comunidades_csv(G, comunidades, nome_arquivo, PASTA_METRICAS)
        if caminho_com:
            print(f"[INFO] Comunidades CSV: {caminho_com}")

    visualizar_grafo(G, nome_arquivo, PASTA_GRAFOS, comunidades=comunidades)

    return {"G": G, "metricas": metricas, "comunidades": comunidades}


def main():
    parser = argparse.ArgumentParser(
        description="Pipeline de NER + Grafo de Coocorrência para TCCs"
    )
    parser.add_argument(
        "--modo",
        choices=["sentenca", "paragrafo", "k_chars", "todos"],
        default="sentenca",
        help="Modo de coocorrência (padrão: sentenca)",
    )
    parser.add_argument(
        "--k-chars",
        type=int,
        default=500,
        dest="k_chars",
        help="Tamanho da janela em caracteres para modo k_chars (padrão: 500)",
    )
    parser.add_argument(
        "--peso-minimo",
        type=int,
        default=1,
        help="Peso mínimo para manter uma aresta (padrão: 1)",
    )
    parser.add_argument(
        "--sem-comunidades",
        action="store_true",
        help="Desativa a detecção de comunidades (Louvain)",
    )
    args = parser.parse_args()
    com_comunidades = not args.sem_comunidades

    print("=" * 60)
    print("  PIPELINE: PDF → Texto → NER → Grafo → Métricas")
    print("=" * 60)

    print("\n--- ETAPA 1: Extração de texto ---\n")
    extrair_todos(PASTA_PDFS, PASTA_TEXTOS)

    from utils import listar_arquivos
    if not listar_arquivos(PASTA_TEXTOS, ".txt"):
        print("\n[ERRO] Nenhum texto disponível para processar.")
        print("       Coloque PDFs em: data/pdfs/")
        sys.exit(1)

    print("\n--- ETAPA 2: Carregando modelo NER ---\n")
    nlp = carregar_modelo()

    print("\n--- ETAPA 3: NER + Grafo + Métricas ---")
    resultados: dict = {}

    if args.modo == "todos":
        r = processar("sentenca", nlp, args.peso_minimo, com_comunidades)
        if r: resultados["sentenca"] = r

        r = processar("paragrafo", nlp, args.peso_minimo, com_comunidades)
        if r: resultados["paragrafo"] = r

        r = processar("k_chars", nlp, args.peso_minimo, com_comunidades, args.k_chars)
        if r: resultados[f"k{args.k_chars}"] = r

    elif args.modo == "k_chars":
        r = processar("k_chars", nlp, args.peso_minimo, com_comunidades, args.k_chars)
        if r: resultados[f"k{args.k_chars}"] = r

    else:
        r = processar(args.modo, nlp, args.peso_minimo, com_comunidades)
        if r: resultados[args.modo] = r

    if resultados:
        print("\n--- ETAPA 4: Figuras ---\n")
        figuras = gerar_figuras_comparativas(resultados, PASTA_FIGURAS)
        for f in figuras:
            print(f"[INFO] Figura: {f}")

    print("\n" + "=" * 60)
    print("  CONCLUÍDO!")
    print("  Resultados em: outputs/grafos/, outputs/metricas/, outputs/figuras/")
    print("=" * 60)


if __name__ == "__main__":
    main()
