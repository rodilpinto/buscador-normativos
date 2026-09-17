---
title: Buscador de Base Normativa — TODOs
last_audit: 2026-09-16
related: [_DECISOES-PENDENTES.md, log.md, LESSONS.md, BLOCKED-ON-RODRIGO.md, SESSION-ONBOARD-buscador.md, decisions/DECISIONS-LOG.md]
---

# TODOs — o que está pendente

> **Conteúdo** de cada task: `docs/superpowers/plans/2026-09-16-consolidacao-fase1.md`.
> ⛔ **Leia as três seções de emendas ANTES do corpo** — precedência **C > B > A > corpo**.
> Cada seção do corpo derrubada carrega um marcador `⛔` dizendo qual emenda a derruba.
> **Status**: aqui, e só aqui.

## ⛔ Superado — o plano de 16 tasks NÃO vale mais

O plano de 08/09 (`docs/superpowers/plans/2026-09-08-buscador-normativos.md`) e o split em
`spec/buscador/tasks/` foram **superados** pela consolidação de 16/09. Ficam no repo como
histórico e porque várias das emendas antigas continuam citadas. **Não execute aquelas tasks.**
Motivo em `log.md` (entrada de 16/09) e na spec de consolidação §1.1.

---

## Fase 1 — consolidação (plano de 16/09)

⚠ **A ordem NÃO é a numeração.** A emenda A1 reordenou: **T3 → T1 → T2 → T4 → T5 → T6 → T7 → T8 → T9.**

⚠ **Os arquivos de código citados abaixo (`app.py`, `llm/__init__.py`, `test_llm_phase3.py`,
`excel_export.py`…) ainda NÃO existem neste repo.** Eles vivem em
`~/Documents/projeto-nuati-normativos-levantamento/levantamento-normativos/` e só chegam aqui
depois da **T3** (o merge). Antes disso, abra-os lá.

- [ ] **T3 · Merge do histórico de A** — `git merge --allow-unrelated-histories`. É a **primeira**.
      ⚠ O Step 6 dela **sai** (A1): chama ferramentas que ainda não existem nesse ponto.
- [ ] **T1 · Golden-master** — congela dedup + planilha. ⚠ `generate_excel`, não `export_to_excel`
      (A2); hash de **células**, não de bytes (A3); entrada limpa (A14); **14** itens cobrindo as
      3 estratégias de dedup (A12/B12).
- [ ] **T2 · Runner único** — ⚠ nasce com `SUITES_PYTEST = ["test_phase4.py"]` só (B2); piso com
      3 ramos, não igualdade (A9/B3/C1); o trecho entra no laço de impressão (C3).
- [ ] **T4 · Ambiente reproduzível** — `pyproject.toml` + venv. ⚠ `pandas` é dependência de
      produção não declarada (A13); SDK de LLM vira extra opcional.
- [ ] **T5 · Protocolo de backend de LLM** — ⚠ `timeout=(3.05, 60)`, tupla (A7); o teste precisa
      afirmar o `timeout` (B9).
- [ ] **T6 · Ligar o cliente ao backend** — a task mais emendada. ⚠ **ACRESCENTAR** linha, não
      trocar a 14 do `test_llm_phase3.py` (B1); blocos nomeados (A4/B6); `app.py` e
      `llm/__init__.py` entram nos Files (A15/B7); Step 4b registra a suíte no runner (B2).
- [ ] **T7 · Corrigir os documentos com premissa falsa** — ⚠ o MEMORY.md é auto-memória e exige
      **autorização do Rodrigo** (B8).
- [ ] **T8 · Renomear para `buscador/` + auditoria de docstrings** — ⚠ gate sem `head` (A8); o
      Step 3 espera **215**, não "os mesmos números da T2" (C2).
- [ ] **T9 · Aposentar o repo A** — ⛔ só depois de todos os critérios de pronto, **e confirmando
      com o Rodrigo no momento** (ação externa).
      - [x] **2026-09-16 · tag `levantamento-v1-streamlit` empurrada para o remoto** (confirmado
        por `git ls-remote --tags origin`). O ponto de restauração deixou de ser local.
      - [ ] README de arquivamento no repo A · [ ] `gh repo archive`

## Fase 2 — as features (plano ainda não escrito)

- [ ] **F1** procedência (`catalogada` / `web-aberta`)
- [ ] **F2** vinculação (`obrigatorio` / `aplicavel` / `contexto`)
- [ ] **F3** pré-marcação com motivo + as **duas** travas anti-ancoragem
- [ ] **F4** selo "já tenho" por sha256
- [ ] **F5** download + organização por tema + relatório de duplicata
- [ ] **F6** SQLite + colunas de registro na planilha
- [ ] **F7** agrupamento semântico dos resultados — ⚠ **aditivo**, nunca subtrativo (D-C1)

## P3 — depois da Fase 1

- [ ] **Medir a lacuna de cobertura** das fontes catalogadas → **`BLOCKED-ON-RODRIGO.md` B-04**.
      É bloqueio no humano (exige tema real e julgamento de quem conhece o acervo), não task.
      ⚠ Obrigatório antes de fechar o MVP. O pacote completo está lá; aqui só o ponteiro.
- [ ] Rodar contra um tema real e medir o critério de sucesso nº 2 da spec: 100+ resultados
      triáveis em menos de 15 decisões.
- [ ] Reavaliar se Planalto e LEGIN fazem falta (D-B2 adiou; a lacuna não foi medida).
- [ ] Escrever o plano da Fase 2.
- [ ] Registrar este repo no `MEMORY.md` do `projetos-nuati` como solução nova.
      ⛔ **Bloqueado em autorização** — é auto-memória; a regra `memory-write-policy` exige que o
      Rodrigo autorize antes.

## Fora de escopo (registrado para não voltar à pauta)

Decidido no board de 16/09 (`decisions/DECISIONS-LOG.md`):

- **Chat sobre o acervo** — é o `wiki-chat`, projeto distinto.
- **Busca semântica sobre o acervo baixado** — mesmo terreno do `wiki-chat`.
- **Selo já-tenho por embedding** — ⚠ lacuna conhecida e **não mitigada**: material sem numeração
  (manuais, frameworks, guias ANPD) continua escapando do selo.
- **Extração de dispositivos e geração de checklist** — o handoff vai para roadmap, fora do MVP.
- **Reescrita em FastAPI** — a decisão B2 foi revertida.
