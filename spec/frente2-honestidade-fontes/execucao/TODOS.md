---
title: Frente 2 — TODOS (SSOT do status desta execução)
related: [CONTEXTO.md, INSIGHTS.md]
---

# TODOS — frente 2

> **SSOT do status da frente 2.** O `_TODO.md` da raiz aponta para cá. Atualizar a cada passo do ciclo,
> **antes** de qualquer compactação. Legenda por task: impl · teste(+e2e) · review · fix · doc — cada passo `▶` em andamento, `✅` feito (com SHA),
> `n/a`. Merge é por trilha inteira (CONTEXTO, "Merge").

## Preparação
- [x] Arquivos de contexto, todos e insights criados
- [x] Worktrees das trilhas A e B criadas (`../bn-trilha-a`, `../bn-trilha-b`, 23/09)

## Fase 1 — Fundação (trilha 0, `master`)
- [x] **T1** vocabulário — impl ✅ `da543be` (58 · runner 222 verde · golden OK) · teste ✅ APROVADO (47 sondas + e2e Playwright até Passo 5 + Excel baixado) · review ✅ nada a corrigir (4 menores → 📝 hardening, INSIGHTS) · fix — n/a · doc ✅ `ed50b6b`
- [x] `/checkpoint` fase 1 (23/09, `a6de0af` + consertos do dogfood)

## Fase 2 — Fontes honestas (trilha A)
- [x] **T2** LexML — impl ✅ `8f5ccfc` (16 · runner 238 verde · golden OK) · teste ✅ APROVADO (sondas + ao vivo + e2e: "2 erros" LexML; `revisoes/T2.md`) · review ✅ 1 importante + 1 menor a corrigir (2 adiados → `_TODO` P3) · fix ✅ `407e341` (+1 teste → 17; runner 239) · doc ✅ `3be5d85` · push ✅ · review · fix · doc
- [ ] **T3** TCU falhas — impl ▶ · teste · review · fix · doc
- [ ] **T4** TCU esquema real — impl · teste · review · fix · doc
- [ ] **T5** Google — impl · teste · review · fix · doc
- [ ] merge trilha A → `master` · `/checkpoint` fase 2

## Fase 3 — Procedência da nota (trilha B)
- [x] **T6** origem da nota — impl ✅ `7d8f1ce` (54/53/1 → 63/63 · runner 232 verde · golden OK) · teste ✅ APROVADO (`revisoes/T6.md`) · review ✅ corrigir bool/NaN/Inf (+1 teste → 64); `ementa None` → frente 5 · fix ✅ `6594cd8` (64; runner 233) · doc ✅ `272f83a` · push ✅ · review · fix · doc
- [ ] **T7** `_merge` — impl ▶ · teste · review · fix · doc
- [ ] (fase 3 fecha no merge da trilha B, depois da T8 — ver Fase 4)

## Fase 4 — Saída honesta
- [ ] **T8** planilha (trilha B; recongela golden) — impl · teste · review · fix · doc
- [ ] merge trilha B → `master` (BASELINE unido conferido) · `/checkpoint` fase 3
- [ ] **T9** tela + V11 (`master`) — impl · teste · review · fix · doc
- [ ] `/checkpoint` fase 4

## Revisão final (várias perspectivas)
- [ ] reviewers do estado final despachados
- [ ] achados triados e aplicados por coder

## Fase 5 — Fechamento
- [ ] **T10** fechar a frente — critérios §7, duráveis, LESSONS
- [ ] `/checkpoint` fase 5
