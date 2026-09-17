---
task: 8
plan: docs/superpowers/plans/2026-09-08-buscador-normativos.md (linhas 1110-1288)
reference: spec/buscador/reference/global-constraints.md
---

> ⛔ **SUPERADO — não execute.** Cópia verbatim de uma task do plano de 16 tasks, superado em
> 2026-09-16. Plano vigente: `docs/superpowers/plans/2026-09-16-consolidacao-fase1.md`.

> Extraído verbatim do plano. O plano segue fonte de verdade; esta cópia existe para o
> agente de build não precisar ler 2641 linhas. Divergência entre os dois = o plano ganha.
> **Depends on:** T1 (`Config`)
> **Onda/trilha:** onda 2 - trilha C (llm)

## Task 8: Palavras-chave (regra + LLM opcional)

**Files:**
- Create: `buscador/llm.py`, `buscador/palavras_chave.py`
- Test: `tests/test_palavras_chave.py`

**Interfaces:**
- Consumes: `Config`
- Produces: `LLM` (Protocol com `completar(prompt: str) -> str`), `NullLLM`, `LLMOpenAICompat(base_url, modelo, chave)`, `expandir(tema: str, llm: LLM | None = None) -> list[str]`

**Requisito duro:** com `llm=None` a função devolve termos úteis. O LLM só acrescenta.

- [ ] **Step 1: Escrever o teste que falha**

`tests/test_palavras_chave.py`:

```python
from buscador.llm import NullLLM
from buscador.palavras_chave import expandir


def test_expandir_sem_llm_devolve_o_tema_e_sinonimos_conhecidos():
    termos = expandir("LGPD")
    assert "LGPD" in termos
    assert any("dados pessoais" in t.lower() for t in termos)


def test_expandir_sem_llm_nunca_devolve_lista_vazia():
    assert expandir("tema totalmente desconhecido xyz") != []


def test_expandir_com_null_llm_e_igual_a_sem_llm():
    assert expandir("LGPD", NullLLM()) == expandir("LGPD")


def test_expandir_com_llm_acrescenta_sem_perder_os_de_regra():
    class LLMFalso:
        def completar(self, prompt):
            return "termo extra 1\ntermo extra 2"
    termos = expandir("LGPD", LLMFalso())
    assert "LGPD" in termos
    assert "termo extra 1" in termos


def test_expandir_deduplica_e_preserva_ordem():
    class LLMRepetido:
        def completar(self, prompt):
            return "LGPD\nLGPD\nnovo"
    termos = expandir("LGPD", LLMRepetido())
    assert termos.count("LGPD") == 1
    assert termos[0] == "LGPD"


def test_expandir_tolera_llm_que_quebra():
    class LLMQuebrado:
        def completar(self, prompt):
            raise RuntimeError("sem rede")
    assert "LGPD" in expandir("LGPD", LLMQuebrado())
```

- [ ] **Step 2: Rodar e confirmar a falha**

Run: `py -m pytest tests/test_palavras_chave.py -v`
Expected: FAIL com `ModuleNotFoundError`

- [ ] **Step 3: Implementar**

`buscador/llm.py`:

```python
"""LLM e OPCIONAL. Com NullLLM o sistema roda inteiro."""
from __future__ import annotations

from typing import Protocol, runtime_checkable

import httpx


@runtime_checkable
class LLM(Protocol):
    def completar(self, prompt: str) -> str: ...


class NullLLM:
    """Nao chama nada. Existe para o resto do codigo nao precisar de `if llm`."""

    def completar(self, prompt: str) -> str:
        return ""


class LLMOpenAICompat:
    """Serve nuvem e LLM local: ambos falam a API OpenAI-compativel."""

    def __init__(self, base_url: str, modelo: str, chave: str | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.modelo = modelo
        self.chave = chave

    def completar(self, prompt: str) -> str:
        cabecalhos = {"Authorization": f"Bearer {self.chave}"} if self.chave else {}
        r = httpx.post(
            f"{self.base_url}/chat/completions",
            headers=cabecalhos,
            json={"model": self.modelo,
                  "messages": [{"role": "user", "content": prompt}],
                  "temperature": 0},
            timeout=60.0,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
```

`buscador/palavras_chave.py`:

```python
"""Expansao do tema em termos de busca. Regra primeiro; LLM so acrescenta."""
from __future__ import annotations

import logging

from buscador.llm import LLM

log = logging.getLogger(__name__)

SINONIMOS: dict[str, list[str]] = {
    "lgpd": ["Lei 13.709", "proteção de dados pessoais", "tratamento de dados pessoais",
             "encarregado de dados pessoais", "ANPD"],
    "ia": ["inteligência artificial", "governança de IA", "sistema de IA"],
    "governanca": ["governança", "governança corporativa", "controle interno"],
    "auditoria": ["auditoria interna", "controle interno", "papel de trabalho"],
}

PROMPT = (
    "Liste de 5 a 8 termos de busca em portugues para encontrar normativos e "
    "documentos oficiais brasileiros sobre o tema abaixo. Um termo por linha, "
    "sem numeracao, sem explicacao.\n\nTema: {tema}"
)


def _por_regra(tema: str) -> list[str]:
    termos = [tema.strip()]
    chave = tema.strip().lower()
    for gatilho, extras in SINONIMOS.items():
        if gatilho in chave:
            termos.extend(extras)
    return termos


def expandir(tema: str, llm: LLM | None = None) -> list[str]:
    termos = _por_regra(tema)
    if llm is not None:
        try:
            bruto = llm.completar(PROMPT.format(tema=tema))
            termos.extend(l.strip() for l in bruto.splitlines() if l.strip())
        except Exception:
            log.warning("LLM falhou na expansao; seguindo so com regra", exc_info=True)
    vistos: set[str] = set()
    saida: list[str] = []
    for t in termos:
        if t.lower() not in vistos:
            vistos.add(t.lower())
            saida.append(t)
    return saida
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `py -m pytest tests/test_palavras_chave.py -v`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add buscador/llm.py buscador/palavras_chave.py tests/test_palavras_chave.py
git commit -m "feat: palavras-chave por regra com LLM opcional e tolerante a falha"
```

---

