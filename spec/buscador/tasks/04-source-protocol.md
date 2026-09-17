---
task: 4
plan: docs/superpowers/plans/2026-09-08-buscador-normativos.md (linhas 481-596)
reference: spec/buscador/reference/global-constraints.md
---

> ⛔ **SUPERADO — não execute.** Cópia verbatim de uma task do plano de 16 tasks, superado em
> 2026-09-16. Plano vigente: `docs/superpowers/plans/2026-09-16-consolidacao-fase1.md`.

> Extraído verbatim do plano. O plano segue fonte de verdade; esta cópia existe para o
> agente de build não precisar ler 2641 linhas. Divergência entre os dois = o plano ganha.
> **Depends on:** T3 (`Resultado`)
> **Onda/trilha:** onda 2 - trilha B (fontes)

## Task 4: Protocolo `Fonte` e catálogo

**Files:**
- Create: `buscador/fontes/base.py`
- Test: `tests/test_fontes_base.py`

**Interfaces:**
- Consumes: `Resultado` da Task 3
- Produces: `Fonte` (Protocol com `nome: str`, `procedencia: str`, `vinculacao_padrao: str`, `categoria: str`, `buscar(termos: list[str]) -> list[Resultado]`), `FonteFake` (para testes), `CATALOGO: dict[str, Fonte]`, `registrar(fonte)`

- [ ] **Step 1: Escrever o teste que falha**

`tests/test_fontes_base.py`:

```python
from buscador.fontes.base import Fonte, FonteFake, CATALOGO, registrar
from buscador.modelos import Resultado


def test_fonte_fake_devolve_resultados_com_procedencia_e_chave():
    f = FonteFake(nome="fake", itens=[("Lei nº 1", "https://x.gov.br/l1.htm")])
    out = f.buscar(["lgpd"])
    assert len(out) == 1
    assert isinstance(out[0], Resultado)
    assert out[0].procedencia == "catalogada"
    assert out[0].fonte == "fake"
    assert out[0].chave_dedup


def test_fonte_fake_satisfaz_o_protocolo():
    assert isinstance(FonteFake(nome="f", itens=[]), Fonte)


def test_registrar_adiciona_ao_catalogo():
    f = FonteFake(nome="registrada", itens=[])
    registrar(f)
    assert CATALOGO["registrada"] is f
```

- [ ] **Step 2: Rodar e confirmar a falha**

Run: `py -m pytest tests/test_fontes_base.py -v`
Expected: FAIL com `ModuleNotFoundError`

- [ ] **Step 3: Implementar**

`buscador/fontes/base.py`:

```python
"""Protocolo comum das fontes. Cada adaptador e trocavel e testavel isolado."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from buscador.modelos import Resultado
from buscador.normalizar import chave_dedup


@runtime_checkable
class Fonte(Protocol):
    nome: str
    procedencia: str
    vinculacao_padrao: str
    categoria: str

    def buscar(self, termos: list[str]) -> list[Resultado]: ...


CATALOGO: dict[str, Fonte] = {}


def registrar(fonte: Fonte) -> None:
    CATALOGO[fonte.nome] = fonte


@dataclass
class FonteFake:
    """Fonte deterministica para teste. Nunca toca a rede."""
    nome: str
    itens: list[tuple[str, str]]
    procedencia: str = "catalogada"
    vinculacao_padrao: str = "aplicavel"
    categoria: str = "fake"
    chamadas: list[list[str]] = field(default_factory=list)

    def buscar(self, termos: list[str]) -> list[Resultado]:
        self.chamadas.append(list(termos))
        return [
            Resultado(
                titulo=t,
                url=u,
                fonte=self.nome,
                procedencia=self.procedencia,
                vinculacao=self.vinculacao_padrao,
                categoria=self.categoria,
                chave_dedup=chave_dedup(u, t),
            )
            for t, u in self.itens
        ]
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `py -m pytest tests/test_fontes_base.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add buscador/fontes/base.py tests/test_fontes_base.py
git commit -m "feat: protocolo Fonte, catalogo e FonteFake"
```

---

