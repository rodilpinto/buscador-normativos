---
task: 7
fase: "Fase 3 — Procedência da nota"
plan: docs/superpowers/plans/2026-09-22-frente2-honestidade-fontes.md (linhas 2338-2385)
reference: spec/frente2-honestidade-fontes/reference/global-constraints.md
depends_on: [T1]
---

> Extraído **verbatim** do plano v4 (linhas 2338-2385). **O plano segue fonte de verdade**:
> divergência entre o plano e esta cópia → o plano ganha. Status em `../execucao/TODOS.md` — **não marque
> os checkboxes aqui**. Antes de começar, ler `../reference/global-constraints.md` (Global
> Constraints, Estrutura de arquivos, BASELINE por task). Ordem e dependências: `../00-overview.md`.

# T7 · `_merge` leva a origem da nota vencedora (invariante declarado)

**Fase 3 — Procedência da nota.**

## Depende de

- **T1** — campo `NormativoResult.relevancia_origem`

**Arquivos compartilhados com outras tasks:** `deduplicator.py` · `test_phase4.py` (T8, T9) · runner

## Critérios de aceite

> Derivados do próprio plano (os "Ver passar", "Expected" e gates da task e das Global
> Constraints) — **nenhum critério novo**. Números são previsões do plano: se o observado
> divergir, contar os `def test_` do bloco da task antes de suspeitar do código.

- `python -m pytest test_phase4.py -q` → **`61 passed`** (Step 4).
- **`dedup_esperado.json` inalterado — obrigatório**; golden OK.
- Docstring de `_merge` declara o invariante (hoje o efeito prático é nulo: o dedup roda antes da pontuação).
- `BASELINE` 61; runner TUDO VERDE (total **272**); auditoria; commit + push.

---

## Conteúdo da task (verbatim do plano)

### Task 7: `_merge` leva a origem da nota vencedora (invariante declarado)

**Files:** `deduplicator.py:98-113` (docstring), `:147` (`relevancia`); `test_phase4.py`; `tools/run_all_tests.py`.

- [ ] **Step 1: Testes** — ao fim de `test_phase4.py`:

```python
class TestMergeOrigem:
    """_merge guarda a maior nota E a origem dela (spec §3.4). Invariante: no app o
    dedup roda ANTES da pontuacao, entao hoje o efeito e nulo — ver docstring."""

    def test_incoming_maior_leva_sua_origem(self):
        a = _make_result(relevancia=0.4); a.relevancia_origem = "padrao_fonte"
        b = _make_result(source="google", relevancia=0.9); b.relevancia_origem = "modelo"
        _merge(a, b)
        assert (a.relevancia, a.relevancia_origem) == (0.9, "modelo")

    def test_existing_maior_mantem_sua_origem(self):
        a = _make_result(relevancia=0.9); a.relevancia_origem = "heuristica"
        b = _make_result(source="google", relevancia=0.2); b.relevancia_origem = "modelo"
        _merge(a, b)
        assert (a.relevancia, a.relevancia_origem) == (0.9, "heuristica")

    def test_empate_mantem_existing(self):
        a = _make_result(relevancia=0.5); a.relevancia_origem = "modelo"
        b = _make_result(source="google", relevancia=0.5); b.relevancia_origem = "fallback_erro"
        _merge(a, b)
        assert a.relevancia_origem == "modelo"
```

- [ ] **Step 2: Ver falhar** — `python -m pytest test_phase4.py -q -k MergeOrigem` → 1 failed.
- [ ] **Step 3: Implementar** — em `_merge`, trocar `existing.relevancia = max(existing.relevancia, incoming.relevancia)` por:

```python
    # Relevancia: keep higher score — e a ORIGEM da nota que venceu.
    # Invariante DECLARADO (M8 da rodada de 22/09): no app o dedup roda ANTES
    # da pontuacao, entao aqui todo item ainda e "padrao_fonte" e o efeito
    # pratico e nulo hoje. Existe para o dia em que a pontuacao vier antes
    # (ex.: nota por fonte), sem que a planilha diga "modelo" sobre uma nota
    # da heuristica.
    if incoming.relevancia > existing.relevancia:
        existing.relevancia = incoming.relevancia
        existing.relevancia_origem = incoming.relevancia_origem
```

Docstring: `- relevancia: keep the higher score` → `- relevancia: keep the higher score, and relevancia_origem of whichever won (tie keeps existing)`.

- [ ] **Step 4: Ver passar** — `61 passed`. **Golden: `dedup_esperado.json` inalterado — obrigatório.** BASELINE 61. Commit `feat(frente2): _merge leva a origem da nota que venceu (invariante)`. Push.
