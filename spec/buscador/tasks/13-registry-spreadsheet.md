---
task: 13
plan: docs/superpowers/plans/2026-09-08-buscador-normativos.md (linhas 1908-2048)
reference: spec/buscador/reference/global-constraints.md
---

> Extraído verbatim do plano. O plano segue fonte de verdade; esta cópia existe para o
> agente de build não precisar ler 2641 linhas. Divergência entre os dois = o plano ganha.
> **Depends on:** T2 (`db`)
> **Onda/trilha:** onda 2 - trilha A (dados)

## Task 13: Planilha-registro

**Files:**
- Create: `buscador/planilha.py`
- Test: `tests/test_planilha.py`

**Interfaces:**
- Consumes: `db`
- Produces: `COLUNAS: list[str]`, `gerar_planilha(conn, busca_id, saida: Path) -> Path`

As 11 colunas da planilha atual do projeto **mais** as 6 de rastreabilidade da spec §6.

- [ ] **Step 1: Escrever o teste que falha**

`tests/test_planilha.py`:

```python
from openpyxl import load_workbook
from buscador.db import conectar, criar_schema
from buscador.busca import executar_busca
from buscador.fontes.base import FonteFake
from buscador.planilha import gerar_planilha, COLUNAS


def _prep(tmp_path):
    conn = conectar(tmp_path / "t.db")
    criar_schema(conn)
    bid = executar_busca(conn, "LGPD", [FonteFake(
        nome="f", itens=[("Lei nº 1", "https://x.gov.br/l1.htm")])], [])
    conn.execute("UPDATE resultados SET decisao='fica' WHERE busca_id=?", (bid,))
    return conn, bid


def test_planilha_tem_todas_as_colunas_na_ordem(tmp_path):
    conn, bid = _prep(tmp_path)
    ws = load_workbook(gerar_planilha(conn, bid, tmp_path / "p.xlsx")).active
    assert [c.value for c in ws[1]] == COLUNAS


def test_colunas_de_rastreabilidade_estao_presentes():
    for c in ["URL", "Fonte", "Procedência", "Decisão", "Motivo da pré-marcação",
              "sha256", "Coletado em"]:
        assert c in COLUNAS


def test_planilha_registra_todos_os_resultados_inclusive_os_descartados(tmp_path):
    conn, bid = _prep(tmp_path)
    conn.execute("UPDATE resultados SET decisao='sai' WHERE busca_id=?", (bid,))
    ws = load_workbook(gerar_planilha(conn, bid, tmp_path / "p.xlsx")).active
    assert ws.max_row == 2  # cabecalho + 1 descartado: o registro guarda o descarte


def test_planilha_usa_fonte_arial(tmp_path):
    conn, bid = _prep(tmp_path)
    ws = load_workbook(gerar_planilha(conn, bid, tmp_path / "p.xlsx")).active
    assert ws["A1"].font.name == "Arial"
```

- [ ] **Step 2: Rodar e confirmar a falha**

Run: `py -m pytest tests/test_planilha.py -v`
Expected: FAIL com `ModuleNotFoundError`

- [ ] **Step 3: Implementar**

`buscador/planilha.py`:

```python
"""Planilha-registro: o que foi achado, o que foi decidido e por que."""
from __future__ import annotations

import sqlite3
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

COLUNAS = [
    "Nº", "Categoria", "Normativo", "Tipo", "Ano", "Ementa / Descrição",
    "Vinculação para a CD", "Status na Pasta", "Observações", "URL",
    "Fonte", "Procedência", "Pré-marcação", "Motivo da pré-marcação",
    "Decisão", "sha256", "Coletado em",
]
LARGURAS = [5, 22, 45, 18, 7, 55, 22, 16, 40, 55, 16, 14, 13, 38, 10, 20, 20]

CONSULTA = """
SELECT r.*, a.sha256 AS sha
FROM resultados r
LEFT JOIN resultado_arquivo ra ON ra.resultado_id = r.id
LEFT JOIN arquivos a ON a.id = ra.arquivo_id
WHERE r.busca_id = ?
ORDER BY r.categoria, r.titulo
"""


def gerar_planilha(conn: sqlite3.Connection, busca_id: int, saida: Path) -> Path:
    wb = Workbook()
    ws = wb.active
    ws.title = "Normativos"

    for i, (nome, largura) in enumerate(zip(COLUNAS, LARGURAS), start=1):
        c = ws.cell(row=1, column=i, value=nome)
        c.font = Font(name="Arial", bold=True, size=10, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="2F5496")
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws.column_dimensions[get_column_letter(i)].width = largura
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(COLUNAS))}1"

    for n, r in enumerate(conn.execute(CONSULTA, (busca_id,)), start=1):
        valores = [
            n, r["categoria"], r["titulo"], r["tipo"], r["ano"], r["ementa"],
            r["vinculacao"], "Já no acervo" if r["ja_tenho"] else "Novo",
            r["ja_tenho_onde"], r["url"], r["fonte"], r["procedencia"],
            r["pre_marca"], r["pre_motivo"], r["decisao"], r["sha"], r["coletado_em"],
        ]
        for col, valor in enumerate(valores, start=1):
            c = ws.cell(row=n + 1, column=col, value=valor)
            c.font = Font(name="Arial", size=10)
            c.alignment = Alignment(vertical="top", wrap_text=True)

    saida.parent.mkdir(parents=True, exist_ok=True)
    wb.save(saida)
    return saida
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `py -m pytest tests/test_planilha.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add buscador/planilha.py tests/test_planilha.py
git commit -m "feat: planilha-registro com colunas de rastreabilidade"
```

---

