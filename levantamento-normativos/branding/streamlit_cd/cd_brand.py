"""Identidade visual Camara dos Deputados para apps Streamlit.

Uso:
    from branding.streamlit_cd import cd_brand

    cd_brand.configurar_pagina("Checklist de Conformidade")   # antes de qualquer st.*
    cd_brand.cabecalho("Checklist de Conformidade", "Normativos em checklists de auditoria")
    ...
    cd_brand.rodape()

Regras aplicadas: branding/README.md.
"""

from __future__ import annotations

import base64
from functools import lru_cache
from pathlib import Path

import streamlit as st

_ASSETS = Path(__file__).resolve().parent.parent / "assets"

UNIDADES_PADRAO = ("Secretaria de Controle Interno", "Núcleo de Auditoria de TI")


@lru_cache(maxsize=None)
def _svg_data_uri(nome: str) -> str:
    dados = (_ASSETS / "logos" / nome).read_bytes()
    return "data:image/svg+xml;base64," + base64.b64encode(dados).decode("ascii")


def configurar_pagina(titulo: str, layout: str = "wide") -> None:
    st.set_page_config(
        page_title=f"{titulo} | Câmara dos Deputados",
        page_icon=str(_ASSETS / "favicon" / "favicon-32x32.png"),
        layout=layout,
    )


def cabecalho(titulo: str, subtitulo: str = "") -> None:
    logo = _svg_data_uri("camara-h2-filetada-branco.svg")
    sub = f'<p class="cd-cab__sub">{subtitulo}</p>' if subtitulo else ""
    st.markdown(
        f"""
        <style>
          .cd-cab {{ background:#004A2F; color:#FFFFFF; border-radius:0.375rem;
                    padding:1.1rem 1.5rem; display:flex; align-items:center;
                    justify-content:space-between; gap:1.5rem; margin-bottom:1.25rem;
                    border-bottom:4px solid #00B142; }}
          .cd-cab__titulo {{ font-size:1.6rem; font-weight:600; margin:0; line-height:1.2;
                             color:#FFFFFF; }}
          .cd-cab__sub {{ margin:0.25rem 0 0 0; font-size:0.95rem; opacity:0.9; }}
          .cd-cab__logo {{ height:44px; min-height:20px; flex-shrink:0; }}
          @media (max-width: 640px) {{ .cd-cab__logo {{ display:none; }} }}
        </style>
        <div class="cd-cab">
          <div><p class="cd-cab__titulo">{titulo}</p>{sub}</div>
          <img class="cd-cab__logo" src="{logo}" alt="Câmara dos Deputados">
        </div>
        """,
        unsafe_allow_html=True,
    )


def rodape(unidades: tuple[str, ...] = UNIDADES_PADRAO) -> None:
    logo = _svg_data_uri("camara-h2-colorida.svg")
    linhas = "<br>".join(unidades)
    st.markdown(
        f"""
        <style>
          .cd-rod {{ display:flex; justify-content:flex-end; align-items:center; gap:1.25rem;
                    border-top:1px solid #D6D6D6; margin-top:2.5rem; padding:1.25rem 0 0.5rem; }}
          .cd-rod__ass {{ text-align:right; color:#414042; font-size:0.9rem; line-height:1.35; }}
          .cd-rod__logo {{ height:40px; min-height:20px; }}
        </style>
        <div class="cd-rod">
          <div class="cd-rod__ass">{linhas}</div>
          <img class="cd-rod__logo" src="{logo}" alt="Câmara dos Deputados">
        </div>
        """,
        unsafe_allow_html=True,
    )
