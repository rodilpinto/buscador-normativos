# -*- coding: utf-8 -*-
"""Testes do tempo_economizado. Viajam com a pasta: nao importam nada de app nenhum, nao fazem rede.

Os quatro modelos que existiam nos apps em 29/09/2026 (LEVANTAMENTO-FRAMEWORK.md, secao 6) sao
reescritos aqui como listas de Etapa e tem de dar o MESMO numero que o codigo original dava.

Rodar da pasta que CONTEM tempo_economizado/:
    python -m pytest tempo_economizado -q
"""
from __future__ import annotations

import pytest

import tempo_economizado as te
from tempo_economizado import Etapa, estimar, explicar, formatar_tempo, plural, resumo


# --- conta ---------------------------------------------------------------------

def test_soma_etapas_com_quantidades_proprias_e_desconta_a_ferramenta():
    est = estimar([Etapa("a", 200, 2.0), Etapa("b", 30, 5.0), Etapa("c", 8, 15.0)], automatico_min=2)
    assert est.manual_min == 400 + 150 + 120
    assert est.economia_min == 668
    assert est.economia_horas == pytest.approx(668 / 60)
    assert est.economia_dias_uteis(8) == pytest.approx(668 / 60 / 8)


def test_economia_nunca_negativa_e_entrada_negativa_e_erro():
    assert estimar([Etapa("a", 1, 1.0)], automatico_min=5).economia_min == 0
    with pytest.raises(ValueError):
        Etapa("a", -1, 1.0)
    with pytest.raises(ValueError):
        estimar([], automatico_min=-1)


def test_sem_etapas_nada_a_poupar():
    assert estimar([]).manual_min == 0 == estimar([]).economia_min


# --- os 4 modelos dos apps cabem na base (F-A2) ------------------------------------

def test_modelo_fracionamento_da_o_mesmo_numero_do_original():
    """nualc/report.py estimativa_ganho @ 91f3e67, com os tempos do nualc/config.py."""
    n_sem_codigo, n_classes, n_casos = 137, 41, 6
    CLASSIFICAR, ANALISAR, CASO, AUTO = 2.0, 5.0, 15.0, 2.0
    total_min = n_sem_codigo * CLASSIFICAR + n_classes * ANALISAR + n_casos * CASO   # conta original
    est = estimar([Etapa("Classificar", n_sem_codigo, CLASSIFICAR), Etapa("Agregar", n_classes, ANALISAR, "classe"),
                   Etapa("Documentar", n_casos, CASO, "caso")], automatico_min=AUTO)
    assert est.manual_min / 60 == pytest.approx(total_min / 60)
    assert est.economia_horas == pytest.approx(max(0.0, total_min - AUTO) / 60)


def test_modelo_checklist_da_o_mesmo_numero_do_original():
    """checklist app.py:502-522 @ 92ac158: minutos por etapa x numero de itens, para todas as etapas."""
    breakdown = {"Leitura": 2.0, "Requisito": 1.0, "MCGR": 1.5, "Criticidade": 1.0, "Responsavel": 0.5,
                 "Mitigacao": 1.5, "Evidencia": 1.0, "Planilha": 0.5}
    n_itens = 50
    est = estimar([Etapa(nome, n_itens, minutos) for nome, minutos in breakdown.items()])
    assert est.economia_min == n_itens * sum(breakdown.values()) == 450   # 9,0 min/item (o comentario la diz 8,0)
    assert formatar_tempo(est.economia_min) == "7h30min"


def test_modelo_scopediagram_da_o_mesmo_numero_do_original():
    """scopediagram app.py:17-32 @ 9d52dc5: horas fixas + termos lineares por componente."""
    i, o, r, rec, sub, ativ = 3, 3, 2, 2, 4, 20
    original_h = round((0.6 + (i + o + r + rec) * 0.06) + (0.8 + sub * 0.35 + ativ * 0.08)
                       + (0.9 + sub * 0.3 + (i + o) * 0.05) + (0.7 + sub * 0.2) + (0.4 + r * 0.03 + rec * 0.03), 1)
    h = 60   # minutos por hora: o original conta em horas
    est = estimar([
        Etapa("Ler e triar o texto-base (fixo)", 1, 0.6 * h, "vez"),
        Etapa("Extrair cada elemento", i + o + r + rec, 0.06 * h, "elemento"),
        Etapa("Organizar componentes (fixo)", 1, 0.8 * h, "vez"),
        Etapa("Estruturar cada subprocesso", sub, 0.35 * h, "subprocesso"),
        Etapa("Estruturar cada atividade", ativ, 0.08 * h, "atividade"),
        Etapa("Diagramar (fixo)", 1, 0.9 * h, "vez"),
        Etapa("Diagramar cada subprocesso", sub, 0.3 * h, "subprocesso"),
        Etapa("Diagramar cada entrada/saída", i + o, 0.05 * h, "entrada/saída", "entradas/saídas"),
        Etapa("Montar o PowerPoint (fixo)", 1, 0.7 * h, "vez"),
        Etapa("Formatar cada subprocesso", sub, 0.2 * h, "subprocesso"),
        Etapa("Revisão final (fixo)", 1, 0.4 * h, "vez"),
        Etapa("Revisar cada regulador e recurso", r + rec, 0.03 * h, "regulador/recurso", "reguladores/recursos"),
    ])
    assert round(est.economia_horas, 1) == original_h == 9.4


def test_modelo_dou_da_o_mesmo_numero_do_original():
    """DOU-clipping app.py @ a6aed4e e pesquisa_diario (identicos): 35 s por termo + 300 s, por data."""
    termos, datas = 10, 3
    original_min = round((termos * 35 + 300) * datas / 60)
    est = estimar([Etapa("Pesquisar cada termo em cada data", termos * datas, 35 / 60, "busca"),
                   Etapa("Juntar, tirar repetidos e formatar, por data", datas, 5.0, "data")])
    assert est.economia_min == pytest.approx(32.5)
    assert round(est.economia_min) == original_min


# --- texto -----------------------------------------------------------------------

@pytest.mark.parametrize("minutos,texto", [
    (35 / 60, "35 s"), (1.5, "1,5 min"), (2, "2 min"), (45, "45 min"), (60, "1h"), (450, "7h30min"),
    (668, "11h08min"), (6000, "100h"), (90000, "1.500h"),
])
def test_formatar_tempo(minutos, texto):
    assert formatar_tempo(minutos) == texto


@pytest.mark.parametrize("singular,esperado", [
    ("item", "itens"), ("caso", "casos"), ("regulador", "reguladores"), ("classe", "classes"),
    ("dispositivo", "dispositivos"), ("questão", "questões"), ("anual", "anuais"),
])
def test_plural(singular, esperado):
    assert plural(singular) == esperado


def test_rotulo_de_quantidade():
    assert Etapa("x", 1, 1.0, "caso").rotulo_quantidade() == "1 caso"
    assert Etapa("x", 50, 1.0).rotulo_quantidade() == "50 itens"
    assert Etapa("x", 1200, 1.0, "linha").rotulo_quantidade() == "1.200 linhas"
    assert Etapa("x", 2, 1.0, "entrada/saída", "entradas/saídas").rotulo_quantidade() == "2 entradas/saídas"


def test_explicacao_conta_a_historia_antes_da_tabela():
    est = estimar([Etapa("Classificar cada item sem código", 200, 2.0),
                   Etapa("Documentar cada caso", 8, 15.0, "caso")], automatico_min=2)
    texto = explicar(est)
    linhas = texto.splitlines()
    assert linhas[0] == ("Se uma pessoa fizesse este trabalho à mão, levaria cerca de **8h40min**. "
                         "A ferramenta fez em **2 min**. A diferença, **8h38min**, é o tempo poupado.")
    assert "| Classificar cada item sem código | 200 itens | 2 min | 6h40min |" in linhas
    assert "| Documentar cada caso | 8 casos | 15 min | 2h |" in linhas
    assert "| **Total à mão** | | | **8h40min** |" in linhas
    assert "| Menos o tempo da ferramenta | | | − 2 min |" in linhas
    assert "| **Tempo poupado** | | | **8h38min** |" in linhas
    assert linhas[-1] == te.NOTA_PADRAO
    assert texto.index("Se uma pessoa") < texto.index("| Etapa") < texto.index(te.NOTA_PADRAO)


def test_sem_tempo_da_ferramenta_a_explicacao_nao_mostra_desconto():
    texto = explicar(estimar([Etapa("Ler cada artigo", 50, 2.0)]))
    assert "ferramenta fez" not in texto and "Menos o tempo" not in texto and "Tempo poupado** |" not in texto
    assert texto.startswith("Se uma pessoa fizesse este trabalho à mão, levaria cerca de **1h40min**: esse é o")


def test_nota_pode_ser_trocada_ou_omitida():
    est = estimar([Etapa("a", 1, 1.0)])
    assert explicar(est, nota="Tempos medidos em 2026.").endswith("Tempos medidos em 2026.")
    assert explicar(est, nota="").splitlines()[-1].startswith("| **Total")


def test_resumo():
    assert resumo(estimar([Etapa("a", 50, 9.0)])) == "Tempo de trabalho manual poupado: cerca de 7h30min"


def test_versao():
    assert te.__version__.count(".") == 2


# --- painel Streamlit (dublado) --------------------------------------------------------

@pytest.fixture
def st_dublado(monkeypatch):
    from tempo_economizado import painel_streamlit as painel
    eventos = []

    class Expander:
        def __init__(self, titulo):
            eventos.append(("expander", titulo))

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(painel.st, "markdown", lambda t, **k: eventos.append(("markdown", t)))
    monkeypatch.setattr(painel.st, "expander", Expander)
    return painel, eventos


def test_painel_mostra_linha_e_explicacao(st_dublado):
    painel, eventos = st_dublado
    est = estimar([Etapa("Ler cada artigo", 50, 2.0)], automatico_min=1)
    painel.mostrar_tempo_economizado(est)
    assert eventos[0] == ("markdown", "⏱️ Tempo de trabalho manual poupado: cerca de 1h39min")
    assert eventos[1] == ("expander", "Como chegamos a esse número?")
    assert eventos[2] == ("markdown", explicar(est))


def test_painel_nao_mostra_nada_sem_resultado(st_dublado):
    painel, eventos = st_dublado
    painel.mostrar_tempo_economizado(estimar([Etapa("Ler cada artigo", 0, 2.0)]))
    assert eventos == []
