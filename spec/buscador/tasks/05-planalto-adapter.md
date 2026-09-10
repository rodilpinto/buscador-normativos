---
task: 5
plan: docs/superpowers/plans/2026-09-08-buscador-normativos.md (linhas 597-752)
reference: spec/buscador/reference/global-constraints.md
---

> Extraído verbatim do plano. O plano segue fonte de verdade; esta cópia existe para o
> agente de build não precisar ler 2641 linhas. Divergência entre os dois = o plano ganha.
> **Depends on:** T4 (`Fonte`), T3 (`Resultado`)
> **Onda/trilha:** onda 2 - trilha B (fontes), paralela a T6 e T7

## Task 5: Adaptador do Planalto

**Files:**
- Create: `buscador/fontes/planalto.py`, `tests/fixtures/planalto_busca.html`
- Test: `tests/test_fonte_planalto.py`

**Interfaces:**
- Consumes: `Fonte`, `Resultado`
- Produces: `FontePlanalto(cliente: httpx.Client | None = None)` com `.buscar(termos) -> list[Resultado]` e `.extrair(html: str) -> list[Resultado]`

`extrair` é separado de `buscar` **de propósito**: o teste roda sobre a fixture, sem rede.

- [ ] **Step 1: Salvar a fixture**

Baixe uma página de resultado real uma única vez e salve. Se não houver rede, crie o arquivo à mão com esta estrutura mínima:

`tests/fixtures/planalto_busca.html`:

```html
<html><body>
<div class="resultado">
  <a href="/ccivil_03/_ato2015-2018/2018/lei/L13709compilado.htm">LEI Nº 13.709, DE 14 DE AGOSTO DE 2018</a>
  <p class="ementa">Lei Geral de Proteção de Dados Pessoais (LGPD).</p>
</div>
<div class="resultado">
  <a href="/ccivil_03/_ato2019-2022/2019/lei/l13853.htm">LEI Nº 13.853, DE 8 DE JULHO DE 2019</a>
  <p class="ementa">Altera a Lei nº 13.709, de 14 de agosto de 2018.</p>
</div>
</body></html>
```

- [ ] **Step 2: Escrever o teste que falha**

`tests/test_fonte_planalto.py`:

```python
from pathlib import Path
from buscador.fontes.planalto import FontePlanalto

FIXTURE = Path(__file__).parent / "fixtures" / "planalto_busca.html"


def test_extrai_titulo_url_absoluta_e_ementa_literais():
    html = FIXTURE.read_text(encoding="utf-8")
    out = FontePlanalto().extrair(html)
    assert len(out) == 2
    assert out[0].titulo == "LEI Nº 13.709, DE 14 DE AGOSTO DE 2018"
    assert out[0].url.startswith("https://www.planalto.gov.br/ccivil_03/")
    assert out[0].ementa == "Lei Geral de Proteção de Dados Pessoais (LGPD)."


def test_extrai_o_ano_do_titulo():
    out = FontePlanalto().extrair(FIXTURE.read_text(encoding="utf-8"))
    assert out[0].ano == 2018
    assert out[1].ano == 2019


def test_planalto_e_catalogada_e_obrigatoria():
    out = FontePlanalto().extrair(FIXTURE.read_text(encoding="utf-8"))
    assert out[0].procedencia == "catalogada"
    assert out[0].vinculacao == "obrigatorio"
    assert out[0].categoria == "legislacao-federal"


def test_html_vazio_devolve_lista_vazia_sem_levantar():
    assert FontePlanalto().extrair("<html></html>") == []
```

- [ ] **Step 3: Rodar e confirmar a falha**

Run: `py -m pytest tests/test_fonte_planalto.py -v`
Expected: FAIL com `ModuleNotFoundError`

- [ ] **Step 4: Implementar**

`buscador/fontes/planalto.py`:

```python
"""Adaptador do Planalto (legislacao federal)."""
from __future__ import annotations

import re
from urllib.parse import urljoin

import httpx
from selectolax.parser import HTMLParser

from buscador.modelos import Resultado
from buscador.normalizar import chave_dedup

BASE = "https://www.planalto.gov.br"
ANO = re.compile(r"\b(19|20)\d{2}\b")


class FontePlanalto:
    nome = "planalto"
    procedencia = "catalogada"
    vinculacao_padrao = "obrigatorio"
    categoria = "legislacao-federal"

    def __init__(self, cliente: httpx.Client | None = None) -> None:
        self._cliente = cliente

    def extrair(self, html: str) -> list[Resultado]:
        doc = HTMLParser(html)
        out: list[Resultado] = []
        for bloco in doc.css("div.resultado"):
            link = bloco.css_first("a")
            if link is None or not link.attributes.get("href"):
                continue
            titulo = link.text(strip=True)
            url = urljoin(BASE, link.attributes["href"])
            ementa_no = bloco.css_first("p.ementa")
            ementa = ementa_no.text(strip=True) if ementa_no else None
            m = ANO.search(titulo)
            out.append(Resultado(
                titulo=titulo,
                url=url,
                fonte=self.nome,
                procedencia=self.procedencia,
                vinculacao=self.vinculacao_padrao,
                categoria=self.categoria,
                ementa=ementa,
                ano=int(m.group(0)) if m else None,
                chave_dedup=chave_dedup(url, titulo),
            ))
        return out

    def buscar(self, termos: list[str]) -> list[Resultado]:
        cliente = self._cliente or httpx.Client(timeout=20.0, follow_redirects=True)
        vistos: set[str] = set()
        out: list[Resultado] = []
        for termo in termos:
            r = cliente.get(f"{BASE}/busca", params={"q": termo})
            r.raise_for_status()
            for res in self.extrair(r.text):
                if res.chave_dedup not in vistos:
                    vistos.add(res.chave_dedup)
                    out.append(res)
        return out
```

- [ ] **Step 5: Rodar e confirmar que passa**

Run: `py -m pytest tests/test_fonte_planalto.py -v`
Expected: 4 passed

- [ ] **Step 6: Commit**

```bash
git add buscador/fontes/planalto.py tests/test_fonte_planalto.py tests/fixtures/planalto_busca.html
git commit -m "feat: adaptador do Planalto com fixture e teste de contrato"
```

---

