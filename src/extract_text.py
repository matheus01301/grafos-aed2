"""Extração de texto de PDFs usando pdfplumber."""

import os

import pdfplumber

from utils import limpar_texto, listar_arquivos, salvar_texto


def extrair_texto_pdf(caminho_pdf: str) -> str:
    """Extrai todo o texto de um PDF. Retorna string vazia se falhar."""
    texto_paginas = []
    try:
        with pdfplumber.open(caminho_pdf) as pdf:
            for pagina in pdf.pages:
                texto = pagina.extract_text()
                if texto:
                    texto_paginas.append(texto)
    except Exception as e:
        print(f"  [ERRO] Falha ao ler '{caminho_pdf}': {e}")
        return ""

    return "\n\n".join(texto_paginas)


def extrair_todos(pasta_pdfs: str, pasta_saida: str) -> list[str]:
    """
    Lê todos os PDFs da pasta, extrai texto e salva como .txt.
    Retorna lista de caminhos dos .txt gerados.
    """
    pdfs = listar_arquivos(pasta_pdfs, ".pdf")

    if not pdfs:
        print(f"[AVISO] Nenhum PDF encontrado em '{pasta_pdfs}'.")
        print("        Coloque seus PDFs nessa pasta e rode novamente.")
        return []

    print(f"[INFO] {len(pdfs)} PDF(s) encontrado(s) em '{pasta_pdfs}'.")
    arquivos_gerados = []

    for pdf_path in pdfs:
        nome = os.path.splitext(os.path.basename(pdf_path))[0]
        print(f"  Extraindo: {nome}.pdf ... ", end="")

        texto = extrair_texto_pdf(pdf_path)

        if not texto.strip():
            print("SEM TEXTO (PDF escaneado ou vazio).")
            continue

        texto = limpar_texto(texto)
        caminho_txt = os.path.join(pasta_saida, f"{nome}.txt")
        salvar_texto(caminho_txt, texto)
        arquivos_gerados.append(caminho_txt)
        print(f"OK ({len(texto)} caracteres)")

    print(f"[INFO] {len(arquivos_gerados)} texto(s) extraído(s) com sucesso.")
    return arquivos_gerados


if __name__ == "__main__":
    extrair_todos("../data/pdfs", "../data/textos")
