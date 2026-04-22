"""Funções auxiliares reutilizáveis."""

import os
import re


def garantir_pasta(caminho: str) -> None:
    """Cria o diretório se não existir."""
    os.makedirs(caminho, exist_ok=True)


def limpar_texto(texto: str) -> str:
    """Limpeza básica: remove excesso de espaços e quebras de linha."""
    # Colapsa múltiplas quebras de linha em duas (preserva parágrafos)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    # Remove espaços múltiplos dentro de uma linha
    texto = re.sub(r"[ \t]+", " ", texto)
    # Remove espaços no início/fim de cada linha
    linhas = [linha.strip() for linha in texto.split("\n")]
    return "\n".join(linhas)


def salvar_texto(caminho: str, conteudo: str) -> None:
    """Salva string em arquivo UTF-8."""
    garantir_pasta(os.path.dirname(caminho))
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(conteudo)


def listar_arquivos(pasta: str, extensao: str) -> list[str]:
    """Lista arquivos com determinada extensão em uma pasta."""
    if not os.path.isdir(pasta):
        return []
    return sorted(
        os.path.join(pasta, f)
        for f in os.listdir(pasta)
        if f.lower().endswith(extensao.lower())
    )
