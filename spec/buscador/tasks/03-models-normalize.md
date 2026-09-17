---
task: 3
plan: docs/superpowers/plans/2026-09-08-buscador-normativos.md (linhas 352-480)
reference: spec/buscador/reference/global-constraints.md
---

> ⛔ **SUPERADO — não execute.** Cópia verbatim de uma task do plano de 16 tasks, superado em
> 2026-09-16. Plano vigente: `docs/superpowers/plans/2026-09-16-consolidacao-fase1.md`.

> Extraído verbatim do plano. O plano segue fonte de verdade; esta cópia existe para o
> agente de build não precisar ler 2641 linhas. Divergência entre os dois = o plano ganha.
> **Depends on:** T1 (pacote `buscador/`)
> **Onda/trilha:** onda 1 - gate

## Task 3: Modelos e normalização

**Files:**
- Create: `buscador/modelos.py`, `buscador/normalizar.py`
- Test: `tests/test_normalizar.py`

**Interfaces:**
- Consumes: nada
- Produces: `Resultado` (dataclass), `normalizar_url(url: str) -> str`, `normalizar_titulo(t: str) -> str`, `chave_dedup(url: str, titulo: str) -> str`

A chave de dedup é o que impede o mesmo normativo de aparecer duas vezes vindo de fontes diferentes.

- [ ] **Step 1: Escrever o teste que falha**

`tests/test_normalizar.py`:

```python
from buscador.normalizar import normalizar_url, normalizar_titulo, chave_dedup


def test_normalizar_url_remove_query_e_fragmento_e_barra_final():
    assert normalizar_url("https://X.gov.br/Lei.htm?a=1#topo") == "https://x.gov.br/lei.htm"
    assert normalizar_url("https://x.gov.br/pasta/") == "https://x.gov.br/pasta"


def test_normalizar_titulo_remove_acento_pontuacao_e_caixa():
    assert normalizar_titulo("Lei nº 13.709/2018 (LGPD)") == "lei n 13 709 2018 lgpd"


def test_chave_dedup_igual_para_mesma_url_com_ruido():
    a = chave_dedup("https://x.gov.br/L1.htm?x=1", "Lei nº 1")
    b = chave_dedup("https://X.gov.br/L1.htm", "Lei n. 1")
    assert a == b


def test_chave_dedup_diferente_para_normativos_diferentes():
    a = chave_dedup("https://x.gov.br/L1.htm", "Lei nº 1")
    b = chave_dedup("https://x.gov.br/L2.htm", "Lei nº 2")
    assert a != b
```

- [ ] **Step 2: Rodar e confirmar a falha**

Run: `py -m pytest tests/test_normalizar.py -v`
Expected: FAIL com `ModuleNotFoundError`

- [ ] **Step 3: Implementar**

`buscador/normalizar.py`:

```python
"""Normalizacao usada para deduplicar resultados vindos de fontes diferentes."""
from __future__ import annotations

import hashlib
import re
import unicodedata
from urllib.parse import urlsplit, urlunsplit


def normalizar_url(url: str) -> str:
    p = urlsplit(url.strip())
    caminho = p.path.rstrip("/") or "/"
    return urlunsplit((p.scheme.lower(), p.netloc.lower(), caminho, "", "")).rstrip("/")


def normalizar_titulo(titulo: str) -> str:
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFD", titulo)
        if unicodedata.category(c) != "Mn"
    )
    limpo = re.sub(r"[^0-9a-zA-Z]+", " ", sem_acento.lower())
    return re.sub(r"\s+", " ", limpo).strip()


def chave_dedup(url: str, titulo: str) -> str:
    """A URL manda. O titulo entra so quando a URL nao e informativa."""
    base = normalizar_url(url)
    if not base or base.count("/") <= 2:
        base = normalizar_titulo(titulo)
    return hashlib.sha256(base.encode("utf-8")).hexdigest()[:32]
```

`buscador/modelos.py`:

```python
"""Dataclasses do dominio. Espelham as colunas de `resultados`."""
from __future__ import annotations

from dataclasses import dataclass

Procedencia = str  # 'catalogada' | 'web-aberta'
Vinculacao = str   # 'obrigatorio' | 'aplicavel' | 'contexto'


@dataclass
class Resultado:
    titulo: str
    url: str
    fonte: str
    procedencia: Procedencia
    vinculacao: Vinculacao
    chave_dedup: str
    tipo: str | None = None
    ano: int | None = None
    ementa: str | None = None
    ementa_llm: str | None = None
    categoria: str | None = None
    ja_tenho: bool = False
    ja_tenho_onde: str | None = None
    pre_marca: str | None = None
    pre_motivo: str | None = None
    id: int | None = None
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `py -m pytest tests/test_normalizar.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add buscador/modelos.py buscador/normalizar.py tests/test_normalizar.py
git commit -m "feat: modelos e chave de deduplicacao"
```

---

