---
task: 9
plan: docs/superpowers/plans/2026-09-08-buscador-normativos.md (linhas 1289-1412)
reference: spec/buscador/reference/global-constraints.md
---

> Extraído verbatim do plano. O plano segue fonte de verdade; esta cópia existe para o
> agente de build não precisar ler 2641 linhas. Divergência entre os dois = o plano ganha.
> **Depends on:** T3 (`Resultado`, `normalizar_titulo`)
> **Onda/trilha:** onda 2 - trilha D (triagem-core)

## Task 9: Índice do acervo e selo "já tenho"

**Files:**
- Create: `buscador/acervo.py`
- Test: `tests/test_acervo.py`

**Interfaces:**
- Consumes: `Resultado`, `normalizar_titulo`
- Produces: `indexar(raizes: list[Path]) -> dict[str, str]` (título normalizado → caminho), `sha256_arquivo(p: Path) -> str`, `marcar_ja_tenho(resultados: list[Resultado], indice: dict[str,str]) -> list[Resultado]`

Este é o mecanismo **M1** da spec: tira do caminho o que já existe no acervo.

- [ ] **Step 1: Escrever o teste que falha**

`tests/test_acervo.py`:

```python
from pathlib import Path
from buscador.acervo import indexar, marcar_ja_tenho, sha256_arquivo
from buscador.modelos import Resultado


def _res(titulo, url="https://x/y"):
    return Resultado(titulo=titulo, url=url, fonte="f", procedencia="catalogada",
                     vinculacao="aplicavel", chave_dedup=titulo)


def test_indexar_encontra_arquivos_por_titulo_normalizado(tmp_path):
    (tmp_path / "ATO DA MESA Nº 152.docx").write_text("x", encoding="utf-8")
    indice = indexar([tmp_path])
    assert "ato da mesa n 152" in indice


def test_indexar_ignora_pasta_inexistente_sem_levantar(tmp_path):
    assert indexar([tmp_path / "nao-existe"]) == {}


def test_marcar_ja_tenho_aplica_selo_e_caminho(tmp_path):
    (tmp_path / "Lei nº 13.709.pdf").write_text("x", encoding="utf-8")
    indice = indexar([tmp_path])
    out = marcar_ja_tenho([_res("Lei nº 13.709")], indice)
    assert out[0].ja_tenho is True
    assert out[0].ja_tenho_onde.endswith("Lei nº 13.709.pdf")


def test_marcar_ja_tenho_deixa_intacto_o_que_nao_existe(tmp_path):
    out = marcar_ja_tenho([_res("Norma inedita")], indexar([tmp_path]))
    assert out[0].ja_tenho is False
    assert out[0].ja_tenho_onde is None


def test_sha256_arquivo_e_estavel(tmp_path):
    p = tmp_path / "a.txt"
    p.write_bytes(b"conteudo")
    assert sha256_arquivo(p) == sha256_arquivo(p)
    assert len(sha256_arquivo(p)) == 64
```

- [ ] **Step 2: Rodar e confirmar a falha**

Run: `py -m pytest tests/test_acervo.py -v`
Expected: FAIL com `ModuleNotFoundError`

- [ ] **Step 3: Implementar**

`buscador/acervo.py`:

```python
"""Indice do acervo que ja existe. Mecanismo M1: reduzir decisoes."""
from __future__ import annotations

import hashlib
from pathlib import Path

from buscador.modelos import Resultado
from buscador.normalizar import normalizar_titulo

EXTENSOES = {".pdf", ".docx", ".doc", ".xlsx", ".xls", ".htm", ".html", ".md", ".txt"}


def sha256_arquivo(caminho: Path) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as fh:
        for bloco in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(bloco)
    return h.hexdigest()


def indexar(raizes: list[Path]) -> dict[str, str]:
    """Titulo normalizado (sem extensao) -> caminho absoluto."""
    indice: dict[str, str] = {}
    for raiz in raizes:
        if not raiz.exists():
            continue
        for p in raiz.rglob("*"):
            if p.is_file() and p.suffix.lower() in EXTENSOES:
                indice.setdefault(normalizar_titulo(p.stem), str(p))
    return indice


def marcar_ja_tenho(resultados: list[Resultado],
                    indice: dict[str, str]) -> list[Resultado]:
    for r in resultados:
        caminho = indice.get(normalizar_titulo(r.titulo))
        if caminho:
            r.ja_tenho = True
            r.ja_tenho_onde = caminho
    return resultados
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `py -m pytest tests/test_acervo.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add buscador/acervo.py tests/test_acervo.py
git commit -m "feat: indice do acervo e selo ja-tenho (M1)"
```

---

