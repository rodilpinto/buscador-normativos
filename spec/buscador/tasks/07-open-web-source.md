---
task: 7
plan: docs/superpowers/plans/2026-09-08-buscador-normativos.md (linhas 998-1109)
reference: spec/buscador/reference/global-constraints.md
---

> ⛔ **SUPERADO — não execute.** Cópia verbatim de uma task do plano de 16 tasks, superado em
> 2026-09-16. Plano vigente: `docs/superpowers/plans/2026-09-16-consolidacao-fase1.md`.

> Extraído verbatim do plano. O plano segue fonte de verdade; esta cópia existe para o
> agente de build não precisar ler 2641 linhas. Divergência entre os dois = o plano ganha.
> **Depends on:** T4 (`Fonte`), T3 (`Resultado`)
> **Onda/trilha:** onda 2 - trilha B (fontes), paralela a T5 e T6

## Task 7: Fonte de web aberta

**Files:**
- Create: `buscador/fontes/web_aberta.py`
- Test: `tests/test_fonte_web_aberta.py`

**Interfaces:**
- Consumes: `Resultado`
- Produces: `FonteWebAberta(buscador_fn: Callable[[str], list[dict]])` — recebe a função de busca por injeção, para o teste não tocar a rede. Todo resultado sai com `procedencia="web-aberta"`, `vinculacao="contexto"`.

- [ ] **Step 1: Escrever o teste que falha**

`tests/test_fonte_web_aberta.py`:

```python
from buscador.fontes.web_aberta import FonteWebAberta


def busca_falsa(termo):
    return [{"titulo": f"Resultado de {termo}", "url": f"https://exemplo.org/{termo}",
             "resumo": "resumo qualquer"}]


def test_web_aberta_marca_procedencia_e_vinculacao_de_contexto():
    out = FonteWebAberta(busca_falsa).buscar(["lgpd"])
    assert len(out) == 1
    assert out[0].procedencia == "web-aberta"
    assert out[0].vinculacao == "contexto"
    assert out[0].categoria == "a-triar"


def test_web_aberta_deduplica_entre_termos():
    def repetida(termo):
        return [{"titulo": "Mesmo", "url": "https://exemplo.org/igual", "resumo": ""}]
    out = FonteWebAberta(repetida).buscar(["a", "b", "c"])
    assert len(out) == 1


def test_web_aberta_sem_resultados_nao_levanta():
    assert FonteWebAberta(lambda t: []).buscar(["x"]) == []
```

- [ ] **Step 2: Rodar e confirmar a falha**

Run: `py -m pytest tests/test_fonte_web_aberta.py -v`
Expected: FAIL com `ModuleNotFoundError`

- [ ] **Step 3: Implementar**

`buscador/fontes/web_aberta.py`:

```python
"""Rede de seguranca: busca generica. Tudo que sai daqui nasce 'a conferir'."""
from __future__ import annotations

from collections.abc import Callable

from buscador.modelos import Resultado
from buscador.normalizar import chave_dedup

BuscaFn = Callable[[str], list[dict]]


class FonteWebAberta:
    nome = "web-aberta"
    procedencia = "web-aberta"
    vinculacao_padrao = "contexto"
    categoria = "a-triar"

    def __init__(self, buscador_fn: BuscaFn) -> None:
        self._buscar_fn = buscador_fn

    def buscar(self, termos: list[str]) -> list[Resultado]:
        vistos: set[str] = set()
        out: list[Resultado] = []
        for termo in termos:
            for item in self._buscar_fn(termo):
                url = item.get("url", "")
                titulo = item.get("titulo", "")
                if not url or not titulo:
                    continue
                chave = chave_dedup(url, titulo)
                if chave in vistos:
                    continue
                vistos.add(chave)
                out.append(Resultado(
                    titulo=titulo,
                    url=url,
                    fonte=self.nome,
                    procedencia=self.procedencia,
                    vinculacao=self.vinculacao_padrao,
                    categoria=self.categoria,
                    ementa=item.get("resumo") or None,
                    chave_dedup=chave,
                ))
        return out
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `py -m pytest tests/test_fonte_web_aberta.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add buscador/fontes/web_aberta.py tests/test_fonte_web_aberta.py
git commit -m "feat: fonte de web aberta com procedencia marcada"
```

---

