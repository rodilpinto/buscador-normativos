---
task: 11
plan: docs/superpowers/plans/2026-09-08-buscador-normativos.md (linhas 1533-1699)
reference: spec/buscador/reference/global-constraints.md
---

> ⛔ **SUPERADO — não execute.** Cópia verbatim de uma task do plano de 16 tasks, superado em
> 2026-09-16. Plano vigente: `docs/superpowers/plans/2026-09-16-consolidacao-fase1.md`.

> Extraído verbatim do plano. O plano segue fonte de verdade; esta cópia existe para o
> agente de build não precisar ler 2641 linhas. Divergência entre os dois = o plano ganha.
> **Depends on:** T2, T4, T8, T9, T10
> **Onda/trilha:** onda 3 - trilha E, paralela a T12

## Task 11: Orquestrador da busca

**Files:**
- Create: `buscador/busca.py`
- Test: `tests/test_busca.py`

**Interfaces:**
- Consumes: `Fonte`, `expandir`, `indexar`/`marcar_ja_tenho`, `premarcar_todos`, `db`
- Produces: `executar_busca(conn, tema: str, fontes: list[Fonte], acervo_raizes: list[Path], llm=None) -> int` (devolve `busca_id`), `resultados_da_busca(conn, busca_id) -> list[sqlite3.Row]`

- [ ] **Step 1: Escrever o teste que falha**

`tests/test_busca.py`:

```python
from buscador.db import conectar, criar_schema
from buscador.busca import executar_busca, resultados_da_busca
from buscador.fontes.base import FonteFake


def _conn(tmp_path):
    c = conectar(tmp_path / "t.db")
    criar_schema(c)
    return c


def test_executar_busca_grava_busca_e_resultados(tmp_path):
    conn = _conn(tmp_path)
    fonte = FonteFake(nome="f1", itens=[("Lei nº 1", "https://x.gov.br/l1.htm")])
    bid = executar_busca(conn, "LGPD", [fonte], [])
    linhas = resultados_da_busca(conn, bid)
    assert len(linhas) == 1
    assert linhas[0]["titulo"] == "Lei nº 1"
    assert linhas[0]["pre_marca"] in ("fica", "sai")
    assert linhas[0]["pre_motivo"]


def test_executar_busca_deduplica_entre_fontes(tmp_path):
    conn = _conn(tmp_path)
    a = FonteFake(nome="a", itens=[("Lei nº 1", "https://x.gov.br/l1.htm")])
    b = FonteFake(nome="b", itens=[("Lei n. 1", "https://X.gov.br/l1.htm?q=2")])
    bid = executar_busca(conn, "LGPD", [a, b], [])
    assert len(resultados_da_busca(conn, bid)) == 1


def test_executar_busca_repassa_os_termos_expandidos_as_fontes(tmp_path):
    conn = _conn(tmp_path)
    f = FonteFake(nome="f", itens=[])
    executar_busca(conn, "LGPD", [f], [])
    assert len(f.chamadas[0]) > 1  # expandiu alem do tema cru


def test_fonte_que_quebra_nao_derruba_a_busca(tmp_path):
    conn = _conn(tmp_path)

    class FonteQuebrada:
        nome, procedencia = "ruim", "catalogada"
        vinculacao_padrao, categoria = "aplicavel", "x"

        def buscar(self, termos):
            raise RuntimeError("site fora do ar")

    boa = FonteFake(nome="boa", itens=[("Lei nº 2", "https://x.gov.br/l2.htm")])
    bid = executar_busca(conn, "tema", [FonteQuebrada(), boa], [])
    assert len(resultados_da_busca(conn, bid)) == 1


def test_ja_tenho_e_aplicado_a_partir_do_acervo(tmp_path):
    conn = _conn(tmp_path)
    acervo = tmp_path / "acervo"
    acervo.mkdir()
    (acervo / "Lei nº 1.pdf").write_text("x", encoding="utf-8")
    f = FonteFake(nome="f", itens=[("Lei nº 1", "https://x.gov.br/l1.htm")])
    bid = executar_busca(conn, "LGPD", [f], [acervo])
    assert resultados_da_busca(conn, bid)[0]["ja_tenho"] == 1
```

- [ ] **Step 2: Rodar e confirmar a falha**

Run: `py -m pytest tests/test_busca.py -v`
Expected: FAIL com `ModuleNotFoundError`

- [ ] **Step 3: Implementar**

`buscador/busca.py`:

```python
"""Orquestrador: junta fontes, deduplica, marca ja-tenho, pre-marca e grava."""
from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from buscador.acervo import indexar, marcar_ja_tenho
from buscador.fontes.base import Fonte
from buscador.llm import LLM
from buscador.modelos import Resultado
from buscador.palavras_chave import expandir
from buscador.premarcacao import premarcar_todos

log = logging.getLogger(__name__)


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def executar_busca(conn: sqlite3.Connection, tema: str, fontes: list[Fonte],
                   acervo_raizes: list[Path], llm: LLM | None = None) -> int:
    termos = expandir(tema, llm)
    cur = conn.execute(
        "INSERT INTO buscas (tema, termos, criado_em) VALUES (?, ?, ?)",
        (tema, json.dumps(termos, ensure_ascii=False), _agora()),
    )
    busca_id = int(cur.lastrowid)

    brutos: list[Resultado] = []
    for fonte in fontes:
        try:
            brutos.extend(fonte.buscar(termos))
        except Exception:
            log.warning("fonte %s falhou; seguindo com as demais", fonte.nome,
                        exc_info=True)

    unicos: dict[str, Resultado] = {}
    for r in brutos:
        unicos.setdefault(r.chave_dedup, r)

    resultados = premarcar_todos(
        marcar_ja_tenho(list(unicos.values()), indexar(acervo_raizes))
    )

    conn.executemany(
        "INSERT OR IGNORE INTO resultados (busca_id, titulo, tipo, ano, ementa, url,"
        " fonte, procedencia, vinculacao, categoria, chave_dedup, ja_tenho,"
        " ja_tenho_onde, pre_marca, pre_motivo, coletado_em)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [(busca_id, r.titulo, r.tipo, r.ano, r.ementa, r.url, r.fonte, r.procedencia,
          r.vinculacao, r.categoria, r.chave_dedup, int(r.ja_tenho), r.ja_tenho_onde,
          r.pre_marca, r.pre_motivo, _agora()) for r in resultados],
    )
    return busca_id


def resultados_da_busca(conn: sqlite3.Connection, busca_id: int) -> list[sqlite3.Row]:
    return list(conn.execute(
        "SELECT * FROM resultados WHERE busca_id = ? ORDER BY categoria, titulo",
        (busca_id,)))
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `py -m pytest tests/test_busca.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add buscador/busca.py tests/test_busca.py
git commit -m "feat: orquestrador de busca resiliente a fonte quebrada"
```

---

