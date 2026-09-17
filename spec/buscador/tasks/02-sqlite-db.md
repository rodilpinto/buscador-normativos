---
task: 2
plan: docs/superpowers/plans/2026-09-08-buscador-normativos.md (linhas 195-351)
reference: spec/buscador/reference/global-constraints.md
---

> ⛔ **SUPERADO — não execute.** Cópia verbatim de uma task do plano de 16 tasks, superado em
> 2026-09-16. Plano vigente: `docs/superpowers/plans/2026-09-16-consolidacao-fase1.md`.

> Extraído verbatim do plano. O plano segue fonte de verdade; esta cópia existe para o
> agente de build não precisar ler 2641 linhas. Divergência entre os dois = o plano ganha.
> **Depends on:** T1 (`Config`)
> **Onda/trilha:** onda 2 - trilha A (dados)

## Task 2: Banco SQLite

**Files:**
- Create: `buscador/db.py`
- Test: `tests/test_db.py`

**Interfaces:**
- Consumes: `Config` da Task 1
- Produces: `conectar(caminho: Path) -> sqlite3.Connection`, `criar_schema(conn) -> None`

Tabelas: `buscas`, `resultados`, `arquivos`, `resultado_arquivo`.

- [ ] **Step 1: Escrever o teste que falha**

`tests/test_db.py`:

```python
import sqlite3
from buscador.db import conectar, criar_schema


def test_criar_schema_cria_as_quatro_tabelas(tmp_path):
    conn = conectar(tmp_path / "t.db")
    criar_schema(conn)
    nomes = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"buscas", "resultados", "arquivos", "resultado_arquivo"} <= nomes


def test_criar_schema_e_idempotente(tmp_path):
    conn = conectar(tmp_path / "t.db")
    criar_schema(conn)
    criar_schema(conn)  # nao pode levantar


def test_resultado_exige_procedencia_valida(tmp_path):
    conn = conectar(tmp_path / "t.db")
    criar_schema(conn)
    conn.execute("INSERT INTO buscas (tema, criado_em) VALUES ('x', '2026-01-01')")
    import pytest
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO resultados (busca_id, titulo, url, fonte, procedencia, "
            "vinculacao, chave_dedup) VALUES (1, 't', 'u', 'f', 'INVALIDA', "
            "'contexto', 'k')")


def test_chave_dedup_e_unica_por_busca(tmp_path):
    conn = conectar(tmp_path / "t.db")
    criar_schema(conn)
    conn.execute("INSERT INTO buscas (tema, criado_em) VALUES ('x', '2026-01-01')")
    ins = ("INSERT INTO resultados (busca_id, titulo, url, fonte, procedencia, "
           "vinculacao, chave_dedup) VALUES (1, 't', 'u', 'f', 'catalogada', "
           "'contexto', 'k')")
    conn.execute(ins)
    import pytest
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(ins)
```

- [ ] **Step 2: Rodar e confirmar a falha**

Run: `py -m pytest tests/test_db.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'buscador.db'`

- [ ] **Step 3: Implementar**

`buscador/db.py`:

```python
"""Estado do pipeline. Cada etapa grava aqui, por isso toda etapa e retomavel."""
from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS buscas (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    tema        TEXT NOT NULL,
    pasta       TEXT,
    termos      TEXT,
    criado_em   TEXT NOT NULL,
    triado_em   TEXT,
    baixado_em  TEXT
);

CREATE TABLE IF NOT EXISTS resultados (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    busca_id      INTEGER NOT NULL REFERENCES buscas(id) ON DELETE CASCADE,
    titulo        TEXT NOT NULL,
    tipo          TEXT,
    ano           INTEGER,
    ementa        TEXT,
    ementa_llm    TEXT,
    url           TEXT NOT NULL,
    fonte         TEXT NOT NULL,
    procedencia   TEXT NOT NULL CHECK (procedencia IN ('catalogada','web-aberta')),
    vinculacao    TEXT NOT NULL CHECK (vinculacao IN ('obrigatorio','aplicavel','contexto')),
    categoria     TEXT,
    chave_dedup   TEXT NOT NULL,
    ja_tenho      INTEGER NOT NULL DEFAULT 0,
    ja_tenho_onde TEXT,
    pre_marca     TEXT CHECK (pre_marca IN ('fica','sai')),
    pre_motivo    TEXT,
    decisao       TEXT CHECK (decisao IN ('fica','sai')),
    decidido_em   TEXT,
    coletado_em   TEXT,
    UNIQUE (busca_id, chave_dedup)
);

CREATE TABLE IF NOT EXISTS arquivos (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    sha256     TEXT NOT NULL UNIQUE,
    caminho    TEXT NOT NULL,
    tamanho    INTEGER NOT NULL,
    baixado_em TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS resultado_arquivo (
    resultado_id INTEGER NOT NULL REFERENCES resultados(id) ON DELETE CASCADE,
    arquivo_id   INTEGER NOT NULL REFERENCES arquivos(id) ON DELETE CASCADE,
    duplicata    INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (resultado_id, arquivo_id)
);

CREATE INDEX IF NOT EXISTS ix_res_busca ON resultados(busca_id);
CREATE INDEX IF NOT EXISTS ix_res_cat ON resultados(busca_id, categoria);
"""


def conectar(caminho: Path) -> sqlite3.Connection:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(caminho, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def criar_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `py -m pytest tests/test_db.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add buscador/db.py tests/test_db.py
git commit -m "feat: schema sqlite com constraints de procedencia e dedup"
```

---

