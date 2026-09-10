---
title: Buscador de Base Normativa — TODOs
last_audit: 2026-09-10
related: [_DECISOES-PENDENTES.md, log.md, SESSION-ONBOARD-buscador.md, spec/buscador/00-overview.md]
---

# TODOs — o que está pendente

> **Conteúdo** de cada task: o plano (`docs/superpowers/plans/2026-09-08-buscador-normativos.md`),
> com cópia verbatim por task em `spec/buscador/tasks/`.
> **Ordenamento** (ondas, trilhas, colisões): `spec/buscador/00-overview.md`.
> **Status**: aqui, e só aqui.

## Onda 1 — gate (sequencial, nada paralelo)

- [ ] **T1 · Fundação** → `spec/buscador/tasks/01-foundation.md`
      (`pyproject.toml`, `README.md`, `buscador/config.py`, `tests/test_config.py`)
      ⚠ **Dois Steps já estão feitos** pelo checkpoint de 09/09: o `git init` (Step 6) e o
      `.gitignore` (Step 1). Pular os dois.
      ⚠ Colisão conhecida: a T16 também lista `README.md` como "Create" e vai sobrescrever.
- [ ] **T3 · Modelos e normalização** → `tasks/03-models-normalize.md`
      (`Resultado`, `chave_dedup`; está no gate porque 3 das 4 trilhas da onda 2 consomem)

## Onda 2 — quatro trilhas em paralelo (interseção de arquivos vazia, verificada)

**Trilha A · dados**
- [ ] **T2 · Banco SQLite** → `tasks/02-sqlite-db.md`
- [ ] **T13 · Planilha-registro** → `tasks/13-registry-spreadsheet.md` (depende de T2)

**Trilha B · fontes**
- [ ] **T4 · Protocolo `Fonte` + catálogo** → `tasks/04-source-protocol.md`
- [ ] **T5 · Adaptador Planalto** → `tasks/05-planalto-adapter.md` ⚠ ver D-B2
- [ ] **T6 · Adaptadores Legin e TCU** → `tasks/06-legin-tcu-adapters.md` ⚠ ver D-B2
- [ ] **T7 · Fonte de web aberta** → `tasks/07-open-web-source.md` (provedor injetado; ver D-B1)
      T5, T6 e T7 são paralelas entre si depois da T4.

**Trilha C · llm**
- [ ] **T8 · Palavras-chave** → `tasks/08-keywords.md` (protocolo `LLM` + `NullLLM`, tolerante a falha)

**Trilha D · triagem-core**
- [ ] **T9 · Índice do acervo e selo já-tenho** → `tasks/09-archive-index.md` (M1)
- [ ] **T10 · Pré-marcação** → `tasks/10-premarking.md` (M3 + M4, **com as duas travas anti-ancoragem**)

## Onda 3 — núcleo (T11 e T12 em paralelo)

- [ ] **T11 · Orquestrador** → `tasks/11-search-orchestrator.md` (resiliente a fonte quebrada)
- [ ] **T12 · Download** → `tasks/12-download-organize.md` (dedup sha256, pasta por tema, 260 chars)

## Onda 4 — web (sequencial: T14 e T15 tocam o mesmo `app.py`)

- [ ] **T14 · Página de triagem** → `tasks/14-triage-page.md` (M2: ações de grupo; mitigação de B5)
- [ ] **T15 · Fluxo web completo** → `tasks/15-web-flow.md` (nova busca → triagem → aplicar)

## Onda 5 — fechamento

- [ ] **T16 · CLI, fontes reais e README** → `tasks/16-cli-sources-readme.md`

## P3 — depois do plano

- [ ] **Validar os seletores CSS contra os sites reais** e trocar as 4 fixtures sintéticas
      por páginas reais salvas. Enquanto isso não for feito, `buscar()` é **não verificado**.
- [ ] **Confirmar as rotas de busca** de Planalto (`/busca?q=`), Legin (`/legin/busca?termo=`)
      e TCU (`/busca?q=`) — todas são suposição do plano.
- [ ] **Rodar contra um tema real** e medir o critério de sucesso nº 2 da spec: 100+ resultados
      triáveis em menos de 15 decisões.
- [ ] **Resolver a ambiguidade do `README.md`** criado duas vezes (T1 e T16), registrada em
      `spec/buscador/00-overview.md`.
- [x] **2026-09-09 · Remoto criado**: `github.com/rodilpinto/buscador-normativos`, **privado**
      (confirmado via `gh repo view --json visibility`). Segue a convenção dos outros repos
      `rodilpinto/*`. ⚠ Exigiu instalar o **GitHub CLI** (`winget install --id GitHub.cli`),
      que não existia nesta máquina — criar repositório é chamada de **API**, não operação
      git, então o token do Credential Manager que faz o `push` funcionar não bastava.
- [x] **2026-09-10 · Split feito**: 16 tasks extraídas verbatim para `spec/buscador/tasks/`,
      agrupadas em 5 ondas e 7 trilhas, com checagem mecânica de colisão de arquivos.
- [ ] Registrar este repo no `MEMORY.md` do `projetos-nuati` como solução nova em `solucoes/`,
      junto às outras (fica no repo-pai, não aqui).

## Fora de escopo (registrado para não voltar à pauta)

Indexação semântica, chat sobre o acervo, extração de dispositivos e geração de checklist.
As duas últimas já existem (`/analise-normativa` + `checklist-conformidade`); as duas
primeiras são o `wiki-chat`.
