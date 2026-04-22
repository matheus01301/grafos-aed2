# Grafos de Coocorrência de Entidades Nomeadas em TCCs

**Matheus Rodrigues Marinho**  
Disciplina de Algoritmos e Estruturas de Dados II — Engenharia de Computação

---

## Sobre o projeto

Este trabalho analisa trabalhos de conclusão de curso (TCCs) da área de Engenharia de Computação por meio de grafos de coocorrência de entidades nomeadas (NER). A ideia é aplicar reconhecimento de entidades sobre os textos dos TCCs e construir um grafo onde cada nó é uma entidade (pessoa, organização, local, tecnologia etc.) e cada aresta representa quantas vezes duas entidades aparecem juntas numa mesma janela de contexto.

Três estratégias de segmentação são comparadas:

| Modo | Janela de contexto |
|------|--------------------|
| `sentenca` | cada sentença do texto |
| `paragrafo` | cada parágrafo (blocos separados por linha em branco) |
| `k_chars` | janelas fixas de *k* caracteres (padrão: 500) |

Para cada modo são calculadas métricas de rede (densidade, clustering, diâmetro, componentes) e comunidades via algoritmo de Louvain. Ao rodar `--modo todos`, o pipeline também gera figuras comparativas entre os três modos.

## Requisitos

- Python 3.10+
- Modelo spaCy para português: `pt_core_news_lg`

## Instalação

```bash
python -m venv venv
# Windows:
.\venv\Scripts\Activate.ps1
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
python -m spacy download pt_core_news_lg
```

## Uso

Coloque os PDFs dos TCCs em `data/pdfs/` e execute a partir da pasta `src/`:

```bash
cd src

# Apenas modo sentença
python main.py

# Modo parágrafo
python main.py --modo paragrafo

# Modo k-caracteres (janela de 500 chars por padrão)
python main.py --modo k_chars

# Janela personalizada de 1000 caracteres
python main.py --modo k_chars --k-chars 1000

# Todos os modos + figuras comparativas
python main.py --modo todos

# Filtrar arestas com poucos coocorrências (remove ruído)
python main.py --modo todos --peso-minimo 2
```

## Saídas

```
outputs/
├── grafos/        ← grafo_sentenca.png, grafo_paragrafo.png, grafo_k500.png
├── metricas/      ← metricas_{modo}.txt/.csv, comunidades_{modo}.csv
└── figuras/       ← comparacao_metricas.png, distribuicao_graus.png,
                      top_entidades.png, distribuicao_comunidades.png
```

## Estrutura do código

```
src/
├── main.py          ← orquestra o pipeline completo
├── extract_text.py  ← extração de texto dos PDFs (pdfplumber)
├── ner_graph.py     ← NER com spaCy + construção do grafo
├── analysis.py      ← métricas, comunidades Louvain, visualização do grafo
├── figures.py       ← figuras comparativas entre modos
└── utils.py         ← funções auxiliares de I/O
```

## Métricas calculadas

- Número de nós e arestas
- Densidade
- Número de componentes conectados e tamanho/diâmetro do maior
- Clustering médio
- Detecção de comunidades (Louvain) com modularidade
