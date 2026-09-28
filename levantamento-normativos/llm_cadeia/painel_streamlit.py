"""Painel Streamlit do llm_cadeia (opcional): "usar minha propria chave" + status da cadeia.

Uso, no app, ANTES de qualquer chamada a gerar() (a barra lateral roda no topo do script):

    from llm_cadeia.painel_streamlit import painel_llm
    with st.sidebar:
        painel_llm()

Por que tem de rodar a cada execucao do script: a chave digitada vale SO para esta
sessao. Ela fica no st.session_state (memoria do servidor), nunca em disco, log ou
planilha, e vai na frente da cadeia do app. O contexto e reinstalado a cada execucao
(nucleo.usar_contexto) porque o ContextVar vale so para a thread daquela execucao
(LESSONS 25/09 do buscador: variavel de modulo vazaria a chave entre usuarios).

Veio do app.py do buscador-normativos (23/09; chave do usuario 25/09), sem mudar os
textos nem as key= dos widgets.
"""

from __future__ import annotations

import streamlit as st

from . import nucleo

_ROTULOS = {"Gemini (Google AI Studio)": "gemini", "Groq": "groq", "Cerebras": "cerebras",
            "OpenRouter": "openrouter", "Outro (compatível com OpenAI)": "openai"}


def painel_llm(mostrar_campo_de_chave: bool = True) -> None:
    """Render the user-key box and the chain status; install this session's context."""
    st.divider()
    if "llm_contexto" not in st.session_state:
        st.session_state["llm_contexto"] = nucleo.novo_contexto()
    ctx = st.session_state["llm_contexto"]

    tipo, chave, url, modelo = "gemini", "", "", ""
    if mostrar_campo_de_chave:
        with st.expander("Usar minha própria chave de IA"):
            tipo = _ROTULOS[st.selectbox("Serviço", list(_ROTULOS), key="llm_usr_tipo")]
            chave = st.text_input("Chave de API", type="password", key="llm_usr_chave")
            url = st.text_input("URL base (ex.: http://host:1234/v1)", key="llm_usr_url") if tipo == "openai" else ""
            modelo = st.text_input("Modelo(s), separados por vírgula (vazio = padrão)", key="llm_usr_modelo")
            st.caption("Vale só nesta sessão; não é gravada. Tem prioridade sobre as chaves do app.")

    # Recria o provedor so quando a entrada muda, para nao zerar as esperas dele a cada clique.
    assinatura = (tipo, chave, url, modelo)
    if ctx.get("assinatura") != assinatura:
        ctx["assinatura"] = assinatura
        ctx["usuario"] = nucleo.provedor_do_usuario(tipo, chave, modelo, url)
    nucleo.usar_contexto(ctx)
    if chave and ctx["usuario"] is None:
        st.warning("Chave incompleta: para 'Outro', informe URL base e modelo.")

    linhas = nucleo.descrever()
    if linhas:
        st.caption("IA (em ordem de tentativa):\n\n" + "\n\n".join(f"- {c}" for c in linhas))
    else:
        st.caption("IA: nenhum provedor configurado (roda sem LLM).")

    # A barra lateral roda ANTES do gerar(): sem o placeholder, "Última resposta" so
    # apareceria na execucao seguinte do script. O gancho atualiza a linha na mesma execucao.
    linha = st.empty()
    if nucleo.ultimo_usado():
        linha.caption(f"Última resposta: {nucleo.ultimo_usado()}")
    ctx["ao_responder"] = lambda origem: linha.caption(f"Última resposta: {origem}")
