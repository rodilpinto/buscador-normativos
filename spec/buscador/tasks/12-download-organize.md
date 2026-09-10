---
task: 12
plan: docs/superpowers/plans/2026-09-08-buscador-normativos.md (linhas 1700-1907)
reference: spec/buscador/reference/global-constraints.md
---

> Extraído verbatim do plano. O plano segue fonte de verdade; esta cópia existe para o
> agente de build não precisar ler 2641 linhas. Divergência entre os dois = o plano ganha.
> **Depends on:** T2 (`db`), T9 (`sha256_arquivo`)
> **Onda/trilha:** onda 3 - trilha E, paralela a T11

## Task 12: Download, organização por tema e duplicatas

**Files:**
- Create: `buscador/download.py`
- Test: `tests/test_download.py`

**Interfaces:**
- Consumes: `db`, `sha256_arquivo`
- Produces: `caminho_longo(p: Path) -> str`, `pasta_do_tema(tema: str) -> str`, `baixar_selecionados(conn, busca_id, raiz_dados: Path, baixar_fn) -> RelatorioDownload`, `RelatorioDownload` (dataclass: `baixados: int`, `duplicatas: int`, `erros: list[tuple[str,str]]`)

Aqui mora a **mitigação obrigatória da B4**: dedup por sha256 com relatório, nunca duplicação silenciosa. E a trava dos 260 caracteres do Windows.

- [ ] **Step 1: Escrever o teste que falha**

`tests/test_download.py`:

```python
from pathlib import Path
from buscador.db import conectar, criar_schema
from buscador.busca import executar_busca
from buscador.fontes.base import FonteFake
from buscador.download import (baixar_selecionados, pasta_do_tema, caminho_longo)


def _prep(tmp_path, itens, decisao="fica"):
    conn = conectar(tmp_path / "t.db")
    criar_schema(conn)
    bid = executar_busca(conn, "LGPD 2026", [FonteFake(nome="f", itens=itens)], [])
    conn.execute("UPDATE resultados SET decisao = ? WHERE busca_id = ?", (decisao, bid))
    return conn, bid


def test_pasta_do_tema_e_curta_e_sem_acento():
    p = pasta_do_tema("Levantamento sobre Governança de IA na Câmara dos Deputados")
    assert len(p) <= 32
    assert p == p.lower()
    assert " " not in p


def test_caminho_longo_prefixa_no_windows(tmp_path):
    assert caminho_longo(tmp_path / "x").endswith("x")


def test_baixa_so_o_que_foi_decidido_fica(tmp_path):
    conn, bid = _prep(tmp_path, [("A", "https://x/a.pdf"), ("B", "https://x/b.pdf")])
    conn.execute("UPDATE resultados SET decisao='sai' WHERE titulo='B'")
    rel = baixar_selecionados(conn, bid, tmp_path / "dados",
                              lambda url: b"conteudo-" + url.encode())
    assert rel.baixados == 1
    assert rel.duplicatas == 0


def test_detecta_duplicata_por_sha256_e_nao_regrava(tmp_path):
    conn, bid = _prep(tmp_path, [("A", "https://x/a.pdf"), ("B", "https://x/b.pdf")])
    rel = baixar_selecionados(conn, bid, tmp_path / "dados", lambda url: b"identico")
    assert rel.baixados == 1
    assert rel.duplicatas == 1
    assert conn.execute("SELECT COUNT(*) FROM arquivos").fetchone()[0] == 1


def test_erro_de_download_nao_interrompe_os_demais(tmp_path):
    conn, bid = _prep(tmp_path, [("A", "https://x/a.pdf"), ("B", "https://x/b.pdf")])

    def falha_no_a(url):
        if url.endswith("a.pdf"):
            raise RuntimeError("404")
        return b"ok"

    rel = baixar_selecionados(conn, bid, tmp_path / "dados", falha_no_a)
    assert rel.baixados == 1
    assert len(rel.erros) == 1


def test_grava_dentro_da_pasta_do_tema(tmp_path):
    conn, bid = _prep(tmp_path, [("A", "https://x/a.pdf")])
    baixar_selecionados(conn, bid, tmp_path / "dados", lambda url: b"x")
    assert list((tmp_path / "dados" / pasta_do_tema("LGPD 2026")).iterdir())
```

- [ ] **Step 2: Rodar e confirmar a falha**

Run: `py -m pytest tests/test_download.py -v`
Expected: FAIL com `ModuleNotFoundError`

- [ ] **Step 3: Implementar**

`buscador/download.py`:

```python
"""Download e organizacao por tema, com dedup sha256 (mitigacao da decisao B4)."""
from __future__ import annotations

import hashlib
import logging
import re
import sqlite3
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

import httpx

log = logging.getLogger(__name__)
MAX_PASTA = 32

BaixarFn = Callable[[str], bytes]


@dataclass
class RelatorioDownload:
    baixados: int = 0
    duplicatas: int = 0
    erros: list[tuple[str, str]] = field(default_factory=list)


def caminho_longo(p: Path) -> str:
    """Acima de 260 chars o Windows falha EM SILENCIO. O prefixo evita isso."""
    bruto = str(p.resolve())
    if len(bruto) > 240 and not bruto.startswith("\\\\?\\"):
        return "\\\\?\\" + bruto
    return bruto


def pasta_do_tema(tema: str) -> str:
    sem_acento = "".join(c for c in unicodedata.normalize("NFD", tema)
                         if unicodedata.category(c) != "Mn")
    limpo = re.sub(r"[^0-9a-zA-Z]+", "-", sem_acento.lower()).strip("-")
    return limpo[:MAX_PASTA].rstrip("-")


def _nome_do_arquivo(url: str, sha: str) -> str:
    base = Path(urlsplit(url).path).name or "arquivo"
    sufixo = Path(base).suffix or ".bin"
    caule = Path(base).stem[:60] or "arquivo"
    return f"{caule}-{sha[:8]}{sufixo}"


def _http_get(url: str) -> bytes:
    r = httpx.get(url, timeout=60.0, follow_redirects=True)
    r.raise_for_status()
    return r.content


def baixar_selecionados(conn: sqlite3.Connection, busca_id: int, raiz_dados: Path,
                        baixar_fn: BaixarFn | None = None) -> RelatorioDownload:
    baixar_fn = baixar_fn or _http_get
    tema = conn.execute("SELECT tema FROM buscas WHERE id = ?",
                        (busca_id,)).fetchone()["tema"]
    destino = raiz_dados / pasta_do_tema(tema)
    destino.mkdir(parents=True, exist_ok=True)

    rel = RelatorioDownload()
    linhas = conn.execute(
        "SELECT id, url, titulo FROM resultados WHERE busca_id = ? AND decisao = 'fica'",
        (busca_id,)).fetchall()

    for linha in linhas:
        try:
            conteudo = baixar_fn(linha["url"])
        except Exception as exc:
            log.warning("falha ao baixar %s", linha["url"], exc_info=True)
            rel.erros.append((linha["titulo"], str(exc)))
            continue

        sha = hashlib.sha256(conteudo).hexdigest()
        ja = conn.execute("SELECT id FROM arquivos WHERE sha256 = ?", (sha,)).fetchone()
        if ja is not None:
            conn.execute("INSERT OR IGNORE INTO resultado_arquivo "
                         "(resultado_id, arquivo_id, duplicata) VALUES (?,?,1)",
                         (linha["id"], ja["id"]))
            rel.duplicatas += 1
            continue

        alvo = destino / _nome_do_arquivo(linha["url"], sha)
        with open(caminho_longo(alvo), "wb") as fh:
            fh.write(conteudo)
        cur = conn.execute(
            "INSERT INTO arquivos (sha256, caminho, tamanho, baixado_em) VALUES (?,?,?,?)",
            (sha, str(alvo), len(conteudo),
             datetime.now(timezone.utc).isoformat(timespec="seconds")))
        conn.execute("INSERT OR IGNORE INTO resultado_arquivo "
                     "(resultado_id, arquivo_id, duplicata) VALUES (?,?,0)",
                     (linha["id"], int(cur.lastrowid)))
        rel.baixados += 1

    conn.execute("UPDATE buscas SET pasta = ?, baixado_em = ? WHERE id = ?",
                 (str(destino),
                  datetime.now(timezone.utc).isoformat(timespec="seconds"), busca_id))
    return rel
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `py -m pytest tests/test_download.py -v`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add buscador/download.py tests/test_download.py
git commit -m "feat: download com dedup sha256, pasta por tema e trava de 260 chars"
```

---

