---
task: 10
plan: docs/superpowers/plans/2026-09-08-buscador-normativos.md (linhas 1413-1532)
reference: spec/buscador/reference/global-constraints.md
---

> Extraído verbatim do plano. O plano segue fonte de verdade; esta cópia existe para o
> agente de build não precisar ler 2641 linhas. Divergência entre os dois = o plano ganha.
> **Depends on:** T3 (`Resultado`)
> **Onda/trilha:** onda 2 - trilha D (triagem-core)

## Task 10: Pré-marcação com justificativa

**Files:**
- Create: `buscador/premarcacao.py`
- Test: `tests/test_premarcacao.py`

**Interfaces:**
- Consumes: `Resultado`
- Produces: `premarcar(r: Resultado) -> Resultado` (preenche `pre_marca` e `pre_motivo`), `premarcar_todos(rs: list[Resultado]) -> list[Resultado]`

Mecanismos **M3** e **M4**. As duas travas da spec §7 são regras aqui, e têm teste próprio.

- [ ] **Step 1: Escrever o teste que falha**

`tests/test_premarcacao.py`:

```python
from buscador.modelos import Resultado
from buscador.premarcacao import premarcar, premarcar_todos


def _res(**kw):
    base = dict(titulo="t", url="u", fonte="f", procedencia="catalogada",
                vinculacao="aplicavel", chave_dedup="k")
    base.update(kw)
    return Resultado(**base)


def test_obrigatorio_e_sempre_fica():
    r = premarcar(_res(vinculacao="obrigatorio"))
    assert r.pre_marca == "fica"
    assert "obrigat" in r.pre_motivo.lower()


def test_obrigatorio_nunca_vira_sai_mesmo_se_ja_tenho():
    r = premarcar(_res(vinculacao="obrigatorio", ja_tenho=True))
    assert r.pre_marca == "fica"


def test_web_aberta_nunca_e_premarcada_fica():
    r = premarcar(_res(procedencia="web-aberta", vinculacao="aplicavel"))
    assert r.pre_marca == "sai"
    assert "web aberta" in r.pre_motivo.lower()


def test_contexto_nasce_desmarcado():
    r = premarcar(_res(vinculacao="contexto"))
    assert r.pre_marca == "sai"


def test_ja_tenho_nao_obrigatorio_nasce_desmarcado():
    r = premarcar(_res(vinculacao="aplicavel", ja_tenho=True))
    assert r.pre_marca == "sai"
    assert "acervo" in r.pre_motivo.lower()


def test_aplicavel_novo_de_fonte_catalogada_fica():
    r = premarcar(_res(vinculacao="aplicavel"))
    assert r.pre_marca == "fica"


def test_todo_resultado_sai_com_motivo_preenchido():
    rs = premarcar_todos([_res(), _res(vinculacao="contexto"),
                          _res(procedencia="web-aberta", vinculacao="contexto")])
    assert all(r.pre_motivo for r in rs)
```

- [ ] **Step 2: Rodar e confirmar a falha**

Run: `py -m pytest tests/test_premarcacao.py -v`
Expected: FAIL com `ModuleNotFoundError`

- [ ] **Step 3: Implementar**

`buscador/premarcacao.py`:

```python
"""Pre-marcacao com justificativa (M4). A ordem das regras E a especificacao."""
from __future__ import annotations

from buscador.modelos import Resultado


def premarcar(r: Resultado) -> Resultado:
    # Trava 1 (spec 7): obrigatorio nunca e desmarcado, aconteca o que acontecer.
    if r.vinculacao == "obrigatorio":
        r.pre_marca, r.pre_motivo = "fica", "Vinculacao obrigatoria para a CD"
        return r
    # Trava 2 (spec 7): web aberta nunca nasce marcada.
    if r.procedencia == "web-aberta":
        r.pre_marca, r.pre_motivo = "sai", "Veio da web aberta: procedencia a conferir"
        return r
    if r.ja_tenho:
        r.pre_marca, r.pre_motivo = "sai", "Ja existe no acervo"
        return r
    if r.vinculacao == "contexto":
        r.pre_marca, r.pre_motivo = "sai", "Material de contexto, sem vinculacao direta"
        return r
    r.pre_marca, r.pre_motivo = "fica", "Aplicavel, de fonte catalogada, ainda nao no acervo"
    return r


def premarcar_todos(resultados: list[Resultado]) -> list[Resultado]:
    return [premarcar(r) for r in resultados]
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `py -m pytest tests/test_premarcacao.py -v`
Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add buscador/premarcacao.py tests/test_premarcacao.py
git commit -m "feat: pre-marcacao com justificativa e as duas travas anti-ancoragem"
```

---

