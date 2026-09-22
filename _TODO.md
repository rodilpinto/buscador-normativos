---
title: Buscador de Base Normativa — TODOs
last_audit: 2026-09-22
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

- [x] **T3 · Merge do histórico de A** — ✅ **feita em 2026-09-22** (`4f36080`). Conflito só no
      `.gitignore`, como previsto. Step 6 não executado (A1). ✅ Verificado: `git log --follow`
      no `app.py` alcança os 2 commits de A, autoria de março preservada, merge com 2 pais,
      15 arquivos `.py` / **6.561 linhas**.
      ⚠ **Correção ao plano:** o heredoc do Step 3 não era a união — faltava `/*.xlsx`. Ver a
      nota na Task 3 do plano e a entrada de 22/09 no `LESSONS.md`.
- [x] **T1 · Golden-master** — ✅ **feita em 2026-09-22.** `tools/golden_master.py` +
      `tests/golden/{entrada_fixa,dedup_esperado}.json`, `planilha_sha256.txt`, `ambiente.txt`.
      Emendas aplicadas: A2 (`generate_excel`), A3 (hash de células), A14 (entrada limpa nas
      duas chamadas), A21 (nome do arquivo · 1º item divergente na mensagem · prova dos 2 ramos),
      A12/B12 (14 itens), B11 (ambiente gravado, mecanizado em `ambiente.txt`).
      ✅ **Provas:** as 3 estratégias disparam uma cada (`id_match` · `tipo_numero` · `fuzzy 0.99`),
      14 → **11** únicos (colapso < 14, check da A12); sha estável em **3** execuções; comparador
      reprova nos **dois** ramos e volta a passar ao desfazer.
- [x] **T2 · Runner único** — ✅ **feita em 2026-09-22.** `tools/run_all_tests.py`. Emendas:
      A5 (exit code das suítes-script não é descartado), B2 (nasce só com `test_phase4.py`),
      A9/B3/C1 (BASELINE como piso com 3 ramos: sem entrada = erro · encolheu = erro · cresceu =
      aviso), C3 (no laço de impressão, onde `nome` existe), A19/B4 (prova bidirecional).
      ✅ **Linha de base após o merge: 205 (13 + 53 + 98 + 41), TUDO VERDE, exit 0.**
      ✅ **Prova bidirecional:** verde → `assert False` injetado → `41 | 1`, HOUVE FALHA, exit 1 →
      desfeito via `git checkout` → verde, exit 0.
      ➕ Coluna de **tempo por suíte** (não estava no plano): `test_searchers.py` leva **~390s**
      porque bate no LexML bloqueado e no TCU em 500 com retries — insumo da frente 2.
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
- [ ] **F8** **aba de instruções e explicações na planilha de saída** — pedido do Rodrigo em
      2026-09-22, ao ver a v1.0 rodando. Hoje a planilha tem **uma aba só** (`Normativos`,
      `excel_export.py:304`). A aba nova explica as colunas, a procedência de cada resultado e
      **como a nota de relevância foi calculada**, inclusive qual parte é determinística.
- [ ] **F9** **aba de explicações e configurações no app** — mesmo pedido, mesma data. Hoje a
      régua de relevância existe **só dentro do prompt** em `llm/gemini_client.py` e não aparece
      em lugar nenhum da interface. Quem lê "30%" não tem como saber o que isso significa.
      ⚠ **Achado da leitura de código (2026-09-22), insumo desta feature:** a coluna `Relevancia`
      hoje **colapsa três procedências diferentes** no mesmo número, sem marcar qual é qual:
      (a) nota dada pelo Gemini; (b) `0.5` de fallback quando o lote do LLM falha ou volta
      malformado; (c) o default do searcher (`0.3` Google, `0.5` LexML/TCU) quando o LLM não roda.
      **`0.5` pode ser as três coisas.** Contra o princípio de rastreabilidade do projeto —
      precisa de campo de procedência da nota, não só da fonte.
      ⚠ **Segundo achado:** a heurística determinística `_keyword_relevance` é **inalcançável
      pelo app**. `score_relevance` só é chamada dentro de `if llm_available()` (`app.py:571`),
      então sem chave a nota **nunca é calculada** — fica no default do searcher. A heurística só
      roda se alguém chamar a função direto.

### 📥 Observações do Rodrigo sobre a planilha de saída (em coleta)

> Aberto em 2026-09-22: *"Eu tenho algumas observações para fazer na Excel de saída, mas já tá bem
> interessante por agora."* As demais observações ainda **não** foram ditas — este é o lugar delas.

- [x] aba de instruções e explicações → virou **F8**

## P3 — depois da Fase 1

- [ ] **Consertar LexML e TCU** — ⚠ **novo em 2026-09-22.** Medido: LexML atrás de WAF do Senado
      (3 URLs de fallback inúteis) e o endpoint de atos normativos do TCU em HTTP 500. Hoje **só a
      web aberta traz resultado** — confirmado pelo Rodrigo ("achou vários normativos por em todos
      da fonte Google"). Detalhe em `LESSONS.md` (2026-09-22).
      ⚠ E a UI precisa **distinguir fonte indisponível de fonte sem resultado** (hoje diz "0 erros").
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
