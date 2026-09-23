---
title: Frente 2 — TODOS (SSOT do status desta execução)
related: [CONTEXTO.md, INSIGHTS.md]
---

# TODOS — frente 2

> **SSOT do status da frente 2.** O `_TODO.md` da raiz aponta para cá. Atualizar a cada passo do ciclo,
> **antes** de qualquer compactação. Legenda por task: impl · teste(+e2e) · review · fix · doc · merge.

## Preparação
- [x] Arquivos de contexto, todos e insights criados
- [ ] Worktrees das trilhas A e B criadas (depois da T1)

## Fase 1 — Fundação (trilha 0, `master`)
- [ ] **T1** vocabulário — impl · teste · review · fix · doc
- [ ] `/checkpoint` fase 1

## Fase 2 — Fontes honestas (trilha A)
- [ ] **T2** LexML — impl · teste · review · fix · doc
- [ ] **T3** TCU falhas — impl · teste · review · fix · doc
- [ ] **T4** TCU esquema real — impl · teste · review · fix · doc
- [ ] **T5** Google — impl · teste · review · fix · doc
- [ ] merge trilha A → `master` · `/checkpoint` fase 2

## Fase 3 — Procedência da nota (trilha B)
- [ ] **T6** origem da nota — impl · teste · review · fix · doc
- [ ] **T7** `_merge` — impl · teste · review · fix · doc
- [ ] merge → `master` · `/checkpoint` fase 3 (junto do merge da trilha B, se T8 fechar antes)

## Fase 4 — Saída honesta
- [ ] **T8** planilha (trilha B; recongela golden) — impl · teste · review · fix · doc
- [ ] merge trilha B → `master` (BASELINE unido conferido)
- [ ] **T9** tela + V11 (`master`) — impl · teste · review · fix · doc
- [ ] `/checkpoint` fase 4

## Revisão final (várias perspectivas)
- [ ] reviewers do estado final despachados
- [ ] achados triados e aplicados por coder

## Fase 5 — Fechamento
- [ ] **T10** fechar a frente — critérios §7, duráveis, LESSONS
- [ ] `/checkpoint` fase 5
