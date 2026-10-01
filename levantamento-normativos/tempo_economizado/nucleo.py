"""Tempo economizado: conta e explicacao, sem Streamlit (o painel fica em painel_streamlit.py).

Base (decisao F-A2 do framework, 30/09/2026): o modelo do analise-fracionamento-dispensa
(nualc/report.py, estimativa_ganho). Cada etapa do trabalho manual tem SUA quantidade (medida no
resultado do app) e SEU tempo por unidade; a soma e o tempo a mao; menos o tempo da ferramenta,
o tempo poupado.

    from tempo_economizado import Etapa, estimar
    est = estimar([
        Etapa("Ler e interpretar cada dispositivo", 50, 2.0),        # 50 itens x 2 min
        Etapa("Documentar cada caso", 8, 15.0, unidade="caso"),       # 8 casos x 15 min
    ], automatico_min=2)
    est.economia_min, formatar_tempo(est.economia_min), explicar(est)

Os tempos por unidade sao estimativas de cada app (nao medicoes); explicar() diz isso numa frase.
"""

from __future__ import annotations

from dataclasses import dataclass, field

NOTA_PADRAO = (
    "Os tempos de cada etapa são estimativas de referência de quem faz esse trabalho, não cronometragens. "
    "O número serve para dar a ordem de grandeza do tempo poupado."
)


@dataclass(frozen=True)
class Etapa:
    """Uma etapa do trabalho manual que a ferramenta substitui.

    descricao:           o que a pessoa faria à mão, em linguagem de quem faz ("Ler cada artigo")
    quantidade:          quantas vezes a etapa se repete NESTE resultado (medido pelo app)
    minutos_por_unidade: quanto tempo leva cada vez, em minutos (estimativa do app)
    unidade:             nome de uma vez, no singular ("item", "caso", "termo")
    unidade_plural:      plural, se não for o singular + "s"/"es"/"ns"
    """

    descricao: str
    quantidade: float
    minutos_por_unidade: float
    unidade: str = "item"
    unidade_plural: str = ""

    def __post_init__(self):
        if self.quantidade < 0 or self.minutos_por_unidade < 0:
            raise ValueError(f"Etapa '{self.descricao}': quantidade e tempo não podem ser negativos.")

    @property
    def total_min(self) -> float:
        return self.quantidade * self.minutos_por_unidade

    def rotulo_quantidade(self) -> str:
        """'50 itens', '1 caso', '2,5 horas'."""
        n = _numero(self.quantidade)
        if self.quantidade == 1:
            return f"{n} {self.unidade}"
        return f"{n} {self.unidade_plural or plural(self.unidade)}"


@dataclass(frozen=True)
class Estimativa:
    etapas: tuple[Etapa, ...]
    automatico_min: float = 0.0
    manual_min: float = field(init=False)
    economia_min: float = field(init=False)

    def __post_init__(self):
        manual = sum(e.total_min for e in self.etapas)
        object.__setattr__(self, "manual_min", manual)
        object.__setattr__(self, "economia_min", max(0.0, manual - self.automatico_min))

    @property
    def economia_horas(self) -> float:
        return self.economia_min / 60.0

    def economia_dias_uteis(self, horas_por_dia: float = 8.0) -> float:
        return self.economia_horas / horas_por_dia


def estimar(etapas, automatico_min: float = 0.0) -> Estimativa:
    """Soma as etapas (quantidade x minutos de cada uma) e desconta o tempo da ferramenta.

    automatico_min: quanto a ferramenta leva (0 = não informado: a explicação omite o desconto).
    A economia nunca é negativa.
    """
    if automatico_min < 0:
        raise ValueError("automatico_min não pode ser negativo.")
    return Estimativa(tuple(etapas), float(automatico_min))


# ---------------------------------------------------------------------------
# Texto
# ---------------------------------------------------------------------------


def plural(palavra: str) -> str:
    """Plural simples do português: item->itens, regulador->reguladores, caso->casos."""
    if not palavra:
        return palavra
    if palavra.endswith("m"):
        return palavra[:-1] + "ns"
    if palavra[-1] in "rzs":
        return palavra + "es"
    if palavra.endswith("ão"):
        return palavra[:-2] + "ões"
    if palavra.endswith("l"):
        return palavra[:-1] + "is"
    return palavra + "s"


def _numero(valor: float) -> str:
    """1 -> '1'; 2.5 -> '2,5'; 1200 -> '1.200'."""
    if float(valor).is_integer():
        return f"{int(valor):,}".replace(",", ".")
    return f"{valor:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")


def formatar_tempo(minutos: float) -> str:
    """Tempo para gente ler: '35 s', '1,5 min', '45 min', '1h', '7h30min'."""
    if minutos < 1:
        return f"{round(minutos * 60)} s"
    if minutos < 10 and not float(minutos).is_integer():
        return f"{_numero(round(minutos, 1))} min"
    total = int(round(minutos))
    if total < 60:
        return f"{total} min"
    horas, resto = divmod(total, 60)
    return f"{_numero(horas)}h{resto:02d}min" if resto else f"{_numero(horas)}h"


def resumo(est: Estimativa) -> str:
    """Uma linha para o rodapé: 'Tempo de trabalho manual poupado: cerca de 7h30min'."""
    return f"Tempo de trabalho manual poupado: cerca de {formatar_tempo(est.economia_min)}"


def explicar(est: Estimativa, nota: str = NOTA_PADRAO) -> str:
    """Explicação em linguagem simples, em Markdown, para o expander 'Como chegamos a esse número?'.

    Ordem pensada para não gerar dúvida: primeiro a história em uma frase (à mão X, a ferramenta
    Y, a diferença é o poupado), depois a conta linha a linha, e por fim de onde vêm os tempos.
    """
    manual = formatar_tempo(est.manual_min)
    poupado = formatar_tempo(est.economia_min)
    if est.automatico_min > 0:
        frase = (f"Se uma pessoa fizesse este trabalho à mão, levaria cerca de **{manual}**. "
                 f"A ferramenta fez em **{formatar_tempo(est.automatico_min)}**. "
                 f"A diferença, **{poupado}**, é o tempo poupado.")
    else:
        frase = f"Se uma pessoa fizesse este trabalho à mão, levaria cerca de **{manual}**: esse é o tempo poupado."
    linhas = [
        frase,
        "",
        "Para cada etapa do trabalho manual, a conta é: **quantas vezes a etapa se repete neste resultado × "
        "quanto tempo leva cada vez**.",
        "",
        "| Etapa do trabalho manual | Quantas vezes | Tempo de cada | Total |",
        "|:--|--:|--:|--:|",
    ]
    for e in est.etapas:
        linhas.append(f"| {e.descricao} | {e.rotulo_quantidade()} | {formatar_tempo(e.minutos_por_unidade)} | "
                      f"{formatar_tempo(e.total_min)} |")
    linhas.append(f"| **Total à mão** | | | **{manual}** |")
    if est.automatico_min > 0:
        linhas.append(f"| Menos o tempo da ferramenta | | | − {formatar_tempo(est.automatico_min)} |")
        linhas.append(f"| **Tempo poupado** | | | **{poupado}** |")
    if nota:
        linhas += ["", nota]
    return "\n".join(linhas)
