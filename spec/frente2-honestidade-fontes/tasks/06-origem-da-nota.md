---
task: 6
fase: "Fase 3 — Procedência da nota"
plan: docs/superpowers/plans/2026-09-22-frente2-honestidade-fontes.md (linhas 2206-2334)
reference: spec/frente2-honestidade-fontes/reference/global-constraints.md
depends_on: [T1]
---

> Extraído **verbatim** do plano v4 (linhas 2206-2334). **O plano segue fonte de verdade**:
> divergência entre o plano e esta cópia → o plano ganha. Status em `../execucao/TODOS.md` — **não marque
> os checkboxes aqui**. Antes de começar, ler `../reference/global-constraints.md` (Global
> Constraints, Estrutura de arquivos, BASELINE por task). Ordem e dependências: `../00-overview.md`.

# T6 · `score_relevance_com_origem` — a nota diz de onde veio

**Fase 3 — Procedência da nota.**

## Depende de

- **T1** — `ORIGENS_RELEVANCIA` em `models.py`

**Arquivos compartilhados com outras tasks:** `llm/gemini_client.py` · `llm/__init__.py` · `test_llm_phase3.py` · runner. Nenhum arquivo da Fase 2.

## Critérios de aceite

> Derivados do próprio plano (os "Ver passar", "Expected" e gates da task e das Global
> Constraints) — **nenhum critério novo**. Números são previsões do plano: se o observado
> divergir, contar os `def test_` do bloco da task antes de suspeitar do código.

- Antes de implementar: `python test_llm_phase3.py | tail -5` → `Total: 54 | PASS: 53 | FAIL: 1` (Step 2).
- Depois: **`Total: 63 | PASS: 63 | FAIL: 0`** (Step 4).
- `score_relevance` vira wrapper com o contrato antigo (os 53 testes antigos intactos); `git grep -n 'score_relevance\b' -- '*.py'` → só o wrapper, `__init__.py`, `app.py` (a T9 troca) e os testes.
- Docstring de módulo (`gemini_client.py:11`) e do pacote atualizadas; frases sobre Gemini/API key **intocadas** (emenda B7, frente 5).
- `BASELINE["test_llm_phase3.py"] = 63`; runner TUDO VERDE (total **269**); golden OK; auditoria; commit + push.

---

## Conteúdo da task (verbatim do plano)

### Task 6: Origem da nota de relevância (`gemini_client.py`)

**Files:** `llm/gemini_client.py` (`:1-14` docstring de módulo; `:340-430`); `llm/__init__.py`; `test_llm_phase3.py` (seção 9, antes do `# Summary`); `tools/run_all_tests.py`.

**Interfaces — Produces:** `score_relevance_com_origem(topic, results, keywords=None) -> list[tuple[float, str]]`; `score_relevance` inalterada (wrapper); ambas exportadas por `llm/__init__.py`.

- [ ] **Step 1: Testes** — em `test_llm_phase3.py`, **antes** do bloco `# Summary` (10 `record`s):

```python
# ===========================================================================
# 9. Origem da nota (frente 2, spec 2026-09-22 §3.4)
# ===========================================================================
run_section("9. Origem da nota de relevancia")

try:
    from llm import score_relevance_com_origem
    from llm import gemini_client as _gc
    from models import ORIGENS_RELEVANCIA

    _docs = [{"nome": "Lei 13.709", "ementa": "Dispoe sobre protecao de dados pessoais e privacidade."},
             {"nome": "COBIT", "ementa": "Framework de governanca de TI."}]

    # sem chave (o topo do arquivo garante): heuristica
    pares = score_relevance_com_origem("tema", _docs, ["dados pessoais", "privacidade"])
    record("sem LLM devolve pares (nota, origem)", all(isinstance(p, tuple) and len(p) == 2 for p in pares))
    record("sem LLM a origem e 'heuristica'", all(o == "heuristica" for _, o in pares), str(pares))
    record("nota heuristica = fracao das keywords na ementa", abs(pares[0][0] - 1.0) < 1e-9 and pares[1][0] == 0.0, str(pares))
    record("toda origem esta em ORIGENS_RELEVANCIA", all(o in ORIGENS_RELEVANCIA for _, o in pares))

    # sem chave e sem keywords: nao ha o que calcular -> fallback_erro rotulado
    pares2 = score_relevance_com_origem("tema", _docs, None)
    record("sem LLM e sem keywords: 0.5 rotulado fallback_erro",
           all(p == (0.5, "fallback_erro") for p in pares2), str(pares2))

    # wrapper preserva o contrato antigo
    record("score_relevance == notas de score_relevance_com_origem",
           score_relevance("tema", _docs, ["dados pessoais", "privacidade"]) == [n for n, _ in pares])

    # com LLM "disponivel" mas lote vazio: fallback_erro (dublando is_available e _generate)
    _orig_avail, _orig_gen = _gc.is_available, _gc._generate
    try:
        _gc.is_available = lambda: True
        _gc._generate = lambda prompt, temperature=0.0, max_tokens=1024: ""
        pares3 = score_relevance_com_origem("tema", _docs, ["x"])
        record("lote vazio do modelo -> (0.5, fallback_erro)", all(p == (0.5, "fallback_erro") for p in pares3), str(pares3))

        _gc._generate = lambda prompt, temperature=0.0, max_tokens=1024: "[0.9, 0.1]"
        pares4 = score_relevance_com_origem("tema", _docs, ["x"])
        record("lote valido -> origem 'modelo'", pares4 == [(0.9, "modelo"), (0.1, "modelo")], str(pares4))

        _gc._generate = lambda prompt, temperature=0.0, max_tokens=1024: '[0.9, "abc"]'
        pares5 = score_relevance_com_origem("tema", _docs, ["x"])
        record("valor nao numerico -> so aquele item e fallback_erro",
               pares5 == [(0.9, "modelo"), (0.5, "fallback_erro")], str(pares5))

        _gc._generate = lambda prompt, temperature=0.0, max_tokens=1024: "[0.9]"
        pares6 = score_relevance_com_origem("tema", _docs, ["x"])
        record("tamanho errado -> lote inteiro fallback_erro", all(p == (0.5, "fallback_erro") for p in pares6), str(pares6))
    finally:
        _gc.is_available, _gc._generate = _orig_avail, _orig_gen
except Exception as e:
    record("secao 9 (origem da nota)", False, traceback.format_exc())
```

- [ ] **Step 2: Ver falhar** — `python test_llm_phase3.py | tail -5` → `Total: 54 | PASS: 53 | FAIL: 1` (a seção inteira cai no `except` com `ImportError`, um único `record` de falha).

- [ ] **Step 3: Implementar** — em `gemini_client.py`, **renomear** a atual `score_relevance` (`:340`) para `score_relevance_com_origem`, tipo de retorno `list[tuple[float, str]]`, e ajustar cada ponto que emite nota:

```python
    if not is_available():
        if keywords:
            logger.info("LLM indisponivel — heuristica por palavras-chave.")
            return [(_keyword_relevance(keywords, r.get("ementa", "")), "heuristica") for r in results]
        logger.info("LLM indisponivel e sem keywords — 0.5 rotulado como fallback_erro.")
        return [(0.5, "fallback_erro")] * len(results)
```

lote vazio (`:403-405`): `all_scores.extend([(0.5, "fallback_erro")] * len(batch))`; lote válido, dentro do `for val in parsed:`:

```python
                try:
                    score = max(0.0, min(1.0, float(val)))
                    batch_scores.append((score, "modelo"))
                except (TypeError, ValueError):
                    batch_scores.append((0.5, "fallback_erro"))
```

lote de tamanho errado (`:418-424`): `all_scores.extend([(0.5, "fallback_erro")] * len(batch))`.

Docstring da função nova — reescrever a atual acrescentando:

```
    Returns:
        Lista de (nota, origem), mesma ordem dos results. origem e um de
        models.ORIGENS_RELEVANCIA: "modelo" quando o LLM deu a nota;
        "heuristica" quando nao ha LLM e ha keywords; "fallback_erro" quando
        o LLM falhou (lote vazio, tamanho errado, valor nao numerico) ou nao
        ha nem LLM nem keywords. Antes, esses tres casos davam 0.5 sem marca.
```

Wrapper, logo abaixo:

```python
def score_relevance(
    topic: str,
    results: list[dict],
    keywords: Optional[list[str]] = None,
) -> list[float]:
    """Compat: so as notas. Ver score_relevance_com_origem para a procedencia."""
    return [nota for nota, _ in score_relevance_com_origem(topic, results, keywords)]
```

**M9 — docstring de módulo** (`gemini_client.py:11`): a linha `- score_relevance returns keyword-based heuristic scores or [0.5, ...]` vira `- score_relevance_com_origem returns (nota, origem): heuristica sem LLM (ou (0.5, "fallback_erro") sem keywords); score_relevance e o wrapper que descarta a origem`. Em `llm/__init__.py`: importar e exportar `score_relevance_com_origem` (no `from .gemini_client import (...)` e no `__all__`); a docstring do pacote, linha `Provides keyword expansion, relevance scoring, and auto-categorization`, ganha `(scores carry their origin: see score_relevance_com_origem)`. ⚠ **Não** tocar as frases sobre Gemini/API key (emenda B7, frente 5).

- [ ] **Step 4: Ver passar** — `Total: 63 | PASS: 63 | FAIL: 0`. `git grep -n 'score_relevance\b' -- '*.py'`: só o wrapper, `__init__.py`, `app.py:582` (que a T9 troca) e os testes.

- [ ] **Step 5: BASELINE 63; runner; golden OK; commit**

```bash
git add levantamento-normativos/llm/ levantamento-normativos/test_llm_phase3.py tools/run_all_tests.py
git commit -m "feat(frente2): a nota de relevancia passa a dizer de onde veio

score_relevance_com_origem devolve (nota, origem) com origem em
ORIGENS_RELEVANCIA; score_relevance vira wrapper com o mesmo contrato
(53 testes intactos). 0.5 de fallback deixa de ser indistinguivel de
nota do modelo. Docstrings de modulo e de pacote atualizadas.
test_llm_phase3: 53 -> 63."
git push origin master
```
