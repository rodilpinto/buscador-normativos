---
task: 6
plan: docs/superpowers/plans/2026-09-08-buscador-normativos.md (linhas 753-997)
reference: spec/buscador/reference/global-constraints.md
---

> ⛔ **SUPERADO — não execute.** Cópia verbatim de uma task do plano de 16 tasks, superado em
> 2026-09-16. Plano vigente: `docs/superpowers/plans/2026-09-16-consolidacao-fase1.md`.

> Extraído verbatim do plano. O plano segue fonte de verdade; esta cópia existe para o
> agente de build não precisar ler 2641 linhas. Divergência entre os dois = o plano ganha.
> **Depends on:** T4 (`Fonte`), T3 (`Resultado`)
> **Onda/trilha:** onda 2 - trilha B (fontes), paralela a T5 e T7

## Task 6: Adaptadores Legin (Câmara) e TCU

**Files:**
- Create: `buscador/fontes/legin_camara.py`, `buscador/fontes/tcu.py`, `tests/fixtures/legin_busca.html`, `tests/fixtures/tcu_busca.html`
- Test: `tests/test_fonte_legin.py`, `tests/test_fonte_tcu.py`

**Interfaces:**
- Consumes: mesmo padrão da Task 5
- Produces: `FonteLegin` (categoria `normativos-camara`, vinculação `obrigatorio`), `FonteTCU` (categoria `acordaos-tcu`, vinculação `aplicavel`)

- [ ] **Step 1: Criar as fixtures**

`tests/fixtures/legin_busca.html`:

```html
<html><body>
<ul class="lista-resultados">
  <li><a href="/legin/int/atomes/2020/atodamesa-152-16-dezembro-2020.html">ATO DA MESA Nº 152, DE 16 DE DEZEMBRO DE 2020</a>
      <span class="ementa">Dispõe sobre a proteção de dados pessoais no âmbito da Câmara dos Deputados.</span></li>
</ul>
</body></html>
```

`tests/fixtures/tcu_busca.html`:

```html
<html><body>
<div class="item-resultado">
  <a class="titulo" href="/data/files/acordao-1372-2025.pdf">Acórdão 1372/2025 - Plenário</a>
  <div class="resumo">Levantamento sobre a adequação de organizações federais à LGPD.</div>
</div>
</body></html>
```

- [ ] **Step 2: Escrever os testes que falham**

`tests/test_fonte_legin.py`:

```python
from pathlib import Path
from buscador.fontes.legin_camara import FonteLegin

FIXTURE = Path(__file__).parent / "fixtures" / "legin_busca.html"


def test_extrai_ato_da_mesa_com_ementa_literal():
    out = FonteLegin().extrair(FIXTURE.read_text(encoding="utf-8"))
    assert len(out) == 1
    assert out[0].titulo == "ATO DA MESA Nº 152, DE 16 DE DEZEMBRO DE 2020"
    assert out[0].ementa.startswith("Dispõe sobre a proteção de dados pessoais")
    assert out[0].url.startswith("https://www2.camara.leg.br/legin/")
    assert out[0].ano == 2020


def test_legin_e_normativo_interno_obrigatorio():
    out = FonteLegin().extrair(FIXTURE.read_text(encoding="utf-8"))
    assert out[0].categoria == "normativos-camara"
    assert out[0].vinculacao == "obrigatorio"
    assert out[0].procedencia == "catalogada"


def test_html_vazio_devolve_lista_vazia():
    assert FonteLegin().extrair("<html></html>") == []
```

`tests/test_fonte_tcu.py`:

```python
from pathlib import Path
from buscador.fontes.tcu import FonteTCU

FIXTURE = Path(__file__).parent / "fixtures" / "tcu_busca.html"


def test_extrai_acordao_com_resumo():
    out = FonteTCU().extrair(FIXTURE.read_text(encoding="utf-8"))
    assert len(out) == 1
    assert out[0].titulo == "Acórdão 1372/2025 - Plenário"
    assert out[0].ementa.startswith("Levantamento sobre a adequação")
    assert out[0].ano == 2025


def test_tcu_e_aplicavel_nao_obrigatorio():
    out = FonteTCU().extrair(FIXTURE.read_text(encoding="utf-8"))
    assert out[0].vinculacao == "aplicavel"
    assert out[0].categoria == "acordaos-tcu"


def test_html_vazio_devolve_lista_vazia():
    assert FonteTCU().extrair("<html></html>") == []
```

- [ ] **Step 3: Rodar e confirmar a falha**

Run: `py -m pytest tests/test_fonte_legin.py tests/test_fonte_tcu.py -v`
Expected: FAIL com `ModuleNotFoundError`

- [ ] **Step 4: Implementar**

`buscador/fontes/legin_camara.py`:

```python
"""Adaptador do Legin (normativos internos da Camara)."""
from __future__ import annotations

import re
from urllib.parse import urljoin

import httpx
from selectolax.parser import HTMLParser

from buscador.modelos import Resultado
from buscador.normalizar import chave_dedup

BASE = "https://www2.camara.leg.br"
ANO = re.compile(r"\b(19|20)\d{2}\b")


class FonteLegin:
    nome = "legin-camara"
    procedencia = "catalogada"
    vinculacao_padrao = "obrigatorio"
    categoria = "normativos-camara"

    def __init__(self, cliente: httpx.Client | None = None) -> None:
        self._cliente = cliente

    def extrair(self, html: str) -> list[Resultado]:
        doc = HTMLParser(html)
        out: list[Resultado] = []
        for item in doc.css("ul.lista-resultados li"):
            link = item.css_first("a")
            if link is None or not link.attributes.get("href"):
                continue
            titulo = link.text(strip=True)
            url = urljoin(BASE, link.attributes["href"])
            no = item.css_first("span.ementa")
            m = ANO.search(titulo)
            out.append(Resultado(
                titulo=titulo,
                url=url,
                fonte=self.nome,
                procedencia=self.procedencia,
                vinculacao=self.vinculacao_padrao,
                categoria=self.categoria,
                ementa=no.text(strip=True) if no else None,
                ano=int(m.group(0)) if m else None,
                chave_dedup=chave_dedup(url, titulo),
            ))
        return out

    def buscar(self, termos: list[str]) -> list[Resultado]:
        cliente = self._cliente or httpx.Client(timeout=20.0, follow_redirects=True)
        vistos: set[str] = set()
        out: list[Resultado] = []
        for termo in termos:
            r = cliente.get(f"{BASE}/legin/busca", params={"termo": termo})
            r.raise_for_status()
            for res in self.extrair(r.text):
                if res.chave_dedup not in vistos:
                    vistos.add(res.chave_dedup)
                    out.append(res)
        return out
```

`buscador/fontes/tcu.py`:

```python
"""Adaptador do portal do TCU (acordaos e pecas)."""
from __future__ import annotations

import re
from urllib.parse import urljoin

import httpx
from selectolax.parser import HTMLParser

from buscador.modelos import Resultado
from buscador.normalizar import chave_dedup

BASE = "https://portal.tcu.gov.br"
ANO = re.compile(r"\b(19|20)\d{2}\b")


class FonteTCU:
    nome = "tcu"
    procedencia = "catalogada"
    vinculacao_padrao = "aplicavel"
    categoria = "acordaos-tcu"

    def __init__(self, cliente: httpx.Client | None = None) -> None:
        self._cliente = cliente

    def extrair(self, html: str) -> list[Resultado]:
        doc = HTMLParser(html)
        out: list[Resultado] = []
        for item in doc.css("div.item-resultado"):
            link = item.css_first("a.titulo")
            if link is None or not link.attributes.get("href"):
                continue
            titulo = link.text(strip=True)
            url = urljoin(BASE, link.attributes["href"])
            no = item.css_first("div.resumo")
            m = ANO.search(titulo)
            out.append(Resultado(
                titulo=titulo,
                url=url,
                fonte=self.nome,
                procedencia=self.procedencia,
                vinculacao=self.vinculacao_padrao,
                categoria=self.categoria,
                ementa=no.text(strip=True) if no else None,
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

Run: `py -m pytest tests/test_fonte_legin.py tests/test_fonte_tcu.py -v`
Expected: 6 passed

- [ ] **Step 6: Commit**

```bash
git add buscador/fontes/legin_camara.py buscador/fontes/tcu.py tests/test_fonte_legin.py tests/test_fonte_tcu.py tests/fixtures/legin_busca.html tests/fixtures/tcu_busca.html
git commit -m "feat: adaptadores Legin e TCU"
```

---

