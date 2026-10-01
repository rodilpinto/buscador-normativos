"""llm_cadeia — chamar LLM com fallback entre provedores. Comece pelo README.md desta pasta.

    from llm_cadeia import gerar
    r = gerar("prompt", sistema="...", json=True)   # nunca levanta excecao
    r.texto, r.origem, r.tentativas

Pasta copiavel: a ORIGEM vive em github.com/rodilpinto/nuati-framework, pasta llm_cadeia/.
Nao edite uma copia — melhore a origem, suba __version__ e recopie.
"""

from .nucleo import (
    GEMINI_MODELOS_PADRAO,
    PRESETS,
    Resposta,
    descrever,
    disponivel,
    gerar,
    novo_contexto,
    provedor_do_usuario,
    recarregar,
    ultimo_usado,
    usar_contexto,
)

__version__ = "1.1.0"

__all__ = [
    "gerar", "Resposta", "disponivel", "descrever", "ultimo_usado",
    "provedor_do_usuario", "novo_contexto", "usar_contexto", "recarregar",
    "PRESETS", "GEMINI_MODELOS_PADRAO", "__version__",
]
