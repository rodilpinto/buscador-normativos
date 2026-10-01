"""tempo_economizado: quanto tempo de trabalho manual o app poupou, e a conta explicada. Comece pelo README.md.

    from tempo_economizado import Etapa, estimar, explicar
    est = estimar([Etapa("Ler cada artigo", 50, 2.0)], automatico_min=1)

Pasta copiavel: a ORIGEM vive em github.com/rodilpinto/nuati-framework, pasta tempo_economizado/.
Nao edite uma copia: melhore a origem, suba __version__ e recopie.
"""

from .nucleo import NOTA_PADRAO, Etapa, Estimativa, estimar, explicar, formatar_tempo, plural, resumo

__version__ = "1.0.0"

__all__ = ["Etapa", "Estimativa", "estimar", "explicar", "resumo", "formatar_tempo", "plural",
           "NOTA_PADRAO", "__version__"]
