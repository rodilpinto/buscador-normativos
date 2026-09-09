---
title: Buscador de Base Normativa — TODOs
last_audit: 2026-09-09
related: [_DECISOES-PENDENTES.md, log.md, SESSION-ONBOARD-buscador.md]
---

# TODOs — o que está pendente

> As 16 tasks de implementação vivem no **plano**, não aqui:
> `docs/superpowers/plans/2026-09-08-buscador-normativos.md`. Este ledger acompanha o
> **progresso** por task e o que não é task de código.

## P0 — próximo movimento

- [ ] **Task 1 · Fundação** (`pyproject.toml`, `config.py`, `tests/test_config.py`).
      ⚠ **Dois passos já estão feitos** pelo checkpoint de 09/09: o `git init` (Step 6) e o
      `.gitignore` (Step 1). Falta o `pyproject.toml`, o `config.py` e o teste.
- [ ] **Task 2 · Banco SQLite** (schema com as constraints de procedência e dedup)
- [ ] **Task 3 · Modelos e normalização** (`chave_dedup` — usada por todas as fontes)

## P1 — núcleo de busca

- [ ] **Task 4 · Protocolo `Fonte` + `FonteFake`**
- [ ] **Task 5 · Adaptador Planalto** — ⚠ substituir a fixture por página real antes de confiar
- [ ] **Task 6 · Adaptadores Legin e TCU** — mesma ressalva da fixture
- [ ] **Task 7 · Fonte de web aberta** (provedor por injeção; ver D-B1)
- [ ] **Task 8 · Palavras-chave** (regra + LLM opcional, tolerante a falha)
- [ ] **Task 9 · Índice do acervo e selo já-tenho** (mecanismo M1)
- [ ] **Task 10 · Pré-marcação** (M3 + M4, com as duas travas anti-ancoragem)
- [ ] **Task 11 · Orquestrador** (resiliente a fonte quebrada)

## P2 — saída e interface

- [ ] **Task 12 · Download** (dedup sha256, pasta por tema, trava de 260 chars)
- [ ] **Task 13 · Planilha-registro** (11 colunas do projeto + 6 de rastreabilidade)
- [ ] **Task 14 · Página de triagem** (M2: ações de grupo; mitigação de B5)
- [ ] **Task 15 · Fluxo web completo** (nova busca → triagem → aplicar)
- [ ] **Task 16 · CLI, fontes reais e README**

## P3 — depois do plano

- [ ] **Validar os seletores CSS contra os sites reais** e trocar as 4 fixtures sintéticas
      por páginas reais salvas. Enquanto isso não for feito, `buscar()` é **não verificado**.
- [ ] **Confirmar as rotas de busca** de Planalto (`/busca?q=`), Legin (`/legin/busca?termo=`)
      e TCU (`/busca?q=`) — todas são suposição do plano.
- [ ] **Rodar contra um tema real** e medir o critério de sucesso nº 2 da spec: 100+ resultados
      triáveis em menos de 15 decisões.
- [x] **2026-09-09 · Remoto criado**: `github.com/rodilpinto/buscador-normativos`, **privado**
      (confirmado via `gh repo view --json visibility`). Segue a convenção dos outros repos
      `rodilpinto/*`. ⚠ Exigiu instalar o **GitHub CLI** (`winget install --id GitHub.cli`),
      que não existia nesta máquina — criar repositório é chamada de **API**, não operação
      git, então o token do Credential Manager que faz o `push` funcionar não bastava.
- [ ] Registrar este repo no `MEMORY.md` do `projetos-nuati` como solução nova em `solucoes/`,
      junto às outras (fica no repo-pai, não aqui).

## Fora de escopo (registrado para não voltar à pauta)

Indexação semântica, chat sobre o acervo, extração de dispositivos e geração de checklist.
As duas últimas já existem (`/analise-normativa` + `checklist-conformidade`); as duas
primeiras são o `wiki-chat`.
