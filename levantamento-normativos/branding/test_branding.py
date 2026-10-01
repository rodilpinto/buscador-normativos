# -*- coding: utf-8 -*-
"""Testes do branding: os tres arquivos de valores (tokens.json, tokens.css, config.toml)
dizem a mesma coisa, os contrastes citados no guia conferem, os arquivos citados existem e
os helpers do Streamlit desenham o que prometem. Viajam com a pasta: nao importam nada do app.

Rodar da pasta que CONTEM branding/:
    python -m pytest branding -q
"""
from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

import pytest

PASTA = Path(__file__).resolve().parent
TOKENS = json.loads((PASTA / "tokens.json").read_text(encoding="utf-8"))


def _valor(grupo: str, nome: str) -> str:
    return TOKENS[grupo][nome]["valor"].upper()


def _luminancia(hexa: str) -> float:
    canais = [int(hexa.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in canais]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def _contraste(a: str, b: str) -> float:
    la, lb = sorted((_luminancia(a), _luminancia(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def test_versao():
    import branding
    assert re.fullmatch(r"\d+\.\d+\.\d+", branding.__version__)


def test_tokens_css_repete_o_json():
    css = (PASTA / "tokens.css").read_text(encoding="utf-8")
    variaveis = {k: v.upper() for k, v in re.findall(r"--(cd-[\w-]+):\s*(#[0-9A-Fa-f]{6})", css)}
    esperado = {
        "cd-verde": _valor("marca", "verde-cd"), "cd-azul": _valor("marca", "azul-cd"),
        "cd-cinza": _valor("marca", "cinza-cd"), "cd-branco": _valor("marca", "branco-cd"),
        "cd-verde-acao": _valor("interface", "verde-acao"),
        "cd-verde-escuro": _valor("interface", "verde-escuro"),
        "cd-verde-tinta": _valor("interface", "verde-tinta"),
        "cd-texto": _valor("interface", "texto"), "cd-texto-suave": _valor("interface", "texto-suave"),
        "cd-borda": _valor("interface", "borda"), "cd-fundo": _valor("interface", "fundo"),
        "cd-erro": _valor("interface", "erro"),
    }
    assert variaveis == esperado


def test_tema_streamlit_repete_o_json():
    tema = tomllib.loads((PASTA / "streamlit_cd" / "config.toml").read_text(encoding="utf-8"))["theme"]
    assert tema["primaryColor"].upper() == _valor("interface", "verde-acao")
    assert tema["linkColor"].upper() == _valor("interface", "verde-acao")
    assert tema["backgroundColor"].upper() == _valor("interface", "fundo")
    assert tema["secondaryBackgroundColor"].upper() == _valor("interface", "verde-tinta")
    assert tema["textColor"].upper() == _valor("interface", "texto")
    assert tema["borderColor"].upper() == _valor("interface", "borda")
    assert tema["headingFont"] == TOKENS["tipografia"]["familia"]["valor"]


@pytest.mark.parametrize("grupo,nome,citado", [
    ("marca", "verde-cd", 2.85), ("marca", "azul-cd", 3.36), ("marca", "cinza-cd", 10.31),
    ("interface", "verde-acao", 5.25), ("interface", "verde-escuro", 10.39),
    ("interface", "texto-suave", 5.22), ("interface", "erro", 4.53),
])
def test_contraste_citado_no_guia_confere(grupo, nome, citado):
    """O guia cita o contraste de cada cor sobre branco (WCAG 2.x); a conta tem de bater."""
    assert _contraste(_valor(grupo, nome), "#FFFFFF") == pytest.approx(citado, abs=0.01)


def test_cores_de_texto_passam_no_wcag_aa():
    for nome in ("verde-acao", "verde-escuro", "texto", "texto-suave", "erro"):
        assert _contraste(_valor("interface", nome), "#FFFFFF") >= 4.5, nome


def test_arquivos_citados_existem():
    citados = [v["arquivo"] for v in TOKENS["logo"].values() if isinstance(v, dict) and "arquivo" in v]
    citados += ["assets/favicon/favicon-32x32.png", "assets/logos/camara-h2-filetada-branco.svg",
                "fonte/MIV_Camara_dos_Deputados_v4.00_dez2025.pdf"]
    faltando = [c for c in citados if not (PASTA / c).is_file()]
    assert faltando == []


def test_assinatura_sem_siglas():
    """MIV p.14: a assinatura de unidade nao usa siglas."""
    from branding.streamlit_cd import cd_brand
    for unidade in list(cd_brand.UNIDADES_PADRAO) + TOKENS["assinatura"]["unidades"]:
        assert not re.search(r"\b[A-Z]{3,}\b", unidade), unidade


@pytest.fixture
def st_dublado(monkeypatch):
    from branding.streamlit_cd import cd_brand
    chamadas = {"markdown": [], "config": []}
    monkeypatch.setattr(cd_brand.st, "markdown", lambda html, **k: chamadas["markdown"].append((html, k)))
    monkeypatch.setattr(cd_brand.st, "set_page_config", lambda **k: chamadas["config"].append(k))
    return cd_brand, chamadas


def test_configurar_pagina(st_dublado):
    cd_brand, chamadas = st_dublado
    cd_brand.configurar_pagina("Meu App")
    cfg = chamadas["config"][0]
    assert cfg["page_title"] == "Meu App | Câmara dos Deputados"
    assert Path(cfg["page_icon"]).is_file()
    assert cfg["layout"] == "wide"


def test_cabecalho_e_rodape_embutem_o_logo(st_dublado):
    cd_brand, chamadas = st_dublado
    cd_brand.cabecalho("Meu App", "Descrição")
    cd_brand.rodape()
    cab, rod = chamadas["markdown"][0], chamadas["markdown"][1]
    assert "Meu App" in cab[0] and "Descrição" in cab[0] and cab[1] == {"unsafe_allow_html": True}
    assert "data:image/svg+xml;base64," in cab[0] and "data:image/svg+xml;base64," in rod[0]
    assert "Secretaria de Controle Interno<br>Núcleo de Auditoria de TI" in rod[0]
