# T1 · Vocabulário de honestidade — registro de implementação

> Task: `../tasks/01-vocabulario-honestidade.md` (plano v4, linhas 246-579 — o plano é a fonte de verdade).
> Commit de código: **`da543be`** `feat(frente2): vocabulario de honestidade, redigir() e FonteIndisponivel`
> (master, 22/09/2026). Teste independente: **APROVADO**. Revisão de código: **APROVADO, "nada a corrigir"**.

## 1. O que foi feito

| Arquivo | Símbolos |
|---|---|
| `levantamento-normativos/models.py` | `import re`; `MOTIVOS` (12 valores) e `ORIGENS_RELEVANCIA` (4) com o comentário de cada valor; `_RE_SEGREDO`, `_RE_BEARER`, `_RE_CONTROLE`; `redigir(texto, limite=2000)`; `rotulo_status(s)`; `NormativoResult.relevancia_origem = "padrao_fonte"` + validação no `__post_init__` (antes do hash) + docstring; `KeywordStatus.motivo/detalhe/parcial`, `__post_init__` (valida `motivo`), `__setattr__` (redige `detalhe`/`error_message` em toda atribuição), docstring; `statuses_para_falha_total()` no fim do arquivo |
| `levantamento-normativos/searchers/base.py` | `BaseSearcher.SOURCE_ID: str = ""` (após `RATE_LIMIT_JITTER`); `FonteIndisponivel(motivo, detalhe="")` no fim do arquivo |
| `levantamento-normativos/test_phase4.py` | 17 testes novos: `TestVocabularioHonestidade` (10), `TestRedigir` (4), `TestRotuloStatus` (1), `TestStatusesParaFalhaTotal` (2) |
| `tools/run_all_tests.py` | `import os`; `_rodar` passa `env={**os.environ, "GEMINI_API_KEY": "", "GOOGLE_API_KEY": ""}`; `BASELINE["test_phase4.py"]` 41 → 58 |
| `docs/superpowers/specs/2026-09-22-frente2-honestidade-fontes-design.md` | §3.1: lista de `motivo` trocada pela de `MOTIVOS`; nota `⚠ Emendado em 22/09 (plano v3, T1)` acrescentada literal |

O código dos blocos do plano foi colado como está. O plano listava o próprio plano no `git add`; como ele não mudou, não entrou no commit.

## 2. Desvios do plano e por quê (os 4 aceitos pelo revisor)

1. **Onde ficaram os testes.** O plano diz "ao fim de `test_phase4.py`". O bloco entrou **antes** do banner final `# Run via pytest or direct execution` / `if __name__ == "__main__"`, para não ficar depois do bloco de execução direta. Conteúdo idêntico.
2. **Comentário extra no runner sobre `secrets.toml`.** Além do comentário do Step 6, acrescentei um sobre `st.secrets` **vencer** a variável vazia (se existir `levantamento-normativos/.streamlit/secrets.toml`). As Global Constraints pedem isso "no comentário do runner e no `LESSONS`". O `LESSONS.md` **não** foi tocado: o plano o atualiza na etapa de fechamento (linha 2872).
3. **Docstring de `KeywordStatus`.** O plano manda usar o "texto da spec §3.1". Para `parcial`, usei o texto emendado R3 (ok/empty e, no TCU, error), não o antigo "status == ok". Também anotei em `error_message` e `detalhe` que ambos passam por `redigir()`.
4. **Spec §3.1.** A linha de `motivo` do bloco de código virou duas linhas, com os 12 valores. A nota da emenda foi inserida literal, depois do parágrafo sobre `MOTIVOS`. Nada removido da spec.

Nota técnica: os arquivos são CRLF no working tree e LF no índice (`core.autocrlf=true`). Todas as edições mantêm CRLF consistente.

## 3. Gates e saídas

**Contagens: o observado bateu exatamente com o plano** (58 em `test_phase4`, total 222 = BASELINE T1). Não houve reconciliação a fazer.

### Implementador (22/09)

- Step 2, falha esperada (em `levantamento-normativos/`, `python -m pytest test_phase4.py -q`):
  ```
  test_phase4.py:579: in <module>
      from models import (KeywordStatus, MOTIVOS, ORIGENS_RELEVANCIA, redigir,
  E   ImportError: cannot import name 'MOTIVOS' from 'models'
  1 error in 0.68s
  ```
- Step 5: `58 passed in 1.67s` (41 + 17).
- Runner (`python tools/run_all_tests.py`, raiz), exit 0, ≈ 9m21s:
  ```
  test_searchers.py     |     13 |      0 |       13 |  411.3s
  test_llm_phase3.py    |     53 |      0 |       53 |    3.9s
  test_comprehensive.py |     98 |      0 |       98 |  143.8s
  test_phase4.py        |     58 |      0 |       58 |    2.5s
  TUDO VERDE
  ```
- `python tools/golden_master.py comparar` → `golden-master OK` (exit 0).

### Auditoria de documentação (os 2 comandos das Global Constraints, lidos inteiros)

`git diff -U0 HEAD~1 -- '*.py' | grep '^-' | grep -v '^---'` → 5 linhas removidas, todas justificadas:

| Linha removida | Destino |
|---|---|
| `status: One of "ok", "empty", "error".` (docstring) | estendida: explica que `error` = fonte indisponível e aponta `rotulo_status()` |
| `retried: Whether this keyword was retried after an initial error.` | trocada pelo texto R3 do plano ("REENVIADA à fonte depois do passe principal… tentativas HTTP internas NÃO contam… retry pulado NÃO marca"); o sentido antigo continua lá, mais preciso |
| `status: str = "ok"  # "ok" \| "empty" \| "error"` | vira `… \| "error" (= fonte indisponivel; ver motivo)`, como o plano manda |
| `"test_phase4.py": 41,` | 58 |
| `cmd, cwd=APP, capture_output=True, …` | a mesma chamada, quebrada em linhas para caber o `env=` |

`git grep -n -E 'score_relevance|…|rotulo_status' -- '*.py'` → a T1 não muda assinatura de nenhum símbolo da lista. Os únicos hits novos são `rotulo_status` (definição em `models.py` e os testes novos). Os demais call sites ficam como estão; são das tasks seguintes.

### Tester independente

- `58 passed`; runner TUDO VERDE 222 (≈ 570 s, `test_searchers` 412 s); golden OK.
- O `env` do runner esvazia as chaves de fato: o processo filho viu `''` e `''`.
- 47 testes extras de sondagem, todos passaram: posições da redação, Bearer, chars de controle, corte em 2000/2001, `replace`/`copy`/`pickle`/`==` do dataclass, ausência de ciclo de import.

### Evidência e2e (tester)

- Playwright (porta 8501, `channel="chrome"`): busca "LGPD" + "protecao de dados pessoais" chegou em **"Passo 4 - Revisar Resultados (16 normativos)"** sem traceback. O Excel baixou e abriu (aba Normativos 18×10).
- Screenshot `tests/evidencia/t1_passo4.png` (não versionado): o relatório da v1.0 ainda diz **"2 OK, 0 erros, 4 sem resultados"**. É a mentira de antes da frente 2, **esperada** nesta task (a T1 só cria o vocabulário; a tela muda nas tasks seguintes).

## 4. Achados de teste e revisão, e para onde foram

Decisão do revisor: **todos ficam na T1 como estão.** O código é o do plano, literal. Mudar a saída de `redigir()` emendaria o plano e poderia mexer no hash do golden da T8.

| # | Achado (tester) | Destino |
|---|---|---|
| 1 | `models.py:72` (o tester citou `:358`): a marca de corte conta `len(texto) - limite`, não os chars de fato removidos. `redigir("A"*1000 + "B"*1001)` diz "cortado 1" mas remove ≈ 25. | 📝 **Proposta, não validada:** `removidos = len(texto) - 2*metade`, numa task posterior com teste próprio. |
| 2 | `models.py:73-74`: com `limite` menor que a marca (≈ 22 chars), `metade` fica negativa e a saída **cresce** (`redigir("q"*100, limite=10)` → 210 chars). Hoje nenhum chamador passa `limite` pequeno. | 📝 **Proposta, não validada:** guarda `if limite < len(marca): return texto[:limite]`. |
| 3 | `motivo` não é validado em atribuição pós-construção. | Aceito: o plano exige validação só no construtor; `FonteIndisponivel` já normaliza o motivo. Sem ação. |
| 4 | `key%3D…` (URL-encoded) e JSON `"key": "x"` não são redigidos. | Fora do escopo da frente 2. 📝 **Proposta, não validada:** endurecer na frente 5. |

Efeito colateral registrado (não é achado): `KeywordStatus.__setattr__` converte `error_message=None` / `detalhe=None` em `""` (`redigir(valor or "")`). Nenhum teste existente dependia de `None`.

## 5. Regras respeitadas

Sem `secrets.toml` criado (só existe o `.example`). Nenhum teste novo faz rede ou chama LLM. Branch `deploy` intocada. `execucao/*` e `_TODO.md` intocados. Push fica com o orquestrador.
