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
- [x] **T3** TCU falhas — impl ✅ `f044a3c` (26+1 xfail · runner 248 · golden OK) · teste ✅ APROVADO (40 sondas; e2e "4 erros", TCU não é mais "sem resultado"; 4 achados no código do plano → `revisoes/T3.md`) · review ✅ 2 importantes + 1 menor a corrigir (+3 testes → 29) · fix ✅ `e8d59a4` (runner 251) · doc ✅ `dfa6f6f` · push ✅ · review · fix · doc
- [x] **T4** TCU esquema real — impl ✅ `e960497` (33 · runner 255 · golden OK; ao vivo "turismo" 0 → 1 acórdão literal) · teste ❌ REPROVADO (1ª×2ª Câmara colidem no id: 212 colisões em 3.200 ao vivo; `revisoes/T4.md`) · fix ✅ `bdd89a1` (`numero` com colegiado, forma de citação do TCU; 35; runner 257; 3.200 keys = 3.200 ids) · re-teste ✅ APROVADO (fuzzy funde acórdãos distintos → 🔴 D-C17, decisão do Rodrigo) · review ✅ (4 menores aplicados) · fix ✅ `38a110d` (36; runner 258) · doc ✅ `3751b2a` · push ✅ · review · fix · doc
- [x] **T5** Google — impl ✅ `5dad3c7` (45 · runner 267 · golden OK; chave do CSE fora dos logs) · teste ✅ APROVADO (26 sondas; nota da spec §5 devida — omissão do plano; `revisoes/T5.md`) · review ✅ 1 importante (teste do log não falhava — mutante) + spec §5 + detalhe do bloqueio · fix ✅ `e70d9f6` (mutante prova o teste do log) · doc ✅ `a0fc6c6` · review · fix · doc
- [x] merge trilha A → `master` ✅ `08d9d8c` (conflito só no `BASELINE`, dois lados mantidos; runner 291 + golden OK no merge; ff) · [x] `/checkpoint` fase 2 (23/09)

## Fase 3 — Procedência da nota (trilha B)
- [x] **T6** origem da nota — impl ✅ `7d8f1ce` (54/53/1 → 63/63 · runner 232 verde · golden OK) · teste ✅ APROVADO (`revisoes/T6.md`) · review ✅ corrigir bool/NaN/Inf (+1 teste → 64); `ementa None` → frente 5 · fix ✅ `6594cd8` (64; runner 233) · doc ✅ `272f83a` · push ✅ · review · fix · doc
- [x] **T7** `_merge` — impl ✅ `7d5e69b` (61 · runner 236 · golden OK, `tests/golden/` intocado) · teste ✅ APROVADO (12.288 combinações; `revisoes/T7.md`) · review ✅ nada a corrigir · fix n/a · doc ✅ `c68bd79` · review · fix · doc
- [ ] (fase 3 fecha no merge da trilha B, depois da T8 — ver Fase 4)

## Fase 4 — Saída honesta
- [x] **T8** planilha (trilha B; recongela golden) — impl ✅ `6178f9d` (71 · runner 246 · golden recongelado: só planilha divergiu, dedup intacto) · teste ✅ APROVADO (recongelamento re-derivado: sem a coluna nova reproduz o sha pré-T8; `revisoes/T8.md`) · review ✅ 3 menores de comentário · fix ✅ `04b2947` · doc ✅ `6eaf590` · review · fix · doc
- [x] merge trilha B → `master` ✅ `9e259ca` (merge de master na trilha sem conflito; runner 246 + golden OK no merge; ff de master) · [x] `/checkpoint` fase 3 (23/09)
- [x] **T9** tela + V11 (worktree `../bn-t9`, branch `frente2/t9`, porta 8501; esperado `test_phase4` 72, runner **292**) — impl ✅ `49d19e1` (V11 OK 7/7; escape duplo consertado +2 testes → 74; runner 294) · teste ✅ APROVADO (7 cenários AppTest; F1 médio: texto da fonte formatado como Markdown/LaTeX no card; `revisoes/T9.md`) · review ✅ F1 (com `_md_html`) + F2 + 3 menores · fix ✅ `0370a21` (76; V11 7/7 de novo; card hostil literal) · doc ✅ `0566533` · merge ✅ `d4cab80` (ff de master; runner 296 + golden OK) · review · fix · doc
- [x] `/checkpoint` fase 4 (23/09)

## Revisão final (várias perspectivas)
- [ ] reviewers do estado final despachados ▶ — 5, só leitura, sobre `master` `d4cab80`; cada veredito em
      `revisoes/final-<slug>.md` quando chega (arquivo existe = terminou). Perspectivas e slugs:
      `spec` (code-reviewer: conformidade ponta a ponta com a spec §3/§4 V1–V11/§7) ·
      `seguranca` (security-auditor: redação de segredos, injeção em planilha/Markdown/HTML, SSRF) ·
      `testes` (qa-test-engineer: gates + **teste de mutação** da lógica de honestidade numa cópia) ·
      `manutencao` (code-reviewer: arquitetura, deriva entre searchers, preservação de docs em `1c063ea..d4cab80`) ·
      `ux` (ui-expert: app real com Playwright na porta 8531, prints em `tests/evidencia/final-ui/` no repo principal).
      Sessão nova com algum faltando: despachar só o que não tem arquivo, com a perspectiva acima e o brief 3 de `BRIEFS.md`
      sobre o diff `1c063ea..d4cab80`.
- [ ] achados triados e aplicados por coder

## Fase 5 — Fechamento
- [ ] (se o Rodrigo escolher `a'` ou `c` na 🔴 D-C17) task extra do dedup fuzzy — **antes** da T10
- [ ] **T10** fechar a frente — critérios §7, duráveis, LESSONS · e limpar os worktrees: `git worktree list`; para cada
      `../bn-*`: (1) inventariar `ls <wt>/tests/evidencia/` (⚠ em `bn-t9` ela é **ignorada**, não untracked — `git status`
      não mostra; os PNG/`.xlsx` são citados pelos `implementacao/*.md`); (2) **preservar** copiando para o repo principal:
      `mkdir -p tests/evidencia/<wt> && cp -r <wt>/tests/evidencia/. tests/evidencia/<wt>/` (ignorado lá também — fica local);
      (3) `git -C <wt> status --short` sem nada além disso; (4) `git worktree remove --force <wt>`; (5) `git branch -d
      frente2/<b>` (já em `master`); (6) remotos: só `frente2/trilha-a` e `frente2/trilha-b` existem em `origin`
      (`git ls-remote origin 'refs/heads/frente2/*'`) — `git push origin --delete` só com ok do Rodrigo. A T10 também lista
      a evidência do próprio repo principal (`tests/evidencia/`, inclui `final-ui/`).
- [ ] `/checkpoint` fase 5
