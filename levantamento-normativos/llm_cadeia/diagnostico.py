"""Diagnostico: qual chave/modelo configurado responde AGORA.

    python -m llm_cadeia            (da pasta que contem llm_cadeia/)

Faz UMA chamada minima ("Responda só: ok") a cada modelo de cada provedor configurado,
ignorando as esperas, e imprime uma tabela. Gasta 1 requisicao por modelo — use ao
configurar chaves num servidor novo, nao em loop. Nunca imprime chave.
"""

from __future__ import annotations

from . import nucleo


def diagnosticar() -> list[tuple[str, str, str]]:
    """Return [(provedor, modelo, "ok" | motivo)] for every configured provider/model."""
    linhas = []
    for p in nucleo._provedores:
        transporte = nucleo._gerar_openai if p["tipo"] == "openai" else nucleo._gerar_gemini
        for modelo in p["modelos"]:
            try:
                texto = transporte(p, modelo, "Responda só: ok", None, False, 0.0, 16)
                estado = "ok" if texto else "resposta vazia"
            except Exception as e:
                estado = nucleo._sem_chave(" ".join(str(e).split())[:100], p)
            linhas.append((p["nome"], modelo, estado))
    return linhas


def main() -> int:
    from . import __version__
    print(f"llm_cadeia {__version__}")
    linhas = diagnosticar()
    if not linhas:
        print("Nenhum provedor configurado (veja README.md: segredos).")
        return 1
    largura_p = max(len(l[0]) for l in linhas)
    largura_m = max(len(l[1]) for l in linhas)
    for prov, modelo, estado in linhas:
        print(f"{prov:<{largura_p}}  {modelo:<{largura_m}}  {estado}")
    return 0 if any(l[2] == "ok" for l in linhas) else 1
