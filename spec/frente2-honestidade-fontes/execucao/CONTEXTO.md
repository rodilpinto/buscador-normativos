---
title: Frente 2 — contexto da execução (ler PRIMEIRO depois de qualquer compactação)
started: 2026-09-22
related: [TODOS.md, INSIGHTS.md, ../00-overview.md, ../reference/global-constraints.md]
---

# Contexto da execução da frente 2

> **Depois de qualquer compactação de memória: ler este arquivo e `TODOS.md` antes de continuar.**

## Objetivo (pedido do Rodrigo, 2026-09-22, literal)

> *"Implement this implementation plan in its entirety. Do not skip a thing. Use the checkpoint skill to
> create commits after each phase is completed. Use the Playwright skill to test each feature end-to-end."*

O plano = `docs/superpowers/plans/2026-09-22-frente2-honestidade-fontes.md` (v4, **fonte de verdade**),
dividido em `spec/frente2-honestidade-fontes/tasks/01..10` (D-C16). ⚠ O pedido citava `spec/implementation`,
que não existe: a pasta é `spec/frente2-honestidade-fontes/`.

## Regras de papel (pedido do Rodrigo, vinculantes)

- **O orquestrador (sessão principal) NÃO escreve código.** Coordena agentes: cria worktrees/branches,
  despacha, repassa feedback, faz merge (conflito → agente coder resolve), atualiza os arquivos de `execucao/` (CONTEXTO, TODOS, INSIGHTS, BRIEFS, `revisoes/`).
- **Trilhas** = tasks sem dependência entre si, em paralelo.
- **Ciclo por task, dentro da trilha:**
  1. **Coder A** (implementador) implementa a task como o arquivo manda (TDD do plano, commit da task).
  2. **Coder B** (testador) testa: suítes da task, runner, golden, e **e2e com Playwright** (app no ar, porta da trilha).
     Reprovou → volta ao Coder A → re-testa.
  3. **Code reviewer** confere contra a spec/plano; o feedback vai **para o Coder A da trilha** (SendMessage).
  4. Coder A aplica o feedback (re-teste se mudou código) e **documenta** em
     `spec/frente2-honestidade-fontes/implementacao/NN-*.md` (o que foi feito, desvios, comandos + saídas).
- **Ao fim de cada fase:** `/checkpoint` (commit + push).
- **No fim de tudo:** vários code reviewers do estado final, de perspectivas diferentes; achados → coder → T10.

## Trilhas (dependências: `../00-overview.md` e o header de cada task)

| Trilha | Tasks | Onde | Porta do app (e2e) |
|---|---|---|---|
| **0 · gate** | T1 | `master` (repo principal) | 8501 |
| **A · fontes** | T2 → T3 → T4 → T5 | worktree `../bn-trilha-a`, branch `frente2/trilha-a` | 8511 |
| **B · nota + planilha** | T6 → T7 → T8 | worktree `../bn-trilha-b`, branch `frente2/trilha-b` | 8521 |
| **C · junção** | merge A+B em `master` → T9 → revisão final → T10 | `master` | 8501 |

- A e B só colidem em `tools/run_all_tests.py` (dict `BASELINE`, chaves diferentes) — verificado por agente
  independente em 22/09. O merge resolve; os totais previstos por task do plano **somam as duas trilhas** e
  deixam de valer isoladamente: em cada trilha vale o número **da suíte** que a task mexe.
- Fases × trilhas: Fase 1 = T1 · Fase 2 = trilha A · Fase 3 = T6+T7 · Fase 4 = T8 + T9 · Fase 5 = T10.
- **Merge: cada trilha entra em `master` INTEIRA, uma vez, quando a última task dela fecha o ciclo** (sem merge
  parcial, sem rebase no meio): trilha A depois da T5 → `/checkpoint` **fase 2**; trilha B depois da T8 →
  `/checkpoint` **fase 3** (a T8 entra junto, mas a fase 4 só fecha com a T9). Uma fase conta como fechada quando
  **todas** as suas tasks passaram o ciclo **e estão em `master`**. A 2ª trilha a entrar faz `git merge master`
  na própria branch antes (conflito → coder), roda runner + golden, e só então entra (fast-forward).
- Push das branches de trilha a cada task fechada no ciclo (`git push -u origin frente2/trilha-X`) — backup,
  não deploy.

## Gates que nunca mudam (plano, Global Constraints)

Runner `python tools/run_all_tests.py` TUDO VERDE (≈9 min) · `python tools/golden_master.py comparar` OK (T8
recongela) · `dedup_esperado.json` nunca muda · auditoria de docs (os 2 comandos) · sem LLM de verdade ·
nada de `levantamento-normativos/.streamlit/secrets.toml` · ⛔ **não avançar a branch `deploy`**.
Push: branches de trilha em `origin/frente2/trilha-*`; `master` a cada merge/fase.

## Estado

Status por task: **`TODOS.md` (SSOT desta execução)**. Aprendizados: `INSIGHTS.md`.
