---
title: Frente 2 — Honestidade das fontes — mapa de execução (split)
plan: docs/superpowers/plans/2026-09-22-frente2-honestidade-fontes.md (v4)
spec: docs/superpowers/specs/2026-09-22-frente2-honestidade-fontes-design.md
reference: spec/frente2-honestidade-fontes/reference/global-constraints.md
last_updated: 2026-09-23
---

# Mapa de execução: 10 tasks, 5 fases

> O **plano** segue fonte de verdade do *conteúdo* de cada task. Este arquivo é fonte de verdade
> do *ordenamento*. O **status** por task vive em `execucao/TODOS.md` (SSOT da execução, 22/09).
> Os arquivos em `tasks/` são cópia **verbatim** do plano (cada um com um header de dependências e
> critérios de aceite derivados do próprio plano), para o agente de build carregar ~100–800 linhas
> em vez de 2.882. Split pedido pelo Rodrigo em 2026-09-22 (decisão D-C16).

**Objetivo da frente** (do plano): fazer o app dizer a verdade quando uma fonte não pôde ser
consultada e de onde veio cada nota de relevância — na tela e na planilha — sem mudar como ele
deduplica.

## Fases e tasks

| Fase | # | Arquivo | Entrega | test total após |
|---|---|---|---|---|
| **1 · Fundação** | 1 | `tasks/01-vocabulario-honestidade.md` | `MOTIVOS`, `ORIGENS_RELEVANCIA`, `redigir()`, `rotulo_status()`, `statuses_para_falha_total()`, `FonteIndisponivel`, `SOURCE_ID`; runner sem LLM | 222 |
| **2 · Fontes honestas** | 2 | `tasks/02-lexml-falhas-declaradas.md` | LexML: bloqueio/timeout/5xx declarados, cache de causa, parcial, `nao_consultada`; **cria a suíte nova** | 238 |
| | 3 | `tasks/03-tcu-falhas-declaradas.md` | TCU: 5xx/4xx/503/HTML declarados, paginação parcial, por endpoint | 247 |
| | 4 | `tasks/04-tcu-esquema-real.md` | TCU lê o esquema real do acórdão (emenda spec §3.7) | 251 |
| | 5 | `tasks/05-google-vocabulario.md` | Google/DDG no vocabulário mínimo (emenda spec §5) | 259 |
| **3 · Procedência da nota** | 6 | `tasks/06-origem-da-nota.md` | `score_relevance_com_origem` → `(nota, origem)` | 269 |
| | 7 | `tasks/07-merge-origem.md` | `_merge` leva a origem vencedora (invariante) | 272 |
| **4 · Saída honesta** | 8 | `tasks/08-planilha-diagnostico.md` | coluna "Origem da nota" + aba "Diagnostico da busca"; **recongela o golden** | 282 |
| | 9 | `tasks/09-tela-honesta.md` | tela: relatório por motivo, avisos por fonte, origem no card; gate visual V11 | 283 |
| **5 · Fechamento** | 10 | `tasks/10-fechar-frente.md` | critérios de pronto da spec §7, duráveis, lições | 283 |

A coluna de total é a tabela de BASELINE do plano (`reference/global-constraints.md`). **O observado manda.**

✅ **Frente fechada em 23/09 (T10).** Total observado ao fechar: **336** (13 + 65 + 98 + 94 + 66), contra os 283 do plano —
a diferença são os testes além do plano (reviews de cada task e as trilhas de conserto da revisão final, FIX-FONTES e
FIX-SAÍDA, que não estão nesta tabela). Status por task: `execucao/TODOS.md`; fechamento: `implementacao/10-fechar-frente.md`.

## Grafo de dependências (por símbolo consumido — ver o "Depende de" de cada task)

```
T1 vocabulário ─┬─► T2 LexML ─► T3 TCU ─► T4 TCU esquema ─► T5 Google ──┐
  (MOTIVOS,     │   (cria a suíte nova; T3/T4/T5 somam nela)             │
   redigir,     │                                                        │
   FonteIndisp.)├─► T6 origem da nota ──────────────────────────────────┤
                │                                                        ▼
                └─► T7 _merge ─► T8 planilha (recongela golden) ─────► T9 tela ─► T10 fechar
```

- **T9 consome quase tudo:** `SOURCE_ID` de T2/T3/T5, `score_relevance_com_origem` (T6),
  `generate_excel(diagnostico=, quando=)` (T8); o gate V11 procura `bloqueio_waf` (T2) e
  "tcu respondeu parcialmente" (T3+T4).
- **T5 não consome código da T3/T4**, mas acrescenta testes à mesma suíte e ao mesmo `BASELINE`;
  vem depois delas para as contagens previstas valerem.
- **T8 depende da T7 só na contagem** (`test_phase4`: 61 → 71).

## Ordem de execução: o plano manda T1 → T10; a execução usa trilhas (seção abaixo)

✅ **Documentado no plano:** "ordem de execução = numeração". As 3 rodadas adversariais aplicaram as
tasks **nessa ordem** num worktree e rodaram os testes; as contagens "Expected" de cada task
pressupõem essa ordem.

Protocolo por task do plano (Global Constraints; state file §5). ⚠ Na execução de 22/09 em diante vale o
ciclo de agentes de `execucao/CONTEXTO.md` (coder → testador + e2e → reviewer → coder aplica e documenta):

1. Despachar **um subagente** com o arquivo da task + `reference/global-constraints.md`
   (`superpowers:subagent-driven-development`: implementador → revisão de conformidade com a spec →
   revisão de qualidade de código).
2. TDD como escrito: teste que falha → ver falhar → implementar → ver passar.
3. Gate: `python tools/run_all_tests.py` TUDO VERDE (+ `BASELINE` atualizado no mesmo commit) **e**
   `python tools/golden_master.py comparar` OK (exceto T8, que recongela no mesmo commit) **e** os 2
   comandos de auditoria de documentação lidos inteiros.
4. Commit + **push** em `master` (D-C7) — na execução por trilhas: push da **branch da trilha**; `master` só no merge. A nuvem segue a branch `deploy`, congelada em `v1.0.1` —
   ⛔ **não avançar `deploy`** durante a frente; só no marco, com ok do Rodrigo.
5. Marcar a task em `execucao/TODOS.md`, e só então a próxima.

### Duas trilhas paralelas depois da T1 — ✅ adotada pelo Rodrigo em 22/09 (era 📝 proposta minha)

Verificado lendo o bloco "Files" de cada task: depois da T1, as trilhas
**A = T2 → T3 → T4 → T5** (searchers, `test_comprehensive.py`, suíte nova, `requirements.txt`, `models.py` —
só a docstring de `situacao`, na T4 —, spec) e
**B = T6 → T7 → T8** (`llm/`, `test_llm_phase3.py`, `deduplicator.py`, `excel_export.py`,
`test_phase4.py`, golden) **só colidem em `tools/run_all_tests.py`**: chaves diferentes do mesmo dict
`BASELINE`, que dá conflito de merge trivial. A T9 junta as duas.

- **Ganha:** cada task custa ~9 min de runner; duas trilhas em worktrees cortam o tempo de parede.
- **Perde:** os totais previstos por task (222, 238…) deixam de valer, porque somam as duas trilhas;
  o golden recongelado na T8 (trilha B) roda enquanto a trilha A mexe nos searchers (o golden não os
  exercita, mas o `comparar` da trilha A passa a depender do merge da B); e nenhuma rodada
  adversarial validou essa ordem.
- **Recomendação original:** sequencial. ✅ **Decisão do Rodrigo (22/09):** executar por trilhas — ver
  `execucao/CONTEXTO.md` (portas, worktrees, como os totais do runner passam a ser lidos).

## Referências

| Arquivo | Conteúdo |
|---|---|
| `reference/global-constraints.md` | cabeçalho do plano (goal, arquitetura, stack, spec) + Global Constraints + Estrutura de arquivos + BASELINE por task — **ler antes de cada task** |
| `reference/triagem-adversarial.md` | as 3 rodadas adversariais (trilha de auditoria; **não** é instrução de build) |
| `reference/self-review-v4.md` | o self-review do plano v4 (cobertura da spec, contagens, nomes) |

**Verificação da extração** (script `tools/split_frente2.py`, que gera `tasks/` e `reference/` — o
header de cada task vive nele; este overview é escrito à mão): toda linha não vazia e diferente de
`---` do plano (1–2882) cai em **exatamente um** arquivo, sem sobreposição; cercas de código pares.
✅ **Conferência independente (22/09, agente que não extraiu, script próprio):** verbatim byte a byte nas
10 faixas + reference; só as 13 linhas `---` ficam de fora; sem mojibake; dependências e critérios
rastreados ao plano; interseção das duas trilhas = só `tools/run_all_tests.py`. Os 3 defeitos menores
que ele achou (2 motivos de dependência da T9, `models.py` na trilha A) foram corrigidos. Registro:
`log.md`, entrada de 2026-09-22 (split).
