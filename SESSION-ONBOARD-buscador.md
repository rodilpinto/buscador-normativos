---
title: Buscador de Base Normativa — state snapshot
maintained_by: sessões do Claude Code; humanos podem editar
last_updated: 2026-09-09
related: [_TODO.md, _DECISOES-PENDENTES.md, log.md, docs/superpowers/specs/2026-09-08-buscador-normativos-design.md, docs/superpowers/plans/2026-09-08-buscador-normativos.md]
---

# Buscador de Base Normativa — onboarding de sessão

Ponto de entrada único. ≤ 1 página. Histórico em `log.md`; backlog em `_TODO.md`; decisões
abertas em `_DECISOES-PENDENTES.md`.

## 1. O que é (30s)

App web local que **constrói** o acervo de critério de uma ação de controle: recebe um tema,
expande em palavras-chave, busca em fontes catalogadas e na web aberta, e entrega uma lista
**triável em poucas decisões humanas**; só o que sobrevive à triagem é baixado e organizado.

Nasceu de um brainstorm na área `ai-com-ia` do repo `projetos-nuati` em 2026-09-08. **Repo
próprio**, pela regra do projeto: cada solução vive em `~/Documents/solucoes/<nome>/`.

⚠ **Não confundir com o `wiki-chat`** (em `projetos-nuati/wiki-chat/`). Aquele **consome** um
acervo pronto e conversa sobre ele; este **constrói** o acervo. Foram explicitamente
declarados projetos diferentes pelo Rodrigo em 08/09.

## 2. Estado na última pausa (2026-09-08/09)

### Feito e commitado
Cadeia desta área (repo só desta área, então aqui o tip **é** o último commit dela):
- `1c04c2d` — **commit inicial**: spec de design, plano de **16 tasks**, ledgers, log,
  comando de onboard, `CLAUDE.md` e `.gitignore`.
- `40d3242` — ajuste doc-only: registra que `git init` e `.gitignore` já estão feitos, e que
  o repo não tem remoto.
- → commit deste checkpoint. ⚠ **O SHA mais novo listado aqui está sempre um passo atrás do
  commit que gravou este arquivo** — a cadeia real termina em `git log --oneline -3`.

### Fase
🟡 **Planejamento concluído, ZERO linha de código escrita.** Nenhum módulo `buscador/`,
nenhum teste, nenhuma dependência instalada. ⚠ Da Task 1 do plano, **dois passos já estão
feitos**: o `git init` e o `.gitignore`. Falta `pyproject.toml`, `config.py` e o teste.

### Working tree
Limpo. ✅ **Remoto criado em 2026-09-09**: `github.com/rodilpinto/buscador-normativos`
(**privado**, confirmado via API), branch `master` rastreando `origin/master`.

## 3. Achados críticos (não perder)

1. **A dor real que este projeto resolve:** a primeira busca do levantamento LGPD trouxe
   **100+ normativos**, "inviável de usar por um humano", exigindo super-filtragem manual.
   O produto não é buscar, é **triar**. Todo desenho serve a reduzir o **número de decisões**.
2. **O artefato original não existe.** Varredura esgotada em 08/09: o "buscador" citado de
   memória nunca foi código. O que existe em
   `projetos-nuati/referencias/_apendices-e-scripts/` é só um **formatador** — uma lista de
   ~30 normativos escrita à mão dentro do `.py`, sem nenhuma chamada de rede. Isto aqui é
   greenfield de verdade.
3. **⚠ Os seletores CSS das Tasks 5-7 são suposição.** As fixtures fazem os testes passarem
   mesmo se o seletor estiver errado **para o site real**. Ao implementar: baixe a página
   real, confirme o seletor, e **substitua a fixture pela página real**.
4. **Duas travas anti-ancoragem são requisito, não detalhe** (spec §7): item `obrigatorio`
   nunca nasce desmarcado; nada vindo da web aberta nasce marcado. Têm teste próprio na
   Task 10 — não "simplificar".
5. **Windows, 260 caracteres:** acima disso o Python falha **em silêncio** (`isfile` devolve
   `False`). Pasta de tema ≤ 32 chars e helper `caminho_longo()` (Task 12).
6. **Rodar Python via Bash, não PowerShell** — caminho acentuado quebra no PowerShell 5.1.

## 4. Disciplina de trabalho

Um chunk = uma task do plano. Fechar cada chunk: rodar a suíte → atualizar duráveis →
commitar. Retomar sempre com `/onboard-buscador`.

## 5. Próximo movimento (recomendação, não decidido)

1. **Task 1 do plano** (fundação: `pyproject.toml`, `config.py`, teste) — ⚠ pular o `git init`.
2. Tasks 2-3 (banco, modelos/dedup) — destravam todo o resto.
3. Antes da Task 5, **decidir D-B1** (provedor da web aberta) não é necessário: a Task 7
   recebe a função por injeção. Mas antes de *rodar de verdade* contra a web, é.

Execução sugerida: subagente por task com revisão entre elas, ou inline em lotes com
checkpoint. O plano traz o handoff no fim.

## 6. Ponteiros

| Doc | Papel |
|---|---|
| `docs/superpowers/specs/2026-09-08-buscador-normativos-design.md` | **spec**: problema, princípio, decisões B1-B5, riscos |
| `docs/superpowers/plans/2026-09-08-buscador-normativos.md` | **plano**: 16 tasks com código e TDD |
| `_TODO.md` | ledger de tarefas |
| `_DECISOES-PENDENTES.md` | decisões abertas |
| `log.md` | timeline |

Acervo de origem (fora deste repo, só leitura):
`~/Documents/projetos-nuati/referencias/` — 141 arquivos em 12 categorias, e o formatador
antigo em `_apendices-e-scripts/`.

## 7. Como atualizar este arquivo

Ao mudar de estado: atualize §2/§5, bump `last_updated`, acrescente entrada no `log.md`,
atualize o ledger de decisões. Mantenha ≤ 1 página.
