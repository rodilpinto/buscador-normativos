"""Painel Streamlit do tempo_economizado (opcional): uma linha + o expander com a explicação.

    from tempo_economizado import Etapa, estimar
    from tempo_economizado.painel_streamlit import mostrar_tempo_economizado

    mostrar_tempo_economizado(estimar([Etapa("Ler cada artigo", n_itens, 2.0)], automatico_min=1))
"""

from __future__ import annotations

import streamlit as st

from .nucleo import NOTA_PADRAO, Estimativa, explicar, resumo

TITULO_EXPANDER = "Como chegamos a esse número?"


def mostrar_tempo_economizado(est: Estimativa, nota: str = NOTA_PADRAO) -> None:
    """Mostra o tempo poupado e a conta. Sem etapa com quantidade (nada gerado ainda), não mostra nada."""
    if est.manual_min <= 0:
        return
    st.markdown(f"⏱️ {resumo(est)}")
    with st.expander(TITULO_EXPANDER):
        st.markdown(explicar(est, nota))
